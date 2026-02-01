"""Race weekend flow and UI wrappers."""

import random

from gmr.constants import MONTHS, WEATHER_WET_CHANCE, PRIZE_RULES, DEFAULT_PRIZE_TOP3
from gmr.data import tracks
from gmr.core_time import get_season_week
from gmr.calendar import generate_calendar_for_year, get_clashes_for_year
from gmr.race_engine import run_ai_only_race, simulate_qualifying, run_race, roll_race_weather


def normalise_country(name: str) -> str:
    """
    Convert free-text country input into the same style your tracks use.
    Tracks currently use: UK, Italy, France, Belgium, Switzerland, USA.
    """
    if not name:
        return "UK"
    s = name.strip().lower()

    aliases = {
        "uk": "UK",
        "u.k.": "UK",
        "united kingdom": "UK",
        "great britain": "UK",
        "britain": "UK",
        "england": "UK",
        "scotland": "UK",
        "wales": "UK",

        "italy": "Italy",
        "italia": "Italy",

        "france": "France",

        "belgium": "Belgium",
        "belgie": "Belgium",
        "belgië": "Belgium",

        "switzerland": "Switzerland",
        "suisse": "Switzerland",
        "schweiz": "Switzerland",

        "usa": "USA",
        "us": "USA",
        "u.s.": "USA",
        "united states": "USA",
        "united states of america": "USA",
        "america": "USA",
    }

    return aliases.get(s, name.strip())


def calc_travel_cost(home_country: str, event_country: str, year: int) -> int:
    """
    Simple early-era logistics costs.
    - Domestic: same country (tow/van + fuel)
    - Near Europe: short hop within nearby European countries
    - Far Europe: longer haul (Italy, or intra-Americas travel)
    - Transatlantic: crossing the Atlantic (Americas <-> non-Americas)

    Warns if unknown countries are encountered (fallback to NEAR_EUROPE).
    """
    home = normalise_country(home_country)
    dest = normalise_country(event_country)

    # Baseline costs (tuned to your £ scale)
    DOMESTIC = 25
    NEAR_EUROPE = 70
    FAR_EUROPE = 110
    TRANSATLANTIC = 350

    # Slight inflation / sport growth later
    era_mult = 1.0
    if year >= 1950:
        era_mult = 1.10

    if home == dest:
        return int(DOMESTIC * era_mult)

    # USA, Brazil, Argentina trips are expensive (transatlantic) only when crossing the Atlantic
    # i.e., one location in Americas + one location outside Americas
    americas = {"USA", "Brazil", "Argentina"}
    home_in_americas = home in americas
    dest_in_americas = dest in americas

    # Both in Americas = intra-Americas (still expensive shipping but not transatlantic logic)
    # For now treat intra-Americas as FAR_EUROPE equivalent (long haul within continent)
    if home_in_americas and dest_in_americas:
        return int(FAR_EUROPE * era_mult)

    # Crossing the Atlantic (one in Americas, one outside)
    if home_in_americas or dest_in_americas:
        return int(TRANSATLANTIC * era_mult)

    # --- Europe split ---
    # “Near” is basically Channel-crossing / neighbouring countries.
    near_europe = {"UK", "France", "Belgium", "Switzerland"}
    far_europe = {"Italy"}

    # If either end is Italy, treat it as the longer-haul European trip
    if home in near_europe.union(far_europe) and dest in near_europe.union(far_europe):
        if home in far_europe or dest in far_europe:
            return int(FAR_EUROPE * era_mult)
        return int(NEAR_EUROPE * era_mult)

    # Fallback: if you add new countries later and forget to tag them,
    # treat as near-Europe rather than doing something wild.
    # But warn so developers know a country needs to be added to a region set.
    all_known = americas | near_europe | far_europe
    unknown = [c for c in (home, dest) if c not in all_known]
    if unknown:
        import warnings
        warnings.warn(
            f"calc_travel_cost: unknown country/countries {unknown!r} - "
            f"defaulting to NEAR_EUROPE cost. Add to americas/near_europe/far_europe set.",
            stacklevel=2
        )
    return int(NEAR_EUROPE * era_mult)


def charge_race_travel_if_needed(state, time, race_name, track_profile):
    """
    Deduct travel/logistics cost and log it to weekly finance buckets.
    """

    # ✅ Prevent double-charging travel if handle_race_week gets called twice
    if getattr(state, "travel_paid_week", None) == time.absolute_week:
        return 0
    state.travel_paid_week = time.absolute_week

    team_country = getattr(state, "country", "UK")
    event_country = track_profile.get("country", "UK")

    cost = calc_travel_cost(team_country, event_country, time.year)
    if cost <= 0:
        return 0

    state.money -= cost
    state.last_week_travel_cost += cost
    state.last_week_outgoings += cost

    team_name = state.player_constructor or "Your team"
    state.news.append(
        f"Travel & logistics: {team_name} spend £{cost} getting to {race_name} ({event_country})."
    )
    return cost


# NOTE: handle_contract_end_after_race was removed - contract handling is now
# centralized in careers.py via tick_driver_contract_after_race_end() which
# is called from race_engine.py after the race completes.


def describe_level(value, name):
    """
    Converts a numeric multiplier into a flavourful description.
    name hint helps us choose wording style.
    """
    if value >= 1.15:
        if name == "engine":
            return "Severe – engines are likely to overheat or fail"
        if name == "crash":
            return "Deadly – mistakes punished hard"
        return "Extreme"
    elif value >= 1.08:
        if name == "engine":
            return "Very High – sustained stress on engines"
        if name == "crash":
            return "High – treacherous corners and poor runoff"
        return "Strong"
    elif value >= 1.02:
        if name == "engine":
            return "Above Average engine strain"
        if name == "crash":
            return "Above Average crash risk"
        return "Moderate bias"
    elif value <= 0.90:
        if name == "engine":
            return "Gentle – forgiving on motors"
        if name == "crash":
            return "Safe – fewer dangerous sections"
        return "Favourable"
    else:
        if name == "engine":
            return "Normal"
        if name == "crash":
            return "Normal"
        return "Balanced"


def describe_style(pace_w, cons_w):
    """
    Explain how the track rewards pace vs consistency.
    """
    if pace_w > cons_w * 1.15:
        return "Flat-out speed decides the order here"
    if cons_w > pace_w * 1.15:
        return "Smooth, repeatable laps matter more than raw pace"
    if pace_w > cons_w:
        return "Slight reward for brave, fast drivers"
    if cons_w > pace_w:
        return "A tidy, controlled approach pays off"
    return "Well-balanced test of speed and discipline"


def show_race_preview(state, time, race_name, track_profile):
    """
    Display race costs and potential earnings BEFORE the enter/skip decision.
    Helps player make informed choice about racing this weekend.
    """
    print("\n=== Race Weekend Preview ===")
    print(f"{race_name}")
    print("----------------------------")
    
    country = track_profile.get("country", "Unknown")
    team_country = getattr(state, "country", "UK")
    
    # --- COSTS ---
    print("\n[ ESTIMATED COSTS ]")
    
    # Travel cost
    travel_cost = calc_travel_cost(team_country, country, time.year)
    if country == team_country:
        print(f"  Travel (home event):    £{travel_cost}")
    else:
        print(f"  Travel to {country}:       £{travel_cost}")
    
    # Driver pay (if you have a driver)
    driver_pay = 0
    if state.player_driver and state.driver_pay > 0:
        driver_pay = state.driver_pay
        print(f"  Driver pay:             £{driver_pay}")
    
    # Special transport costs (nationality restrictions, transatlantic)
    extra_costs = 0
    allowed_nats = track_profile.get("allowed_nationalities")
    if allowed_nats and state.player_driver:
        player_nat = state.player_driver.get("country", "UK")
        if player_nat not in allowed_nats:
            extra_costs = 200
            print(f"  Int'l transport fee:    £{extra_costs} (driver is {player_nat})")
    
    if race_name == "Union Speedway" and state.player_driver:
        player_nat = state.player_driver.get("country", "UK")
        if player_nat != "USA":
            extra_costs = 500
            print(f"  Transatlantic shipping: £{extra_costs}")
    
    total_cost = travel_cost + driver_pay + extra_costs
    print(f"  --------------------------")
    print(f"  TOTAL COST:             £{total_cost}")
    
    # --- POTENTIAL EARNINGS ---
    print("\n[ POTENTIAL EARNINGS ]")
    
    # Prize money
    rule = PRIZE_RULES.get(race_name)
    if rule:
        top3 = rule.get("top3", DEFAULT_PRIZE_TOP3)
        finisher_bonus = rule.get("finisher_bonus", 0)
    else:
        top3 = DEFAULT_PRIZE_TOP3
        finisher_bonus = 0
    
    print(f"  1st place:              £{top3[0]}")
    print(f"  2nd place:              £{top3[1]}")
    print(f"  3rd place:              £{top3[2]}")
    if finisher_bonus > 0:
        print(f"  Finisher bonus (4th+):  £{finisher_bonus}")
    
    # Sponsor bonuses if applicable
    if hasattr(state, 'sponsor_name') and state.sponsor_name:
        print(f"\n  Sponsor: {state.sponsor_name}")
        if hasattr(state, 'sponsor_bonus_per_race') and state.sponsor_bonus_per_race > 0:
            print(f"  Race start bonus:       £{state.sponsor_bonus_per_race}")
    
    # --- FINANCIAL CONTEXT ---
    print("\n[ YOUR FINANCES ]")
    print(f"  Current funds:          £{state.money}")
    print(f"  Tyre sets available:    {getattr(state, 'tyre_sets', 0)}")
    
    # Warning if low on cash
    if state.money < total_cost:
        print(f"\n  ⚠ WARNING: You may not have enough to cover all costs!")
    elif state.money < total_cost * 2:
        print(f"\n  ⚠ Tight budget - a DNF could hurt your finances.")
    
    # --- TRACK QUICK INFO ---
    print("\n[ TRACK INFO ]")
    engine_danger = track_profile.get("engine_danger", 1.0)
    crash_danger = track_profile.get("crash_danger", 1.0)
    print(f"  Engine strain:          {describe_level(engine_danger, 'engine')}")
    print(f"  Crash danger:           {describe_level(crash_danger, 'crash')}")
    
    # Weather tendency
    wet_chance = track_profile.get("wet_chance", WEATHER_WET_CHANCE)
    if wet_chance >= WEATHER_WET_CHANCE + 0.1:
        print(f"  Weather:                Rain likely")
    elif wet_chance <= WEATHER_WET_CHANCE - 0.1:
        print(f"  Weather:                Usually dry")
    else:
        print(f"  Weather:                Changeable")
    
    print("")  # blank line before decision


def show_race_briefing(state, time, race_name):
    track_profile = tracks.get(
        race_name,
        {
            "engine_danger": 1.0,
            "crash_danger": 1.0,
            "pace_weight": 1.0,
            "consistency_weight": 1.0,
        },
    )

    country = track_profile.get("country", "Unknown")

    print("\n=== Race Weekend Briefing ===")
    print(f"{race_name} ({country})")
    print(f"Week {time.week}, {MONTHS[time.month]} {time.year}")
    print("-----------------------------")
    
    # Track grade and ratings
    from gmr.track_evolution import get_track_grade, get_track_rating
    grade = get_track_grade(race_name, time.year)
    safety = get_track_rating(race_name, "safety")
    facilities = get_track_rating(race_name, "facilities")
    prestige = get_track_rating(race_name, "prestige")
    
    grade_desc = {
        "A": "World Championship",
        "B": "International",
        "C": "Regional",
        "D": "Club"
    }.get(grade, "Unknown")
    
    print(f"FIA Grade: {grade} ({grade_desc})")
    print(f"Safety: {'★' * safety}{'☆' * (10 - safety)} ({safety}/10)")
    print(f"Facilities: {'★' * facilities}{'☆' * (10 - facilities)} ({facilities}/10)")
    print(f"Prestige: {'★' * prestige}{'☆' * (10 - prestige)} ({prestige}/10)")
    print()

    # --- Home/Away flavour (optional, safe) ---
    team_country = getattr(state, "country", None)
    if team_country and country != "Unknown":
        if country == team_country:
            print("Home event: local press and familiar faces in the paddock.")
        else:
            print("Away event: travel costs up, local teams know the place well.")

    engine_danger = track_profile.get("engine_danger", 1.0)
    crash_danger = track_profile.get("crash_danger", 1.0)
    pace_w = track_profile.get("pace_weight", 1.0)
    cons_w = track_profile.get("consistency_weight", 1.0)
    wet_chance = track_profile.get("wet_chance", WEATHER_WET_CHANCE)
    hot_chance = track_profile.get("base_hot_chance", 0.2)
    length_km = track_profile.get("length_km")
    race_distance_km = track_profile.get("race_distance_km")

    print("Track Identity:")
    print(f"  Engine strain: {describe_level(engine_danger, 'engine')}")
    print(f"  Crash danger:  {describe_level(crash_danger, 'crash')}")
    print(f"  Style:         {describe_style(pace_w, cons_w)}")

    # Add flavor text if available
    if "flavor" in track_profile:
        print(f"\n{track_profile['flavor']}")

    # Climate flavour
    climate_line = None
    if wet_chance >= WEATHER_WET_CHANCE + 0.1:
        climate_line = "Weather tendency: Showers are common at this venue."
    elif hot_chance >= 0.4:
        climate_line = "Weather tendency: This venue is notorious for summer heatwaves."
    elif wet_chance <= WEATHER_WET_CHANCE - 0.1:
        climate_line = "Weather tendency: Rain is relatively rare here."

    if climate_line:
        print(f"  {climate_line}")

    # Length / distance / laps info
    if length_km and race_distance_km:
        laps = max(1, round(race_distance_km / length_km))
        print(f"\nCircuit Layout:")
        print(f"  Lap length ........... {length_km:.1f} km")
        print(f"  Race distance ........ {race_distance_km:.0f} km (~{laps} laps)")

    # Car / Driver summary
    print("\nDriver/Car summary:")
    if state.player_driver:
        d = state.player_driver
        print(f"  Driver: {d['name']} (Pace {d['pace']}, Consistency {d['consistency']})")
        cxp = float(d.get("car_xp", 0.0))
        print(f"  Car comfort: {cxp:.1f}/10")
    else:
        print("  No driver hired yet.")

    print(f"  Car speed number: {state.car_speed}, reliability: {state.car_reliability}")


def choose_race_strategy(state):
    """
    Let the player choose how hard to run the car for this race.
    This is the ONE source of truth:
      - sets risk_mode (used in performance + DNF logic)
      - sets risk_multiplier (used in wear logic)
    """
    print("\nRace pace for this event:")
    print("1. Attack (faster, more wear, more DNFs)")
    print("2. Neutral")
    print("3. Nurse (slower, less wear, fewer DNFs)")

    while True:
        choice = input("> ").strip()

        if choice == "1":
            state.risk_mode = "attack"
            state.risk_multiplier = 1.4
            state.race_strategy = "attack"   # keep if anything else reads it later
            print("You order an all-out attack. Lap time over mechanical sympathy.")
            return

        if choice in ("", "2"):
            state.risk_mode = "neutral"
            state.risk_multiplier = 1.0
            state.race_strategy = "neutral"
            print("You choose a balanced run.")
            return

        if choice == "3":
            state.risk_mode = "nurse"
            state.risk_multiplier = 0.7
            state.race_strategy = "nurse"
            print("You instruct the team to nurse the car and minimise risk.")
            return

        print("Please choose 1 (Attack), 2 (Neutral), or 3 (Nurse).")


def handle_race_clash_choice(state, time, season_week, clash_races):
    """
    When multiple races occur on the same week, let the player choose which to enter.
    Returns (chosen_race_name, skipped_race_name) or (None, None) if skipping both.
    """
    print("\n" + "=" * 60)
    print("⚔️  RACE CLASH - SCHEDULING CONFLICT  ⚔️")
    print("=" * 60)
    print("\nTwo races are scheduled for the same week!")
    print("Your team can only attend ONE event. Choose wisely.\n")

    for i, race_name in enumerate(clash_races, 1):
        track = tracks.get(race_name, {})
        country = track.get("country", "Unknown")
        fame_mult = track.get("fame_mult", 1.0)
        
        # Determine prestige tier
        if fame_mult >= 1.2:
            tier = "⭐⭐⭐ MAJOR"
        elif fame_mult >= 0.9:
            tier = "⭐⭐ Standard"
        else:
            tier = "⭐ Club"
        
        print(f"  {i}. {race_name}")
        print(f"     Location: {country}")
        print(f"     Prestige: {tier} (×{fame_mult:.2f} fame)")
        
        # Check nationality restrictions
        allowed_nats = track.get("allowed_nationalities")
        if allowed_nats:
            print(f"     ⚠️  Restricted to: {', '.join(allowed_nats)} drivers")
        print()

    print("  3. Skip both races this week")
    print()

    while True:
        choice = input("Which race do you want to enter? > ").strip()
        if choice == "1":
            chosen = clash_races[0]
            skipped = clash_races[1]
            print(f"\nYou've chosen to enter {chosen}.")
            print(f"The {skipped} will run without your team.")
            input("\nPress Enter to continue...")
            return chosen, skipped
        elif choice == "2":
            chosen = clash_races[1]
            skipped = clash_races[0]
            print(f"\nYou've chosen to enter {chosen}.")
            print(f"The {skipped} will run without your team.")
            input("\nPress Enter to continue...")
            return chosen, skipped
        elif choice == "3":
            print("\nYou've decided to skip both races this week.")
            print("Your team will rest while both events run without you.")
            input("\nPress Enter to continue...")
            return None, clash_races  # Return None and list of races to run AI-only
        else:
            print("Please enter 1, 2, or 3.")


def handle_race_week(state, time):
    """
    Race weekend flow:

    - If you have no car or no driver, you automatically skip the race
      and an AI-only event is run.
    - If you DO have a car+driver, you can CHOOSE:
        1) Enter the race weekend
        2) Skip the event and watch from the paddock

    If you enter:
    - Show briefing
    - Roll race-day weather
    - Run qualifying (once)
    - Between-sessions menu
    - Run race
    """
    state.news.append(f"DEBUG: handle_race_week fired. player_driver={state.player_driver is not None}")

    season_week = get_season_week(time)
    race_calendar = generate_calendar_for_year(time.year)
    
    # Check for race clashes first
    clashes = get_clashes_for_year(time.year)
    skipped_race = None
    
    if season_week in clashes:
        clash_races = clashes[season_week]
        chosen, skipped = handle_race_clash_choice(state, time, season_week, clash_races)
        
        if chosen is None:
            # Player chose to skip both races - run them AI-only
            # But drivers can only be at one race, so split the grid
            first_race = skipped[0]
            second_race = skipped[1]
            first_track = tracks.get(first_race, {})
            second_track = tracks.get(second_race, {})
            
            # Run first race and get drivers who participated
            drivers_at_first = run_ai_only_race(state, first_race, time, season_week, first_track)
            
            # Run second race excluding drivers from first race
            run_ai_only_race(state, second_race, time, season_week, second_track, 
                           excluded_drivers=drivers_at_first or set())
            
            state.completed_races.add(season_week)
            return
        else:
            race_name = chosen
            skipped_race = skipped
    else:
        race_name = race_calendar.get(season_week)
    
    if race_name is None:
        return

    # ✅ HARD GUARD: never run the same race twice
    if not hasattr(state, "completed_races") or state.completed_races is None:
        state.completed_races = set()

    if season_week in state.completed_races:
        state.news.append(f"DEBUG: {race_name} already completed for season_week={season_week}. Skipping.")
        return

    # Vallone is a season milestone even if you skip it
    if race_name == "Vallone GP":
        state.ever_completed_vallone = True


    from gmr.careers import warn_if_contract_last_race
    warn_if_contract_last_race(state)


    track_profile = tracks.get(race_name, {})

    # ------------------------------
    # Can we actually race this week?
    # ------------------------------
    no_car = (
        state.current_engine is None
        or state.current_chassis is None
        or not state.player_driver
    )

    no_tyres = getattr(state, "tyre_sets", 0) <= 0
    
    # Check if driver is injured
    driver_injured = getattr(state, 'player_driver_injured', False) and getattr(state, 'player_driver_injury_weeks_remaining', 0) > 0

    if no_car or driver_injured or no_tyres:
        # You physically can't run the event: auto-skip, AI-only race
        print(f"\n{race_name} takes place, but your team cannot compete this week.")
        if state.current_engine is None:
            print("  • No engine installed.")
        if state.current_chassis is None:
            print("  • No chassis installed.")
        if not state.player_driver:
            print("  • No driver contracted.")
        if driver_injured:
            weeks_remaining = getattr(state, 'player_driver_injury_weeks_remaining', 0)
            print(f"  • Driver injured ({weeks_remaining} week{'s' if weeks_remaining != 1 else ''} remaining).")
        if no_tyres:
            print("  • No tyre sets available.")

        print("You watch from the paddock as other teams take part.")
        input("\nPress Enter to continue...")

        drivers_in_main_race = run_ai_only_race(state, race_name, time, season_week, track_profile)
        
        # If there was a clash, run the other race as AI-only too
        # Drivers in the main race can't also be at the skipped race
        if skipped_race:
            print(f"\nMeanwhile, at {skipped_race}...")
            skipped_track = tracks.get(skipped_race, {})
            run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                           excluded_drivers=drivers_in_main_race or set())

        state.completed_races.add(season_week)  # Mark as done to prevent loop

        from gmr.sponsorship import maybe_offer_sponsor, maybe_offer_tyre_sponsorship
        maybe_offer_sponsor(state, time)
        maybe_offer_tyre_sponsorship(state, time)

        return


    # --------------------------------------------
    # You DO have a car and a driver: give a choice
    # --------------------------------------------
    # Show preview BEFORE the decision so player has all the info
    show_race_preview(state, time, race_name, track_profile)
    
    print(f"{race_name} is scheduled for this week.")
    print("1. Enter the race weekend")
    print("2. Skip this race and watch from the paddock")

    while True:
        choice = input("> ").strip()
        if choice in ("1", ""):
            # Check if driver is injured before proceeding
            if getattr(state, 'player_driver_injured', False) and getattr(state, 'player_driver_injury_weeks_remaining', 0) > 0:
                weeks_remaining = getattr(state, 'player_driver_injury_weeks_remaining', 0)
                print(f"\nYour driver {state.player_driver['name']} is still injured and cannot race.")
                print(f"They will be unable to drive for another {weeks_remaining} week{'s' if weeks_remaining != 1 else ''}.")
                print("You cannot enter this race.")
                input("\nPress Enter to continue...")
                drivers_in_main_race = run_ai_only_race(state, race_name, time, season_week, track_profile)
                if skipped_race:
                    skipped_track = tracks.get(skipped_race, {})
                    run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                                   excluded_drivers=drivers_in_main_race or set())
                state.completed_races.add(season_week)  # Mark as done to prevent loop
                return

            if getattr(state, "tyre_sets", 0) <= 0:
                print("\nYou have no tyre sets available and cannot start the race.")
                input("\nPress Enter to continue...")
                drivers_in_main_race = run_ai_only_race(state, race_name, time, season_week, track_profile)
                if skipped_race:
                    skipped_track = tracks.get(skipped_race, {})
                    run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                                   excluded_drivers=drivers_in_main_race or set())
                state.completed_races.add(season_week)  # Mark as done to prevent loop
                return
            
            # ✅ ONLY charge travel if you actually enter the event
            charge_race_travel_if_needed(state, time, race_name, track_profile)

            # Check nationality restrictions for player driver
            allowed_nats = track_profile.get("allowed_nationalities")
            if allowed_nats and state.player_driver:
                player_nat = state.player_driver.get("country", "UK")
                if player_nat not in allowed_nats:
                    print(f"\n{race_name} restricts entries to {', '.join(allowed_nats)} drivers only.")
                    print(f"Your driver {state.player_driver['name']} is from {player_nat}.")
                    transport_cost = 200  # fixed cost to transport internationally
                    print(f"You can pay £{transport_cost} to transport your driver and car internationally.")
                    print("1. Pay and enter")
                    print("2. Skip this race")
                    while True:
                        sub_choice = input("> ").strip()
                        if sub_choice in ("1", ""):
                            if state.money >= transport_cost:
                                state.money -= transport_cost
                                state.last_week_outgoings += transport_cost
                                state.last_week_travel_cost += transport_cost
                                if not hasattr(state, 'transport_paid_races'):
                                    state.transport_paid_races = set()
                                state.transport_paid_races.add(race_name)
                                state.news.append(f"Paid £{transport_cost} for international transport to {race_name}.")
                                print(f"Paid £{transport_cost}. Proceeding to the race.")
                            else:
                                print("You don't have enough money. Skipping the race.")
                                drivers_in_main_race = run_ai_only_race(state, race_name, time, season_week, track_profile)
                                if skipped_race:
                                    print(f"\nMeanwhile, at {skipped_race}...")
                                    skipped_track = tracks.get(skipped_race, {})
                                    run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                                                   excluded_drivers=drivers_in_main_race or set())
                                state.completed_races.add(season_week)  # Mark as done to prevent loop
                                return
                            break
                        elif sub_choice == "2":
                            print("Skipping the race.")
                            drivers_in_main_race = run_ai_only_race(state, race_name, time, season_week, track_profile)
                            if skipped_race:
                                print(f"\nMeanwhile, at {skipped_race}...")
                                skipped_track = tracks.get(skipped_race, {})
                                run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                                               excluded_drivers=drivers_in_main_race or set())
                            state.completed_races.add(season_week)  # Mark as done to prevent loop
                            return
                        else:
                            print("Please choose 1 or 2.")

            # Special transatlantic transport for Union Speedway
            if race_name == "Union Speedway" and state.player_driver:
                player_nat = state.player_driver.get("country", "UK")
                if player_nat != "USA":
                    print(f"\n{race_name} is across the Atlantic Ocean.")
                    print(f"Your driver {state.player_driver['name']} is from {player_nat}.")
                    transatlantic_cost = 500  # higher cost for long distance
                    print(f"You can pay £{transatlantic_cost} to transport your driver and car across the Atlantic.")
                    print("1. Pay and enter")
                    print("2. Skip this race")
                    while True:
                        sub_choice = input("> ").strip()
                        if sub_choice in ("1", ""):
                            if state.money >= transatlantic_cost:
                                state.money -= transatlantic_cost
                                state.last_week_outgoings += transatlantic_cost
                                state.last_week_travel_cost += transatlantic_cost
                                if not hasattr(state, 'transport_paid_races'):
                                    state.transport_paid_races = set()
                                state.transport_paid_races.add(race_name)
                                state.news.append(f"Paid £{transatlantic_cost} for transatlantic transport to {race_name}.")
                                print(f"Paid £{transatlantic_cost}. Proceeding to the race.")
                            else:
                                print("You don't have enough money. Skipping the race.")
                                drivers_in_main_race = run_ai_only_race(state, race_name, time, season_week, track_profile)
                                if skipped_race:
                                    print(f"\nMeanwhile, at {skipped_race}...")
                                    skipped_track = tracks.get(skipped_race, {})
                                    run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                                                   excluded_drivers=drivers_in_main_race or set())
                                state.completed_races.add(season_week)  # Mark as done to prevent loop
                                return
                            break
                        elif sub_choice == "2":
                            print("Skipping the race.")
                            drivers_in_main_race = run_ai_only_race(state, race_name, time, season_week, track_profile)
                            if skipped_race:
                                print(f"\nMeanwhile, at {skipped_race}...")
                                skipped_track = tracks.get(skipped_race, {})
                                run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                                               excluded_drivers=drivers_in_main_race or set())
                            state.completed_races.add(season_week)  # Mark as done to prevent loop
                            return
                        else:
                            print("Please choose 1 or 2.")

            break

        elif choice == "2":
            print(f"\nYou decide not to enter {race_name} this year.")
            print("You watch from the paddock as other teams take part.")
            input("\nPress Enter to continue...")

            # ❌ NO TRAVEL CHARGE when skipping
            drivers_in_main_race = run_ai_only_race(state, race_name, time, season_week, track_profile)
            
            # If there was a clash, run the other race as AI-only too
            # Drivers in the main race can't also be at the skipped race
            if skipped_race:
                print(f"\nMeanwhile, at {skipped_race}...")
                skipped_track = tracks.get(skipped_race, {})
                run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                               excluded_drivers=drivers_in_main_race or set())
            
            state.completed_races.add(season_week)  # Mark as done to prevent loop
            return
        else:
            print("Please choose 1 to race or 2 to skip.")

    # ------------------------------
    # From here on: full race weekend
    # ------------------------------

    # Deliver tyre sponsor tyres before the race
    from gmr.sponsorship import deliver_tyre_sponsor_tyres
    deliver_tyre_sponsor_tyres(state, time, race_name)

    # Decide race-day weather up front
    is_wet, is_hot = roll_race_weather(track_profile)

    # Pre-weekend briefing
    show_race_briefing(state, time, race_name)

    # Simple forecast so your strategy isn't blind
    print("\nRace-day forecast:")
    if is_wet:
        print("  Expect a wet race – grip will be low, mistakes and crashes more likely.")
    elif is_hot:
        print("  Hot, dry conditions – engines will run hotter and be more prone to failure.")
    else:
        print("  Likely dry and temperate – no major weather extremes expected.")

    input("\nPress Enter to begin qualifying...")

    # Run qualifying ONCE for this weekend
    qual_results, grid_bonus, is_wet_quali = simulate_qualifying(
        state, race_name, time, track_profile
    )

    # Dump current news immediately so quali headlines appear now
    if state.news:
        print("\n--- Qualifying News ---")
        for item in state.news:
            print(item)
        print("-----------------------")
        state.news.clear()

    # Between-sessions menu – you're locked into the weekend now
    while True:
        print("\nBetween Sessions:")
        print("1. Garage (post-qualifying adjustments – not implemented yet)")
        print("2. Start the race")

        choice = input("> ").strip()

        if choice == "1":
            # Future hook: this will be the 'race-day garage' screen.
            print("\nPost-qualifying garage options are not implemented yet.")
            print("You'll be able to tweak setup here in a later version.")
        elif choice in ("", "2"):
            choose_race_strategy(state)
            run_race(state, race_name, time, season_week, grid_bonus, is_wet, is_hot)

            input("\nPress Enter to see the race weekend summary...")

            # Dump race news NOW so it feels like the race happened before any contract talk
            if state.news:
                print("\n--- Race Weekend News ---")
                for item in state.news:
                    print(item)
                print("-------------------------")
                state.news.clear()

            # If there was a clash, run the skipped race as AI-only
            # Exclude drivers who raced in the player's race (stored during qualifying)
            if skipped_race:
                print(f"\nMeanwhile, at {skipped_race}...")
                skipped_track = tracks.get(skipped_race, {})
                drivers_in_main_race = getattr(state, 'last_race_drivers', set())
                run_ai_only_race(state, skipped_race, time, season_week, skipped_track,
                               excluded_drivers=drivers_in_main_race)
                if state.news:
                    print("\n--- Results from the other race ---")
                    for item in state.news:
                        print(item)
                    print("-----------------------------------")
                    state.news.clear()

            from gmr.sponsorship import maybe_offer_sponsor, maybe_offer_tyre_sponsorship
            maybe_offer_sponsor(state, time)
            maybe_offer_tyre_sponsorship(state, time)
            
            return  # ✅ leave race week after the race runs (prevents infinite loop)
          
        else:
            print("Invalid choice. Please select 1 or 2.")