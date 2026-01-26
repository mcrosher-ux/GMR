# gmr/race_day.py
import random

from gmr.constants import (
    CHAMPIONSHIP_ACTIVE, CONSTRUCTOR_SHARE, POINTS_TABLE, MONTHS,
    WEATHER_WET_CHANCE, get_reliability_mult, get_crash_mult,
    TEST_DRIVERS_ENABLED, get_prize_for_race_and_pos,
    ERA_RELIABILITY_MULTIPLIER, ERA_CRASH_MULTIPLIER
)
from gmr.data import drivers, tracks, constructors, engines, chassis_list
from gmr.world_logic import driver_enters_event, get_car_speed_for_track, calculate_car_speed
from gmr.core_time import GameTime, get_season_week
from gmr.calendar import generate_calendar_for_year
from gmr.careers import (
    update_fame_after_race, update_driver_progress, grant_participation_xp_for_dnfs,
    tick_driver_contract_after_race_end
)
from gmr.story import maybe_trigger_demo_finale  


def clamp(v, lo, hi):
    return max(lo, min(hi, v))

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
    - Domestic: tow/van + fuel
    - Near Europe: short hop (France/Belgium etc.)
    - Far Europe: longer haul (Italy etc.)
    - USA: ship + major logistics
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

    # USA trip is expensive for non-USA teams and vice versa
    if home == "USA" or dest == "USA":
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





def record_race_result(state, time, season_week, race_name, is_wet, is_hot, finishers, retired):
    """
    Save one race to state.race_history and update state.driver_career totals.

    finishers: list of (driver_dict, performance)
    retired: list of (driver_dict, reason) where reason is "engine" or "crash" (or "unknown")
    """

    # Safety for old saves
    if not hasattr(state, "race_history") or state.race_history is None:
        state.race_history = []
    if not hasattr(state, "driver_career") or state.driver_career is None:
        state.driver_career = {}

    entry = {
        "year": time.year,
        "week": season_week,
        "race": race_name,
        "wet": bool(is_wet),
        "hot": bool(is_hot),
        "finishers": [],
        "dnfs": [],
    }

    # ---- finishers ----
    for pos, (d, _perf) in enumerate(finishers, start=1):
        pts = 0
        if CHAMPIONSHIP_ACTIVE and (pos - 1) < len(POINTS_TABLE):
            pts = POINTS_TABLE[pos - 1]

        prize = get_prize_for_race_and_pos(race_name, pos - 1)


        entry["finishers"].append({
            "pos": pos,
            "name": d.get("name"),
            "constructor": d.get("constructor"),
            "pts": pts,
            "prize": prize,
        })

        name = d.get("name")
        c = state.driver_career.get(name, {
            "starts": 0,
            "wins": 0,
            "podiums": 0,
            "dnfs": 0,
            "engine_dnfs": 0,
            "crash_dnfs": 0,
            "points": 0,
            "prize_money": 0,
            "best_finish": None,
        })

        c["starts"] += 1
        c["points"] += pts
        c["prize_money"] += prize
        if pos == 1:
            c["wins"] += 1
        if pos <= 3:
            c["podiums"] += 1
        if c["best_finish"] is None or pos < c["best_finish"]:
            c["best_finish"] = pos

        state.driver_career[name] = c

    # ---- DNFs ----
    for (d, reason) in retired:
        entry["dnfs"].append({
            "name": d.get("name"),
            "constructor": d.get("constructor"),
            "reason": reason,
        })

        name = d.get("name")
        c = state.driver_career.get(name, {
            "starts": 0,
            "wins": 0,
            "podiums": 0,
            "dnfs": 0,
            "engine_dnfs": 0,
            "crash_dnfs": 0,
            "points": 0,
            "prize_money": 0,
            "best_finish": None,
        })

        c["starts"] += 1
        c["dnfs"] += 1
        if reason == "engine":
            c["engine_dnfs"] += 1
        elif reason == "crash":
            c["crash_dnfs"] += 1

        state.driver_career[name] = c

    state.race_history.append(entry)




def pay_appearance_money(state, race_name):
    t = tracks.get(race_name, {})
    base = int(t.get("appearance_base", 0))
    mult = float(t.get("appearance_prestige_mult", 0.0))

    if base <= 0 and mult <= 0:
        return 0

    payout = int(base + state.prestige * mult)
    payout = max(0, payout)

    # Cap appearance money based on track prestige
    if race_name in ["Bradley Fields", "Little Autodromo"]:
        payout = min(payout, 50)
    elif race_name in ["Ardennes Endurance GP", "Union Speedway"]:
        payout = min(payout, 150)
    else:
        payout = min(payout, 100)

    # Track appearance money separately from prize money
    if not hasattr(state, "last_week_appearance_income"):
        state.last_week_appearance_income = 0

    state.money += payout
    state.last_week_income += payout
    state.last_week_appearance_income += payout


    team_name = state.player_constructor or "Your team"
    state.news.append(
        f"Appearance money: {team_name} receive £{payout} from {race_name}'s organisers for taking the start."
    )
    return payout



def get_suspension_value_for_driver(state, d):
    """
    Returns suspension score (1–10) for this driver's current car.
    Player uses current_chassis. AI uses constructor chassis if available.
    """
    if d == state.player_driver and state.current_chassis:
        return int(state.current_chassis.get("suspension", 5))

    # AI: try to read from their works chassis
    c = constructors.get(d.get("constructor", ""), {})
    ch_id = c.get("chassis_id")
    if ch_id:
        ch = next((x for x in chassis_list if x.get("id") == ch_id), None)
        if ch:
            return int(ch.get("suspension", 5))

    return 5

def suspension_track_factor(track_profile):
    return float(track_profile.get("suspension_importance", 1.0))


def get_ai_car_stats(constructor_name):
    c = constructors.get(constructor_name, {})

    # Parts-based path FIRST (only if ids are defined)
    eng_id = c.get("engine_id")
    ch_id = c.get("chassis_id")
    if eng_id and ch_id:
        eng = next((e for e in engines if e["id"] == eng_id), None)
        ch = next((x for x in chassis_list if x["id"] == ch_id), None)
        if eng and ch:
            speed = calculate_car_speed(eng, ch)
            reliability = eng.get("reliability", 5)
            return speed, reliability

    # Legacy fallback (Independents stay here)
    if "speed" in c and "reliability" in c:
        return c["speed"], c["reliability"]

    return 5, 5

def build_event_grid(state, time, race_name, track_profile):
    """
    Returns a list of drivers who will take part in THIS event,
    respecting per-team car limits.

    IMPORTANT:
    - "Independent" is NOT a real team; it's the open-entry pool.
      So it should NOT be capped to 2 cars.
    """

    # Optional: let tracks define grid size (fallback to something sane)
    grid_size = track_profile.get("grid_size", 12)

    # How many cars each WORKS team can enter this year
    def team_car_limit(team_name: str) -> int:
        if team_name == "Enzoni":
            return 3 if time.year >= 1950 else 2
        if team_name == "Scuderia Valdieri":
            return 2
        if state.player_constructor and team_name == state.player_constructor:
            return 1
        return 999  # any future "real" team won't be accidentally capped

    # Collect eligible drivers by "team"/pool
    by_team = {}
    for d in drivers:
        if not driver_enters_event(d, race_name, track_profile, state):
            continue

        # Block Test drivers if debug toggle is off
        if not TEST_DRIVERS_ENABLED and d.get("constructor") == "Test":
            continue

        # Player team: only the contracted player driver is allowed to represent it
        if state.player_constructor and d.get("constructor") == state.player_constructor:
            if d is not state.player_driver:
                continue

        team = d.get("constructor", "Independent")
        by_team.setdefault(team, []).append(d)

    final_grid = []

    # 1) Add works teams and player (capped)
    for team in ("Enzoni", "Scuderia Valdieri"):
        if team in by_team:
            team_drivers = by_team[team]

            # best drivers get the seats
            team_drivers.sort(
                key=lambda x: (x.get("pace", 0) * 1.0 + x.get("consistency", 0) * 0.5),
                reverse=True,
            )

            final_grid.extend(team_drivers[:team_car_limit(team)])

    # Player
    if state.player_constructor and state.player_constructor in by_team:
        final_grid.extend(by_team[state.player_constructor][:1])

    # 2) Fill the rest of the grid with Independents (open pool)
    independents = by_team.get("Independent", [])

    # IMPORTANT: don't always pick the same top guys
    # Shuffle first, then lightly sort by ability so it still feels “real”
    random.shuffle(independents)
    independents.sort(
        key=lambda x: (x.get("pace", 0) * 1.0 + x.get("consistency", 0) * 0.4),
        reverse=True,
    )

    # Fill remaining slots up to grid_size
    remaining = max(0, grid_size - len(final_grid))
    final_grid.extend(independents[:remaining])

    return final_grid


def roll_race_weather(track_profile):
    """
    Decide race-day weather once, so you can show a forecast before the player
    picks their risk level.
    Returns (is_wet, is_hot).
    """
    track_wet_chance = track_profile.get("wet_chance", WEATHER_WET_CHANCE)
    is_wet = random.random() < track_wet_chance

    base_hot_chance = track_profile.get("base_hot_chance", 0.2)
    is_hot = False
    if not is_wet:
        is_hot = random.random() < base_hot_chance

    return is_wet, is_hot

def run_ai_only_race(state, race_name, time, season_week, track_profile):
    """
    AI-only race simulation for weeks where the player does not/cannot compete.

    IMPORTANT:
    - This version includes engine failures + crashes (DNFs), using the same core logic
      style as run_race(), but without player wear/damage effects.
    - Fame/XP update is applied to FINISHERS only (DNFs don't gain post-race fame).
    """

    # Roll conditions for flavour + crash modifiers
    is_wet, is_hot = roll_race_weather(track_profile)

    
    finishers = []
    retired = []  # list of (driver, reason)

    track_pace_w = track_profile.get("pace_weight", 1.0)
    track_cons_w = track_profile.get("consistency_weight", 1.0)

    # Race length factor (endurance = more failures)
    race_distance_km = track_profile.get("race_distance_km", 250.0)
    race_length_factor = race_distance_km / 250.0

    reliability_mult = get_reliability_mult(time)
    crash_mult = get_crash_mult(time)

    event_grid = build_event_grid(state, time, race_name, track_profile)
    grid_size = len(event_grid)
    grid_risk_mult = 1.0 + max(0, grid_size - 12) * 0.01  # +1% per car above 12

    for d in event_grid:
        # Player shouldn't appear in AI-only race
        if state.player_driver is d:
            continue
        if state.player_constructor and d.get("constructor") == state.player_constructor:
            continue

   

        ctor_speed, ctor_reliability = get_ai_car_stats(d["constructor"])
        ctor_speed = max(1, ctor_speed)
        reliability = ctor_reliability

        # ---------- Performance roll (same vibe as your existing AI sim) ----------
        base = d["pace"] * track_pace_w + d["consistency"] * 0.4 * track_cons_w
        base += ctor_speed

        cons_factor = max(0.0, min(d["consistency"] / 10.0, 0.95))
        variance = (
            random.uniform(-1, 1)
            * (1 - cons_factor)
            * base
            * 0.25
        )
        performance = base + variance

        # Wet pace effect
        if is_wet:
            wet_factor = d.get("wet_skill", 5) / 10.0
            performance *= (0.9 + wet_factor * 0.3)

        # Heat pace effect (small)
        if is_hot:
            heat_handling = (d.get("mechanical_sympathy", 5) + d.get("consistency", 5)) / 20.0
            performance *= (0.97 + heat_handling * 0.06)

        # ---------- DNF logic (ported from run_race, simplified for AI) ----------
        mech = d.get("mechanical_sympathy", 5)
        aggression = d.get("aggression", 5)
        consistency = d.get("consistency", 5)
        wet_skill = d.get("wet_skill", 5)

        # Engine fail chance
        engine_fail_chance = (11 - reliability) * 0.02 * reliability_mult
        engine_fail_chance *= (1 + (5 - mech) * 0.05)
        engine_fail_chance *= track_profile.get("engine_danger", 1.0)
        engine_fail_chance *= race_length_factor

        # Hot-day engine stress (AI heat tolerance assumed average=5)
        if is_hot:
            heat_intensity = track_profile.get("heat_intensity", 1.0)
            engine_fail_chance *= heat_intensity

        # Crash chance
        base_crash_chance = (11 - consistency) * 0.012
        base_crash_chance *= (1 + (aggression - 5) * 0.05)
        base_crash_chance *= (1 + (5 - mech) * 0.03)

        crash_chance = base_crash_chance * crash_mult
        crash_chance *= track_profile.get("crash_danger", 1.0)

        # Wet -> more crashes, better wet_skill reduces it
        if is_wet:
            wet_factor = wet_skill / 10.0
            rain_crash_mult = 1.40 - wet_factor * 0.30
            crash_chance *= rain_crash_mult

        # Suspension affects crash risk (AI too)
        sus = get_suspension_value_for_driver(state, d)
        sus_importance = suspension_track_factor(track_profile)

        crash_sus_mult = 1.08 - (sus - 5) * 0.02
        crash_sus_mult = clamp(crash_sus_mult, 0.88, 1.15)
        crash_sus_mult = 1.0 + (crash_sus_mult - 1.0) * sus_importance

        crash_chance *= crash_sus_mult
        crash_chance *= grid_risk_mult

        # ---------- Resolve DNF ----------
        if random.random() < engine_fail_chance:
            retired.append((d, "engine"))
            state.news.append(f"{d['name']} ({d['constructor']}) retired with engine failure.")

            # --- simple breakdown so the news doesn't default to "general fatigue" ---
            breakdown = []

            reliability = max(1, ctor_reliability)
            mech = d.get("mechanical_sympathy", 5)

            reliability_mult = get_reliability_mult(time)
            race_distance_km = track_profile.get("race_distance_km", 250.0)
            race_length_factor = race_distance_km / 250.0

            # Start from baseline
            base_chance = (11 - reliability) * 0.02 * reliability_mult
            running = base_chance

            def add_factor(label, mult):
                nonlocal running
                extra = running * (mult - 1.0)
                if extra > 0:
                    breakdown.append((label, extra))
                running *= mult

            # Make reliability show up as a real contributor (lower reliability = more baseline risk)
            # Weight isn't perfect science — it's just to stop "generic fatigue" lines.
            reliability_weight = max(0.0, (11 - reliability) * 0.02 * reliability_mult)
            breakdown.append(("car reliability", reliability_weight))

            add_factor("driver mechanical sympathy", (1 + (5 - mech) * 0.05))
            add_factor("track engine strain", track_profile.get("engine_danger", 1.0))
            add_factor("race distance", race_length_factor)

            if is_hot:
                add_factor("heat intensity", track_profile.get("heat_intensity", 1.0))

            breakdown.sort(key=lambda x: x[1], reverse=True)
            if not breakdown:
                breakdown = [("a run of bad luck", 1.0)]

            add_engine_failure_explanation(
                state, d, track_profile, is_hot, is_wet,
                perspective="neutral",
                breakdown=breakdown
            )
            continue


        if random.random() < crash_chance:
            retired.append((d, "crash"))
            state.news.append(f"{d['name']} ({d['constructor']}) crashed out of the race.")
            add_crash_explanation(state, d, track_profile, is_hot, is_wet, perspective="neutral")
            
            # Check for injuries (player driver only)
            if state.player_driver and d['name'] == state.player_driver['name']:
                injury_roll = random.random()
                if injury_roll < 0.05:  # 5% chance of career-ending injury
                    state.player_driver_injury_severity = 3
                    state.player_driver_injury_weeks_remaining = 0  # Immediate retirement
                    state.news.append(f"TERRIBLE NEWS: {d['name']} has suffered a career-ending injury in the crash!")
                    state.news.append(f"{d['name']} will never race again. Your team must find a new driver.")
                    # Clear player driver
                    state.player_driver = None
                elif injury_roll < 0.20:  # 15% chance of serious injury (2-6 weeks)
                    state.player_driver_injury_severity = 2
                    weeks_out = random.randint(2, 6)
                    state.player_driver_injury_weeks_remaining = weeks_out
                    state.news.append(f"BAD NEWS: {d['name']} has suffered a serious injury in the crash!")
                    state.news.append(f"{d['name']} will be unable to drive for {weeks_out} weeks.")
                else:  # 80% chance of minor injury (1-2 weeks)
                    state.player_driver_injury_severity = 1
                    weeks_out = random.randint(1, 2)
                    state.player_driver_injury_weeks_remaining = weeks_out
                    state.news.append(f"{d['name']} has suffered a minor injury in the crash.")
                    state.news.append(f"{d['name']} will be unable to drive for {weeks_out} week{'s' if weeks_out > 1 else ''}.")
                
                state.player_driver_injured = state.player_driver_injury_weeks_remaining > 0
            
            continue

        # Survived -> classified finisher
        finishers.append((d, performance))

    if not finishers:
        state.news.append(f"{race_name}: chaotic scenes — no cars reach the finish.")
        record_race_result(state, time, season_week, race_name, is_wet, is_hot, finishers, retired)
        state.completed_races.add(season_week)
        return



    # Sort finishers fastest to slowest
    finishers.sort(key=lambda x: x[1], reverse=True)

    # ------------------------------
    # DEMO FINALE (AI-only): force fatal DNF so they cannot be classified
    # ------------------------------
    victim = maybe_trigger_demo_finale(state, time, race_name)
    if victim:
        vname = victim.get("name")

        # If they were a finisher, pull them out of classification
        before_n = len(finishers)
        finishers = [(drv, perf) for (drv, perf) in finishers if drv.get("name") != vname]

        # Ensure we log it as a retirement
        retired.append((victim, "crash"))

        if len(finishers) != before_n:
            state.news.append(f"Classification update: {vname} is not classified after the incident.")

        # Remove from global pool so future seasons are consistent
        from gmr.data import drivers as global_drivers
        if victim in global_drivers:
            global_drivers.remove(victim)




    # Fame/XP progression should apply to FINISHERS, not entrants
    fame_mult = track_profile.get("fame_mult", 1.0)
    xp_mult = track_profile.get("xp_mult", 1.0)

    update_fame_after_race(
        finishers,
        fame_mult=fame_mult,
        race_name=race_name,
        season_week=season_week,
        year=time.year
    )

    # Sponsor story event: driver promo at Fame 2+
    from gmr.sponsorship import maybe_gallant_driver_promo
    maybe_gallant_driver_promo(state, time)


    update_driver_progress(state, finishers, time, xp_mult=xp_mult)

    # Championship points (finishers only)
    if CHAMPIONSHIP_ACTIVE:
        for pos, (d, _) in enumerate(finishers):
            if pos < len(POINTS_TABLE):
                state.points[d["name"]] += POINTS_TABLE[pos]

    # Headline with enhanced media flavor
    winner = finishers[0][0]
    if len(finishers) > 1:
        runner_up = finishers[1][0]
        headline = (
            f"{race_name}: {winner['name']} wins for {winner['constructor']}, "
            f"ahead of {runner_up['name']}."
        )
    else:
        headline = f"{race_name}: {winner['name']} wins for {winner['constructor']}."
    state.news.append(headline)

    # Add atmospheric and media coverage based on race conditions
    weather_descriptions = []
    if is_wet:
        weather_descriptions.extend([
            "Dramatic wet-weather victory as rain made conditions treacherous.",
            "Spectacular driving in the pouring rain - a true test of skill.",
            "Rain-soaked triumph as drivers battled aquaplaning and poor visibility.",
        ])
    elif is_hot:
        weather_descriptions.extend([
            "Scorching conditions tested cars and drivers to their limits.",
            "Heat haze shimmered over the track as temperatures soared.",
            "Tires and engines pushed to the brink in the blazing heat.",
        ])
    else:
        weather_descriptions.extend([
            "Perfect racing conditions produced an exciting spectacle.",
            "Clear skies and good grip led to wheel-to-wheel racing.",
            "A beautiful day for racing with excellent track conditions.",
        ])

    if weather_descriptions:
        state.news.append("RACE ATMOSPHERE: " + random.choice(weather_descriptions))

    # Media coverage for significant results
    if len(finishers) >= 3:
        winner_constructor = winner.get('constructor', 'Independent')
        second_constructor = finishers[1][0].get('constructor', 'Independent')
        third_constructor = finishers[2][0].get('constructor', 'Independent')

        # Constructor dominance
        if winner_constructor == second_constructor == third_constructor:
            state.news.append(f"DOMINANCE DISPLAY: {winner_constructor} sweeps the podium with a 1-2-3 finish!")

        # Close racing
        winner_perf = finishers[0][1]
        second_perf = finishers[1][1]
        if winner_perf - second_perf < 2.0:  # Very close finish
            state.news.append("PHOTO FINISH: Victory decided by the narrowest of margins!")

    # Crowd reactions and atmosphere
    crowd_reactions = [
        "The crowd erupts in cheers as the chequered flag falls.",
        "Spectators wave flags and banners in celebration of the racing.",
        "The grandstands buzz with excitement and conversation.",
        "Marshals in white coats direct the post-race procedures.",
        "Team personnel rush to congratulate their drivers.",
        "Journalists swarm the podium for interviews and photos.",
        "The pit lane comes alive with celebrations and analysis.",
    ]
    state.news.append("TRACKSIDE: " + random.choice(crowd_reactions))

    # Podium (finishers)
    podium = []
    for pos, (d, _) in enumerate(finishers[:3]):
        podium.append((d["name"], d["constructor"]))
    state.podiums[season_week] = podium
    state.podiums_year = time.year

    # Full classification with enhanced reporting
    state.news.append("Race Results (AI-only event):")
    for pos, (d, _) in enumerate(finishers, start=1):
        line = f"{pos}. {d['name']} ({d['constructor']})"
        if CHAMPIONSHIP_ACTIVE:
            pts = POINTS_TABLE[pos - 1] if (pos - 1) < len(POINTS_TABLE) else 0
            line += f" - {pts} pts"
        state.news.append(line)

    # Retirements list with more dramatic reporting
    if retired:
        state.news.append("Retirements:")
        for d, reason in retired:
            if reason == "engine":
                state.news.append(f"- {d['name']} ({d['constructor']}): engine failure")
                # Add media context for engine failures
                engine_comments = [
                    "Mechanical gremlins strike again in this relentless sport.",
                    "The roar of racing gives way to the silence of mechanical failure.",
                    "Engineers will be working through the night to understand this failure.",
                ]
                state.news.append("TECHNICAL ANALYSIS: " + random.choice(engine_comments))
            else:
                state.news.append(f"- {d['name']} ({d['constructor']}): crash")
                # Add media context for crashes
                crash_comments = [
                    "Safety marshals respond quickly to extract the driver.",
                    "The incident brings out the red flags and stops the race.",
                    "Medical teams stand ready as the car is recovered.",
                ]
                state.news.append("INCIDENT RESPONSE: " + random.choice(crash_comments))

    # Small prestige hit for skipping
    if state.prestige > 0:
        state.prestige = max(0.0, state.prestige - 0.2)

    record_race_result(state, time, season_week, race_name, is_wet, is_hot, finishers, retired)
    state.completed_races.add(season_week)

def get_grid_bonus_multiplier(position):
    """
    Simple grid-position bonus/penalty applied to race performance.
    Pole gets a small edge, deep backmarkers get a tiny drag.
    """
    if position == 1:
        return 1.04
    elif position == 2:
        return 1.03
    elif position == 3:
        return 1.02
    elif 4 <= position <= 6:
        return 1.01
    elif 7 <= position <= 10:
        return 1.00
    else:
        return 0.99  # very small penalty for starting at the back


def simulate_qualifying(state, race_name, time, track_profile):
    """
    Simulate a single qualifying session for this race.
    Returns:
      - ordered list of (driver, quali_score)
      - dict: driver_name -> grid performance multiplier
      - bool: whether qualifying was wet
    """
    # Track-based chance of a wet qualifying session
    quali_wet_chance = track_profile.get("wet_chance", WEATHER_WET_CHANCE)
    is_wet_quali = random.random() < quali_wet_chance

    # Announce quali conditions
    condition_label = "WET" if is_wet_quali else "DRY"
    print(f"\nQualifying for {race_name} – conditions: {condition_label}")

    results = []
    event_grid = build_event_grid(state, time, race_name, track_profile)

    for d in event_grid:
        # existing qualifying logic unchanged
        if not driver_enters_event(d, race_name, track_profile, state):
            continue

        # Base from pace + a bit of consistency, with track bias
        track_pace_w = track_profile.get("pace_weight", 1.0)
        track_cons_w = track_profile.get("consistency_weight", 1.0)

        base = d["pace"] * track_pace_w + d["consistency"] * 0.4 * track_cons_w

        # Aggression: drivers lean on it in qualifying more than in race
        base *= (1 + (d["aggression"] - 5) * 0.02)

        # Car performance: player uses actual car, AI uses constructor speed
        if d == state.player_driver:
            car_speed = get_car_speed_for_track(state, track_profile)

        else:
            car_speed, _ = get_ai_car_stats(d["constructor"])


        score = base + car_speed

        # Wet qualifying: wet_skill matters a lot for one-lap pace
        if is_wet_quali:
            wet_factor = d["wet_skill"] / 10.0  # 0–1
            score *= (0.9 + wet_factor * 0.4)

        # Variance: low consistency = swingy quali
        consistency_factor = d["consistency"] / 10.0
        consistency_factor = max(0.0, min(consistency_factor, 0.95))
        variance_scale = 0.45
        variance = (
            random.uniform(-1, 1)
            * (1 - consistency_factor)
            * score
            * 0.3  # qualifying is swingy but not insane
        )
        score += variance

        results.append((d, score))

    # Sort by fastest to slowest
    results.sort(key=lambda x: x[1], reverse=True)

    # Build grid bonus mapping
    grid_bonus = {}
    for pos, (d, _) in enumerate(results, start=1):
        grid_bonus[d["name"]] = get_grid_bonus_multiplier(pos)

    # -------- QUALI NEWS & FLAVOUR --------
    # Headline summary
    if len(results) >= 2:
        p1, p2 = results[0][0], results[1][0]
        if p1["constructor"] == p2["constructor"]:
            summary = (
                f"{p1['constructor']} lock out the front row: "
                f"{p1['name']} on pole, {p2['name']} P2."
            )
        else:
            summary = (
                f"{p1['name']} takes pole for {p1['constructor']}, "
                f"{p2['name']} joins on the front row."
            )
    elif len(results) == 1:
        p1 = results[0][0]
        summary = f"{p1['name']} takes pole for {p1['constructor']}."
    else:
        summary = "Qualifying completed."

    session_weather = "wet" if is_wet_quali else "dry"
    state.news.append(
        f"Qualifying for {race_name} ({session_weather} session): {summary}"
    )

    # Results (Q1/Q2/Q3...) into news
    state.news.append("Qualifying results:")
    for pos, (d, _) in enumerate(results, start=1):
        state.news.append(f"Q{pos}: {d['name']} ({d['constructor']})")


    return results, grid_bonus, is_wet_quali

def run_race(state, race_name, time, season_week, grid_bonus, is_wet, is_hot):
    state.news.append(f"=== {race_name} ===")

    # How swingy race performance is (qualifying is higher)
    variance_scale = 0.25

    if state.player_driver:
        eid = state.current_engine.get("unit_id") if state.current_engine else None
        state.news.append(
            f"DEBUG ENGINE: unit_id={eid}, wear={state.engine_wear:.0f}%, health={state.engine_health:.0f}%")


    # PATCH : remember if we've ever completed Vallone GP
    if race_name == "Vallone GP":
        state.ever_completed_vallone = True

    finishers = []
    dnf_drivers = []


    # Track why drivers retired this race (engine vs crash etc.)
    retire_reasons = {}  # driver_name -> "engine" or "crash"

    track_profile = tracks.get(
        race_name,
        {
            "engine_danger": 1.0,
            "crash_danger": 1.0,
            "pace_weight": 1.0,
            "consistency_weight": 1.0,
            "wet_chance": WEATHER_WET_CHANCE,
            "base_hot_chance": 0.2,
            "heat_intensity": 1.0,
            "race_distance_km": 250.0,
        },
    )



    # Race length factor: how long this race is relative to a baseline 250 km
    race_distance_km = track_profile.get("race_distance_km", 250.0)
    race_length_factor = race_distance_km / 250.0

    # ------------------------------
    # WEATHER: WET vs DRY + HOT DAYS
    # ------------------------------ 

    if is_wet:
        state.news.append("Rain falls over the circuit – conditions are WET.")
    else:
        if is_hot:
            state.news.append("Baking heat grips the circuit – HOT and dry conditions.")
        else:
            state.news.append("Skies stay clear – conditions are DRY.")

    event_grid = build_event_grid(state, time, race_name, track_profile)
    grid_size = len(event_grid)
    grid_risk_mult = 1.0 + max(0, grid_size - 12) * 0.01  # +1% per car above 12


    for d in event_grid:
        # existing race logic unchanged


        # --- Base driver performance with track bias ---
        track_pace_w = track_profile.get("pace_weight", 1.0)
        track_cons_w = track_profile.get("consistency_weight", 1.0)
        weight_pace_importance = track_profile.get("weight_pace_importance", 1.0)
        weight_crash_importance = track_profile.get("weight_crash_importance", 1.0)

        base_pace = d["pace"] * track_pace_w
        base_cons = d["consistency"] * 0.4 * track_cons_w

        car_xp = float(d.get("car_xp", 0.0)) if d == state.player_driver else 0.0
        car_xp = clamp(car_xp, 0.0, 10.0)


        # Consistency controls how wild the variance is
        consistency_factor = (d["consistency"] / 10) * track_cons_w
        consistency_factor = max(0.0, min(consistency_factor, 0.95))

        sus = get_suspension_value_for_driver(state, d)
        sus_importance = suspension_track_factor(track_profile)

        # 1–10 where 5 is baseline. Higher = less swing.
        # var_mult range roughly ~1.22 (sus=1) to ~0.95 (sus=10) before track factor.
        var_mult = 1.10 - (sus - 5) * 0.03
        var_mult = clamp(var_mult, 0.85, 1.30)

        # Track importance scales the effect away from 1.0
        # If importance = 1.35, effect is stronger. If 0.85, effect is weaker.
        var_mult = 1.0 + (var_mult - 1.0) * sus_importance

        variance = (
            random.uniform(-1, 1)
            * (1 - consistency_factor)
            * base_pace
            * variance_scale
            * track_pace_w
            * var_mult
)

        # Comfort reduces swinginess a bit (max ~20% reduction at 10.0)
        variance *= (1.0 - car_xp * 0.02)

        performance = base_pace + base_cons + variance

   
        # Decide where the car performance comes from
        if d == state.player_driver:
            # Track-specific blend of engine speed vs acceleration
            car_speed = get_car_speed_for_track(state, track_profile)

            # Effective reliability lowered by long-term engine fatigue
            health_factor = max(0.2, state.engine_health / 100.0)
            car_reliability = state.car_reliability * health_factor
        else:
            car_speed, car_reliability = get_ai_car_stats(d["constructor"])


        performance += car_speed

        # Weather effect: in wet races, wet_skill matters for pace
        if is_wet:
            wet_factor = d["wet_skill"] / 10
            performance *= (0.9 + wet_factor * 0.3)

        # Heat effect
        if is_hot:
            heat_handling = (d["mechanical_sympathy"] + d["consistency"]) / 20.0
            performance *= (0.97 + heat_handling * 0.06)

        # Track-specific chassis weight effect on pace (player only)
        if d == state.player_driver and state.current_chassis:
            lightness = 11 - state.current_chassis["weight"]
            pace_weight_effect = 1 + (lightness - 5) * 0.03 * weight_pace_importance
            performance *= pace_weight_effect

        # Apply race strategy
        if d == state.player_driver:
            mode = getattr(state, "risk_mode", "neutral")
            if mode == "nurse":
                # Slightly slower, safer
                performance *= 0.97
            elif mode == "attack":
                # Slightly faster
                performance *= 1.03
        else:
            # AI strategy
            ai_mode = choose_ai_race_strategy(d, d["constructor"])
            if ai_mode == "nurse":
                performance *= 0.97
            elif ai_mode == "attack":
                performance *= 1.03
            # neutral: no change



        # Apply grid position bonus/penalty from qualifying
        performance *= grid_bonus.get(d["name"], 1.0)

        # --- DNF chances: engine vs crash ---
        reliability_mult = get_reliability_mult(time)

        # Engine failure from car reliability
        reliability = car_reliability
        engine_fail_chance = (11 - reliability) * 0.02 * reliability_mult

        # Driver-side influence: mechanical sympathy
        mech = d["mechanical_sympathy"]
        engine_fail_chance *= (1 + (5 - mech) * 0.05)

        # Track influence
        engine_fail_chance *= track_profile["engine_danger"]

        # Long-term engine condition: worn units fail more often
        if d == state.player_driver:
            wear_factor = max(0.2, min(state.engine_wear / 100.0, 1.0))  # clamp 0.2–1.0
            # At 100%: *1.0; at 70%: ~1.3; at 50%: ~1.5; at 20%: ~1.8
            engine_fail_chance *= (1 + (1 - wear_factor))


        # Race length: endurance events expose engines longer
        engine_fail_chance *= race_length_factor

        # Engine heat tolerance: only meaningful on hot days
        if d == state.player_driver and state.current_engine:
            heat_tol = state.current_engine.get("heat_tolerance", 5)
        else:
            heat_tol = 5  # average for AI

        if is_hot:
            heat_intensity = track_profile.get("heat_intensity", 1.0)
            engine_fail_chance *= heat_intensity
            engine_fail_chance *= (1 + (5 - heat_tol) * 0.06)       


        # Crash chance from driver consistency
        consistency = d["consistency"]
        base_crash_chance = (11 - consistency) * 0.012
        aggression = d["aggression"]
        base_crash_chance *= (1 + (aggression - 5) * 0.05)
        base_crash_chance *= (1 + (5 - mech) * 0.03)
        

        # Player chassis effect on crash risk (light & worn chassis are twitchy)
        if d == state.player_driver and state.current_chassis:
            lightness = 11 - state.current_chassis["weight"]
            base_crash_chance *= (1 + (lightness - 5) * 0.02 * weight_crash_importance)

            # Extra risk when the chassis is tired
            chassis_factor = (100.0 - state.chassis_health) / 100.0  # 0 at 100%, 1 at 0%
            base_crash_chance *= (1 + chassis_factor * 0.5)  # up to +50% at 0% health

        crash_mult = get_crash_mult(time)
        crash_chance = base_crash_chance * crash_mult
        crash_chance *= grid_risk_mult


        # Track influence
        crash_chance *= track_profile["crash_danger"]

        # Long-term chassis condition: tired frames are scarier to crash in
        if d == state.player_driver:
            chassis_factor = max(0.2, min(state.chassis_wear / 100.0, 1.0))
            # At 100%: *1.0; at 70%: ~1.33; at 50%: ~1.55; at 20%: ~1.88
            crash_chance *= (1 + (1 - chassis_factor) * 1.1)


        # Weather: wet -> more crashes, mitigated by wet_skill
        if is_wet:
            wet_factor = d["wet_skill"] / 10.0
            rain_crash_mult = 1.40 - wet_factor * 0.30
            crash_chance *= rain_crash_mult

        sus = get_suspension_value_for_driver(state, d)
        sus_importance = suspension_track_factor(track_profile)

        # baseline around 5.
        crash_sus_mult = 1.08 - (sus - 5) * 0.02
        crash_sus_mult = clamp(crash_sus_mult, 0.88, 1.15)

        crash_sus_mult = 1.0 + (crash_sus_mult - 1.0) * sus_importance
        crash_chance *= crash_sus_mult



        # Apply race strategy to failure risks (player only)
        if d == state.player_driver:
            mode = getattr(state, "risk_mode", "neutral")
            if mode == "nurse":
                engine_fail_chance *= 0.75
                crash_chance *= 0.70
            elif mode == "attack":
                engine_fail_chance *= 1.25
                crash_chance *= 1.30


        # Comfort reduces crash risk slightly (max ~15% at 10.0)
        crash_chance *= (1.0 - car_xp * 0.015)


        # --- Build breakdown of what made engine risk high (for better news blurbs) ---
        # Rank factors by how much extra failure probability they add above the base.
        engine_fail_breakdown = []

        base_chance = (11 - reliability) * 0.02 * reliability_mult  # reliability-only baseline
        running = base_chance

        def add_factor(label, mult):
            nonlocal running
            extra = running * (mult - 1.0)
            if extra > 0:
                engine_fail_breakdown.append((label, extra))
            running *= mult

        # Mechanical sympathy
        mech_mult = (1 + (5 - mech) * 0.05)
        add_factor("driver mechanical sympathy", mech_mult)

        # Track strain
        track_mult = track_profile.get("engine_danger", 1.0)
        add_factor("track engine strain", track_mult)

        # Wear + health (player only)
        if d == state.player_driver:
            wear_factor = max(0.2, min(state.engine_wear / 100.0, 1.0))
            wear_mult = (1 + (1 - wear_factor))
            add_factor("engine condition", wear_mult)

            # Only mention long-term fatigue when it's actually meaningfully degraded
            if state.engine_health < 75.0:
                health_factor = max(0.2, state.engine_health / 100.0)
                health_mult = 1 / health_factor
                add_factor("long-term engine fatigue", health_mult)


        # Race length
        add_factor("race distance", race_length_factor)

        # Heat (only if hot)
        if is_hot:
            heat_intensity = track_profile.get("heat_intensity", 1.0)
            add_factor("heat intensity", heat_intensity)

            heat_tol_mult = (1 + (5 - heat_tol) * 0.06)
            add_factor("heat tolerance", heat_tol_mult)

        # Sort by biggest extra-risk contributor
        engine_fail_breakdown.sort(key=lambda x: x[1], reverse=True)

        if not engine_fail_breakdown:
            # If nothing actually increased risk, don't lie to the player.
            # This covers "new engine, normal track, normal distance" failures.
            if is_hot:
                engine_fail_breakdown = [("heat stress", 1.0)]
            elif track_profile.get("engine_danger", 1.0) > 1.02:
                engine_fail_breakdown = [("track engine strain", 1.0)]
            elif race_length_factor > 1.10:
                engine_fail_breakdown = [("race distance", 1.0)]
            else:
                engine_fail_breakdown = [("an undetected component defect", 1.0)]


        # ------------------------------
        # ENGINE FAILURE CHECK
        # ------------------------------
        if random.random() < engine_fail_chance:
            is_player = (d == state.player_driver)

            if is_player and state.engine_wear < 50.0:
                # Low-condition engine: chance it's completely destroyed
                if random.random() < 0.4:
                    state.news.append(
                        f"{d['name']} ({d['constructor']}) suffers a huge engine blow-up – the unit is beyond saving."
                    )
                    state.engine_wear = 0.0

                    # Hardware fatigue: future ceiling drops
                    if state.engine_max_condition > 40.0:
                        state.engine_max_condition -= 10.0

                    # Scrap engine completely
                    state.current_engine = None
                    state.car_speed = 0
                    state.car_reliability = 0

                    state.news.append(
                        "Your mechanics confirm the engine is scrap metal only – "
                        "you'll need to buy or install a new unit before racing again."
                    )

                    retire_reasons[d["name"]] = "engine"

                    add_engine_failure_explanation(
                        state, d, track_profile, is_hot, is_wet,
                        perspective="player",
                        breakdown=engine_fail_breakdown
                    )

                else:
                    state.news.append(
                        f"{d['name']} ({d['constructor']}) retired with engine failure."
                    )
                    retire_reasons[d["name"]] = "engine"

                    add_engine_failure_explanation(
                        state, d, track_profile, is_hot, is_wet,
                        perspective="player",
                        breakdown=engine_fail_breakdown
                    )

            else:
                # AI or healthier engines
                state.news.append(
                    f"{d['name']} ({d['constructor']}) retired with engine failure."
                )
                retire_reasons[d["name"]] = "engine"

                add_engine_failure_explanation(
                    state, d, track_profile, is_hot, is_wet,
                    perspective="neutral",
                    breakdown=engine_fail_breakdown
                )
            dnf_drivers.append(d)
            continue  # stop processing this driver



        # ------------------------------
        # CRASH CHECK (ONLY IF ENGINE SURVIVED)
        # ------------------------------

        # --- Build breakdown of what made crash risk high (for better news blurbs) ---
        crash_breakdown = []

        base_c = (11 - consistency) * 0.012
        running_c = base_c

        def add_crash_factor(label, mult):
            nonlocal running_c
            extra = running_c * (mult - 1.0)
            if extra > 0:
                crash_breakdown.append((label, extra))
            running_c *= mult

        # Driver factors
        add_crash_factor("driver aggression", (1 + (aggression - 5) * 0.05))
        add_crash_factor("driver mechanical sympathy", (1 + (5 - mech) * 0.03))

        # Track danger
        add_crash_factor("track danger", track_profile.get("crash_danger", 1.0))

        # Wet conditions (if wet)
        if is_wet:
            wet_factor = d.get("wet_skill", 5) / 10.0
            rain_crash_mult = 1.40 - wet_factor * 0.30
            add_crash_factor("wet conditions", rain_crash_mult)

        # Suspension (only if it actually increased risk above baseline)
        add_crash_factor("suspension compliance", crash_sus_mult)

        # Player-only chassis condition multipliers
        if d == state.player_driver and state.current_chassis:
            lightness = 11 - state.current_chassis["weight"]
            add_crash_factor("chassis lightness", (1 + (lightness - 5) * 0.02 * weight_crash_importance))

            chassis_factor = max(0.2, min(state.chassis_wear / 100.0, 1.0))
            add_crash_factor("chassis wear", (1 + (1 - chassis_factor) * 1.1))

        crash_breakdown.sort(key=lambda x: x[1], reverse=True)
        if not crash_breakdown:
            crash_breakdown = [("a simple driving error", 1.0)]


        if random.random() < crash_chance:
            if d == state.player_driver:
                heavy_shunt = random.random() < 0.35

                if heavy_shunt:
                    state.news.append(
                        f"{d['name']} ({d['constructor']}) has a heavy shunt and slams out of the race."
                    )
                else:
                    state.news.append(
                        f"{d['name']} ({d['constructor']}) loses it and crashes out of the race."
                    )

                add_crash_explanation(
                    state, d, track_profile, is_hot, is_wet,
                    perspective="player",
                    breakdown=crash_breakdown
                )

                # Check for injuries
                injury_roll = random.random()
                if injury_roll < 0.05:  # 5% chance of career-ending injury
                    state.player_driver_injury_severity = 3
                    state.player_driver_injury_weeks_remaining = 0  # Immediate retirement
                    state.news.append(f"TERRIBLE NEWS: {d['name']} has suffered a career-ending injury in the crash!")
                    state.news.append(f"{d['name']} will never race again. Your team must find a new driver.")
                    # Clear player driver
                    state.player_driver = None
                elif injury_roll < 0.20:  # 15% chance of serious injury (2-6 weeks)
                    state.player_driver_injury_severity = 2
                    weeks_out = random.randint(2, 6)
                    state.player_driver_injury_weeks_remaining = weeks_out
                    state.news.append(f"BAD NEWS: {d['name']} has suffered a serious injury in the crash!")
                    state.news.append(f"{d['name']} will be unable to drive for {weeks_out} weeks.")
                else:  # 80% chance of minor injury (1-2 weeks)
                    state.player_driver_injury_severity = 1
                    weeks_out = random.randint(1, 2)
                    state.player_driver_injury_weeks_remaining = weeks_out
                    state.news.append(f"{d['name']} has suffered a minor injury in the crash.")
                    state.news.append(f"{d['name']} will be unable to drive for {weeks_out} week{'s' if weeks_out > 1 else ''}.")
                
                state.player_driver_injured = state.player_driver_injury_weeks_remaining > 0

                # Damage values
                if heavy_shunt:
                    chassis_hit = random.uniform(25.0, 45.0)
                    engine_hit = random.uniform(15.0, 35.0)
                else:
                    chassis_hit = random.uniform(15.0, 30.0)
                    engine_hit = random.uniform(5.0, 20.0)

                old_chassis = state.chassis_wear
                old_engine = state.engine_wear

                state.chassis_wear = max(0.0, state.chassis_wear - chassis_hit)
                state.engine_wear = max(0.0, state.engine_wear - engine_hit)

                # Long-term fatigue
                state.chassis_health = max(0.0, state.chassis_health - chassis_hit * 0.5)
                state.engine_health = max(0.0, state.engine_health - engine_hit * 0.5)

                # Chassis write-off chance
                writeoff_chance = 0.15
                if old_chassis < 50.0:
                    writeoff_chance += 0.20
                if heavy_shunt:
                    writeoff_chance += 0.20

                if random.random() < writeoff_chance:
                    state.news.append(
                        "The chassis is twisted beyond repair – the car is written off."
                    )
                    state.chassis_wear = 0.0
                    if state.chassis_max_condition > 40.0:
                        state.chassis_max_condition -= 10.0
                    state.current_chassis = None
                    state.car_speed = 0
                else:
                    state.news.append(
                        f"Crash damage report: engine {old_engine:.0f}% → {state.engine_wear:.0f}%, "
                        f"chassis {old_chassis:.0f}% → {state.chassis_wear:.0f}%."
                    )

                # Engine write-off from impact
                engine_writeoff_chance = 0.0
                if heavy_shunt:
                    engine_writeoff_chance += 0.20
                if old_engine < 40.0:
                    engine_writeoff_chance += 0.20

                if random.random() < engine_writeoff_chance:
                    state.news.append(
                        "Your mechanics report the engine block is cracked – the unit is beyond repair."
                    )
                    state.engine_wear = 0.0
                    if state.engine_max_condition > 40.0:
                        state.engine_max_condition -= 10.0
                    state.current_engine = None
                    state.car_speed = 0
                    state.car_reliability = 0

            else:
                # AI crash
                state.news.append(
                    f"{d['name']} ({d['constructor']}) crashed out of the race."
                )

                add_crash_explanation(
                    state, d, track_profile, is_hot, is_wet,
                    perspective="neutral",
                    breakdown=crash_breakdown
                )


            retire_reasons[d["name"]] = "crash"
            dnf_drivers.append(d)
            continue


        # ------------------------------
        # FINISHER (ONLY IF NO ENGINE FAIL + NO CRASH)
        # ------------------------------
        finishers.append((d, performance))


    # Sort by performance
    finishers.sort(key=lambda x: x[1], reverse=True)

    # ------------------------------
    # DEMO FINALE (player race): force fatal DNF so they cannot be classified
    # ------------------------------
    victim = maybe_trigger_demo_finale(state, time, race_name)
    if victim:
        vname = victim.get("name")

        # Remove from classified finishers
        finishers = [(drv, perf) for (drv, perf) in finishers if drv.get("name") != vname]

        # Treat as crash retirement for prestige logic
        retire_reasons[vname] = "crash"

        # If victim is player's driver, they are a DNF and the contract ends brutally
        if state.player_driver and state.player_driver.get("name") == vname:
            dnf_drivers.append(state.player_driver)
            state.demo_player_died = True  # just a flag for after-results cleanup

        # Remove from global driver list for future seasons
        from gmr.data import drivers as global_drivers
        if victim in global_drivers:
            global_drivers.remove(victim)


    # ------------------------------
    # CAR COMFORT XP (car_xp)
    # ------------------------------
    # ------------------------------
    # CAR COMFORT XP (player only)
    # ------------------------------
    if state.player_driver:
        finished = any(d == state.player_driver for d, _ in finishers)
        started = (state.player_driver in dnf_drivers) or finished

        if started:
            gain = 1.0 if finished else 0.35
            state.player_driver["car_xp"] = round(
                min(10.0, float(state.player_driver.get("car_xp", 0.0)) + gain), 2
            )




    # Track your driver's results with your team
    player_finish_pos = None
    if state.player_driver:
        for pos, (d, _) in enumerate(finishers):
            if d == state.player_driver:
                player_finish_pos = pos
                break

        # They started the race, even if they DNF'd
        state.races_entered_with_team += 1

        if player_finish_pos is not None:
            # Wins / podiums
            if player_finish_pos == 0:
                state.wins_with_team += 1
                state.podiums_with_team += 1
            elif player_finish_pos <= 2:
                state.podiums_with_team += 1

            # Championship points with your team
            if player_finish_pos < len(POINTS_TABLE):
                state.points_with_team += POINTS_TABLE[player_finish_pos]

    fame_mult = track_profile.get("fame_mult", 1.0)
    xp_mult = track_profile.get("xp_mult", 1.0)


    update_fame_after_race(
        finishers,
        fame_mult=fame_mult,
        race_name=race_name,
        season_week=season_week,
        year=time.year
    )

    # Sponsor story event: driver promo at Fame 2+
    from gmr.sponsorship import maybe_gallant_driver_promo
    maybe_gallant_driver_promo(state, time)


    player_xp_gain = update_driver_progress(state, finishers, time, xp_mult=xp_mult)
    player_xp_gain += grant_participation_xp_for_dnfs(state, dnf_drivers, time, xp_mult=xp_mult)



    # ------------------------------
    # CHAMPIONSHIP POINTS + PRIZE MONEY
    # ------------------------------

    # Award points ONLY if a championship exists
    if CHAMPIONSHIP_ACTIVE:
        for pos, (drv, _) in enumerate(finishers):
            if pos < len(POINTS_TABLE):
                state.points[drv["name"]] += POINTS_TABLE[pos]

    # Pay prize money ONLY to the player's team (your cut of organiser prize)
    if state.player_driver and player_finish_pos is not None:
        raw_prize = get_prize_for_race_and_pos(race_name, player_finish_pos)  # player_finish_pos is 0-based
        if raw_prize > 0:
            prize_cut = int(raw_prize * CONSTRUCTOR_SHARE)

            state.money += prize_cut
            state.constructor_earnings += prize_cut
            state.last_week_prize_income += prize_cut
            state.last_week_income += prize_cut


    # Appearance money (paid for taking the start; even if you DNF)
    if state.player_driver:
        pay_appearance_money(state, race_name)


    # ------------------------------
    # SPONSORSHIP PAYMENTS
    # ------------------------------
    if state.sponsor_active and state.player_driver:
        # Appearance fee is paid as long as the car turned up for the race,
        # even if it retires
        state.sponsor_races_started += 1

        mult = getattr(state, "sponsor_rate_multiplier", 1.0)

        # Appearance money
        appearance = int(60 * mult)
        state.money += appearance
        state.last_week_income += appearance
        state.last_week_sponsor_income += appearance
        state.constructor_earnings += appearance

        # Points bonus ONLY if a championship exists
        if CHAMPIONSHIP_ACTIVE and player_finish_pos is not None and player_finish_pos < len(POINTS_TABLE):
            pts = POINTS_TABLE[player_finish_pos]
            points_bonus = int(pts * 10 * mult)
            state.money += points_bonus
            state.last_week_income += points_bonus
            state.last_week_sponsor_income += points_bonus
            state.constructor_earnings += points_bonus

        # Podium bonus (always valid, championship or not)
        if player_finish_pos is not None and player_finish_pos <= 2:
            state.sponsor_podiums += 1
            podium_bonus = int(120 * mult)
            state.money += podium_bonus
            state.last_week_income += podium_bonus
            state.last_week_sponsor_income += podium_bonus
            state.constructor_earnings += podium_bonus

        # Check sponsor goals
        if not state.sponsor_goals_races_started and state.sponsor_races_started >= 3:
            state.sponsor_goals_races_started = True
            bonus = 500  # bonus for completing races started goal
            state.money += bonus
            state.last_week_income += bonus
            state.last_week_sponsor_income += bonus
            state.constructor_earnings += bonus
            state.news.append(f"Sponsor bonus: Completed 3 races started goal! +£{bonus}")

        if not state.sponsor_goals_podium and state.sponsor_podiums >= 1:
            state.sponsor_goals_podium = True
            bonus = 1000  # bonus for completing podium goal
            state.money += bonus
            state.last_week_income += bonus
            state.last_week_sponsor_income += bonus
            state.constructor_earnings += bonus
            state.news.append(f"Sponsor bonus: Achieved first podium! +£{bonus}")

    # Pay driver salary ONLY on race weeks (mercenary model)
    if state.player_driver and state.driver_pay > 0:
        state.money -= state.driver_pay
        state.last_week_driver_pay = state.driver_pay
        state.last_week_outgoings += state.driver_pay


    # ------------------------------
    # PATCH D: POST-RACE DEBRIEF (YOUR TEAM)
    # ------------------------------
    if state.player_driver:
        # Store race-scoped numbers for UI/finances if needed
        state.last_race_xp_gained = player_xp_gain
        state.last_race_prize_gained = state.last_week_prize_income
        state.last_race_sponsor_gained = state.last_week_sponsor_income
        state.last_race_driver_pay = state.last_week_driver_pay

        team_name = state.player_constructor or "Your team"
        driver_name = state.player_driver["name"]

        # How close to next stat tick?
        current_xp_bank = state.player_driver.get("xp", 0.0)
        xp_to_next = max(0.0, 5.0 - current_xp_bank)

        state.news.append("")
        state.news.append(f"--- Post-Race Debrief ({team_name}) ---")
        state.news.append(f"Driver: {driver_name}")

        # XP line
        state.news.append(
            f"Experience gained: +{player_xp_gain:.1f} XP "
            f"(banked: {current_xp_bank:.1f}/5.0, {xp_to_next:.1f} to next improvement roll)"
        )

        # Money breakdown
        prize = state.last_week_prize_income
        sponsor = state.last_week_sponsor_income
        appearance = getattr(state, "last_week_appearance_income", 0)
        travel = getattr(state, "last_week_travel_cost", 0)
        pay = state.last_week_driver_pay

        state.news.append("Financial rundown:")
        state.news.append(f"  Prize money (your cut): +£{prize}")
        state.news.append(f"  Sponsor income: +£{sponsor}")
        state.news.append(f"  Appearance / start money: +£{appearance}")
        state.news.append(f"  Travel & logistics: -£{travel}")
        state.news.append(f"  Driver pay: -£{pay}")

        net = (prize + sponsor + appearance) - (travel + pay)
        sign = "+" if net >= 0 else "-"
        state.news.append(f"  Net from race weekend: {sign}£{abs(net)}")


    # Race classification: show ALL classified finishers plus prize money
    state.news.append("Race Results:")
    for pos, (d, _) in enumerate(finishers):
        place = pos + 1

        prize = get_prize_for_race_and_pos(race_name, pos)

        line = f"{place}. {d['name']} ({d['constructor']})"

        # Only show points if the championship exists
        if CHAMPIONSHIP_ACTIVE:
            pts = POINTS_TABLE[pos] if pos < len(POINTS_TABLE) else 0
            line += f" - {pts} pts"


        if prize > 0:
            line += f", Prize: £{prize}"
            if d == state.player_driver:
                ctor_share = int(prize * CONSTRUCTOR_SHARE)
                line += f" (your cut: £{ctor_share})"

        state.news.append(line)



    # Save podium (top 3 finishers) for calendar display
    top3 = []
    for pos, (d, _) in enumerate(finishers[:3]):
        top3.append((d["name"], d["constructor"]))
    state.podiums[season_week] = top3
    state.podiums_year = time.year

    # --- Prestige gains for the player team (now fame-weighted) ---
    if state.player_driver:
        fame = state.player_driver.get("fame", 0)

        # Step 1: base prestige change (same as before)
        base_change = 0.0

        if player_finish_pos is not None:
            # Classified finish
            if player_finish_pos == 0:
                base_change = 3.0   # win
            elif player_finish_pos == 1:
                base_change = 2.0   # P2
            elif player_finish_pos == 2:
                base_change = 1.5   # P3
            elif player_finish_pos < len(POINTS_TABLE):
                base_change = 1.0   # points but no podium
            else:
                base_change = 0.3   # solid finish
        else:
            # DNF – split by cause
            reason = retire_reasons.get(state.player_driver["name"])

            if reason == "engine":
                # Mechanical DNF – frustrating, but more “unlucky”
                base_change = -0.2
            elif reason == "crash":
                # Crash DNF – more of a black mark
                base_change = -0.8
            else:
                base_change = -0.5

        # Step 2: fame multiplier (unchanged)
        fame_capped = min(fame, 8)

        if base_change > 0:
            mult = 1.0 + fame_capped * 0.07
        elif base_change < 0:
            mult = 1.0 + fame_capped * 0.05
        else:
            mult = 1.0

        change = base_change * mult

        before = state.prestige
        state.prestige = max(0.0, min(100.0, state.prestige + change))

        # Optional: you can uncomment this if you want visible logs for debugging
        # state.news.append(
        #     f"Prestige change this race: base {base_change:+.2f}, fame {fame}, "
        #     f"mult {mult:.2f}, applied {change:+.2f} "
        #     f"({before:.1f} → {state.prestige:.1f})."
        # )


    # --- Post-race wear (player car only) ---
    if state.player_driver:
        base_engine_wear = 8.0    # typical GP
        base_chassis_wear = 5.0   # chassis ages a bit slower

        danger_factor_engine = track_profile.get("engine_danger", 1.0)
        danger_factor_chassis = track_profile.get("crash_danger", 1.0)

        engine_wear_loss = base_engine_wear * race_length_factor * danger_factor_engine
        chassis_wear_loss = base_chassis_wear * race_length_factor * danger_factor_chassis

        sus = int(state.current_chassis.get("suspension", 5)) if state.current_chassis else 5
        sus_importance = suspension_track_factor(track_profile)

        wear_sus_mult = 1.06 - (sus - 5) * 0.015
        wear_sus_mult = clamp(wear_sus_mult, 0.90, 1.12)
        wear_sus_mult = 1.0 + (wear_sus_mult - 1.0) * sus_importance

        chassis_wear_loss *= wear_sus_mult


        # Heat cooks engines; wet races are slightly gentler on the chassis
        if is_hot:
            engine_wear_loss *= 1.25
        if is_wet:
            chassis_wear_loss *= 0.9

        # Small randomness so it isn't totally deterministic
        engine_wear_loss *= random.uniform(0.8, 1.2)
        chassis_wear_loss *= random.uniform(0.8, 1.2)

        # Apply to condition, clamp at 0
        old_engine = state.engine_wear
        old_chassis = state.chassis_wear

        state.engine_wear = max(0.0, state.engine_wear - engine_wear_loss)
        state.chassis_wear = max(0.0, state.chassis_wear - chassis_wear_loss)

        state.news.append(
            f"Post-race inspection: engine {old_engine:.0f}% → {state.engine_wear:.0f}%, "
            f"chassis {old_chassis:.0f}% → {state.chassis_wear:.0f}%."
        )

    # --- Long-term wear from this race (player car only) ---
    if state.player_driver:
        # Base wear from track + distance
        engine_base_wear = 4.0 * race_length_factor * track_profile.get("engine_danger", 1.0)
        chassis_base_wear = 3.0 * race_length_factor * track_profile.get("crash_danger", 1.0)

        # Pace mode multiplies wear
        pace = getattr(state, "risk_mode", "neutral")
        risk_mult = getattr(state, "risk_multiplier", 1.0)

        engine_wear = engine_base_wear * risk_mult
        chassis_wear = chassis_base_wear * risk_mult

        # Extra punishment if you actually finished the full distance
        player_finished = any(d == state.player_driver for d, _ in finishers)
        if player_finished:
            engine_wear *= 1.2
            chassis_wear *= 1.2
        else:
            # If you retired early, you spared some miles
            engine_wear *= 0.8
            chassis_wear *= 0.8

        # Apply wear and clamp
        state.engine_health = max(0.0, state.engine_health - engine_wear)
        state.chassis_health = max(0.0, state.chassis_health - chassis_wear)

    # Small news blurbs at thresholds – match what the player sees
    if state.engine_wear < 40:
        state.news.append(
            "Your mechanics warn that the engine is getting very tired (<40% condition)."
        )
    elif state.engine_wear < 70:
        state.news.append(
            "The engine is showing its age – performance and reliability may start to drop."
        )

    if state.chassis_wear < 40:
        state.news.append(
            "Your chassis is badly fatigued – any big hit could write it off."
        )
    elif state.chassis_wear < 70:
        state.news.append(
            "Cracks and flex are appearing in the chassis – the ride is getting rough."
        )

    # If the scripted finale killed the player's driver, wipe the contract now.
    if getattr(state, "demo_player_died", False):
        state.player_driver = None
        state.driver_pay = 0
        state.driver_contract_races = 0
        state.demo_player_died = False
   
    retired = []
    for d in dnf_drivers:
        retired.append((d, retire_reasons.get(d.get("name"), "unknown")))

    # ✅ Contract tick ONLY after the race is finished
    started_race = (
        (state.player_driver in dnf_drivers) or
        any(d == state.player_driver for d, _ in finishers)
    )

    tick_driver_contract_after_race_end(state, time, started_race)

    record_race_result(state, time, season_week, race_name, is_wet, is_hot, finishers, retired)

    # ✅ CRITICAL: stop the race repeating
    state.completed_races.add(season_week)

    # ✅ If you use pending_race_week, clear it so the week doesn't re-trigger
    if getattr(state, "pending_race_week", None) == season_week:
        state.pending_race_week = None
        state.completed_races.add(season_week)


def handle_contract_end_after_race(state):
    """
    After a race, if the driver's contract has just hit 0 races remaining,
    offer a chance to renew. If declined, the driver leaves the team.
    """
    if not state.player_driver:
        return

    races_left = getattr(state, "driver_contract_races", 0)
    if races_left > 0:
        # Still races left on the deal, nothing to do.
        return

    d = state.player_driver
    team_name = state.player_constructor or "your team"

    print("\n=== Driver Contract Decision ===")
    print(f"{d['name']}'s contract with {team_name} has now expired.")
    print("Do you want to discuss a new deal with them?")

    choice = input("Renew this driver? (y/n): ").strip().lower()
    if choice != "y":
        # Let them go
        print(f"\nYou part ways with {d['name']} at the end of the weekend.")
        state.news.append(
            f"{d['name']} departs {team_name} as their contract ends."
        )
        d["constructor"] = "Independent"
        state.player_driver = None
        return

    print(f"\nYou sit down with {d['name']} to discuss a fresh contract.")

    # Re-use your hire logic: stats + fame → pay
    stat_sum = (
        d["pace"]
        + d["consistency"]
        + d["aggression"]
        + d["mechanical_sympathy"]
        + d["wet_skill"]
    )
    fame = d.get("fame", 0)

    base_pay = stat_sum * 2
    fame_factor = 1 + fame * 0.10
    pay_per_race = int(base_pay * fame_factor)

    while True:
        races_str = input(
            f"How many races do you want to offer {d['name']}? (1–12): "
        ).strip()
        if not races_str.isdigit():
            print("Please enter a number.")
            continue
        races = int(races_str)
        if races < 1:
            print("Contract must be at least 1 race.")
            continue
        if races > 12:
            print("Let's keep it to 12 races or fewer for now.")
            continue
        break

    total_value = pay_per_race * races

    print(f"\nProposed renewal:")
    print(f"  Length: {races} race(s)")
    print(f"  Pay per race: £{pay_per_race}")
    print(f"  Total value: £{total_value}")
    confirm = input("Confirm this renewed contract? (y/n): ").strip().lower()
    if confirm != "y":
        print("Talks break down; the driver moves on.")
        state.news.append(
            f"Contract talks with {d['name']} collapse; they leave {team_name}."
        )
        d["constructor"] = "Independent"
        state.player_driver = None
        return

    # Lock in renewed deal
    state.driver_contract_races = races
    state.driver_pay = pay_per_race
    d["constructor"] = team_name

    print(f"\n{d['name']} signs a new deal for {races} race(s).")
    state.news.append(
        f"{d['name']} signs a new contract with {team_name} for {races} race(s)."
    )

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


def add_engine_failure_explanation(
    state, d, track_profile, is_hot, is_wet,
    perspective="neutral", breakdown=None
):
    """
    Add a short news blurb explaining *why* the engine probably failed.
    If a breakdown is provided, use it instead of generic heuristics.
    """

    # ---------- NEW: use real breakdown if available ----------
    if breakdown:
        # Expecting list of (reason, weight), already sorted high → low
        top = breakdown[:2]
        reasons = [r for r, _ in top]

        if len(reasons) == 1:
            reason_text = reasons[0]
        else:
            reason_text = f"{reasons[0]} and {reasons[1]}"

        if perspective == "player":
            state.news.append(
                f"The crew pinpoint {reason_text} as the main cause of the engine failure."
            )
        else:
            state.news.append(
                f"Race debrief: {reason_text} were the primary contributors to the engine failure."
            )
        return

    # ---------- FALLBACK: old heuristic logic ----------
    factors = []

    if is_hot:
        factors.append("the extreme heat")
    if state.engine_wear < 60.0 and perspective == "player":
        factors.append("how tired the engine already was")
    if d.get("mechanical_sympathy", 5) <= 4:
        factors.append("poor mechanical sympathy")
    if track_profile.get("engine_danger", 1.0) > 1.05:
        factors.append("how hard this circuit is on engines")

    if not factors:
        factors.append("a run of small issues and bad luck")

    if len(factors) > 2:
        factors = random.sample(factors, 2)

    reason_text = factors[0] if len(factors) == 1 else " and ".join(factors)

    if perspective == "player":
        state.news.append(
            f"The crew reckon {reason_text} played a big part in the engine letting go."
        )
    else:
        state.news.append(
            f"Race debrief: {reason_text} likely contributed to the engine failure."
        )


def add_crash_explanation(state, d, track_profile, is_hot, is_wet, perspective="neutral", breakdown=None):
    """
    Add a short news blurb explaining *why* the crash probably happened.
    If a breakdown is provided, use it instead of generic heuristics.
    """
    # Use real breakdown if available
    if breakdown:
        top = breakdown[:2]
        reasons = [r for r, _ in top]

        if len(reasons) == 1:
            reason_text = reasons[0]
        else:
            reason_text = f"{reasons[0]} and {reasons[1]}"

        if perspective == "player":
            prefix = "Your race debrief suggests"
        else:
            prefix = "Post-race analysis suggests"

        state.news.append(f"{prefix} {reason_text} were key factors in the accident.")
        return

    # Fallback: old heuristic logic
    factors = []

    cons = d.get("consistency", 5)
    agg = d.get("aggression", 5)
    wet = d.get("wet_skill", 5)

    if cons <= 4:
        factors.append("a lack of consistency")
    if agg >= 7:
        factors.append("an aggressive driving style")
    if is_wet and wet <= 4:
        factors.append("poor wet-weather feel")
    if track_profile.get("crash_danger", 1.0) > 1.05:
        factors.append("how unforgiving the circuit is")
    if d == state.player_driver and state.chassis_wear < 60.0:
        factors.append("a tired, flexing chassis")

    # Suspension (player-only heuristic)
    if d == state.player_driver and state.current_chassis:
        sus = int(state.current_chassis.get("suspension", 5))
        if sus <= 3:
            factors.append("poor suspension compliance over bumps")

    if not factors:
        factors.append("a simple mistake pushed too far")

    if len(factors) > 2:
        factors = random.sample(factors, 2)

    reason_text = factors[0] if len(factors) == 1 else " and ".join(factors)

    prefix = "Your race debrief suggests" if perspective == "player" else "Post-race analysis suggests"
    state.news.append(f"{prefix} {reason_text} were key factors in the accident.")

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




def choose_ai_race_strategy(driver, constructor):
    """
    AI drivers choose strategy based on aggression and constructor.
    Returns risk_mode string.
    """
    aggression = driver.get("aggression", 5)
    
    # Base chance from aggression
    if aggression >= 7:
        attack_chance = 0.6
        nurse_chance = 0.1
    elif aggression <= 3:
        attack_chance = 0.1
        nurse_chance = 0.6
    else:
        attack_chance = 0.3
        nurse_chance = 0.3
    
    # Constructor influence
    if constructor == "Enzoni":
        attack_chance += 0.2  # More aggressive
    elif constructor == "Independent":
        nurse_chance += 0.1  # More conservative
    
    # Normalize
    attack_chance = min(attack_chance, 1.0)
    nurse_chance = min(nurse_chance, 1.0)
    neutral_chance = 1.0 - attack_chance - nurse_chance
    neutral_chance = max(neutral_chance, 0.0)
    
    rand = random.random()
    if rand < attack_chance:
        return "attack"
    elif rand < attack_chance + neutral_chance:
        return "neutral"
    else:
        return "nurse"






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
    
    # Check if driver is injured
    driver_injured = getattr(state, 'player_driver_injured', False) and getattr(state, 'player_driver_injury_weeks_remaining', 0) > 0

    if no_car or driver_injured:
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

        print("You watch from the paddock as other teams take part.")
        input("\nPress Enter to continue...")

        run_ai_only_race(state, race_name, time, season_week, track_profile)

        from gmr.sponsorship import maybe_offer_sponsor
        maybe_offer_sponsor(state, time)

        return


    # --------------------------------------------
    # You DO have a car and a driver: give a choice
    # --------------------------------------------
    print(f"\n{race_name} is scheduled for this week.")
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
                run_ai_only_race(state, race_name, time, season_week, track_profile)
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
                                state.last_week_travel_cost += transport_cost
                                if not hasattr(state, 'transport_paid_races'):
                                    state.transport_paid_races = set()
                                state.transport_paid_races.add(race_name)
                                state.news.append(f"Paid £{transport_cost} for international transport to {race_name}.")
                                print(f"Paid £{transport_cost}. Proceeding to the race.")
                            else:
                                print("You don't have enough money. Skipping the race.")
                                run_ai_only_race(state, race_name, time, season_week, track_profile)
                                return
                            break
                        elif sub_choice == "2":
                            print("Skipping the race.")
                            run_ai_only_race(state, race_name, time, season_week, track_profile)
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
                                state.last_week_travel_cost += transatlantic_cost
                                if not hasattr(state, 'transport_paid_races'):
                                    state.transport_paid_races = set()
                                state.transport_paid_races.add(race_name)
                                state.news.append(f"Paid £{transatlantic_cost} for transatlantic transport to {race_name}.")
                                print(f"Paid £{transatlantic_cost}. Proceeding to the race.")
                            else:
                                print("You don't have enough money. Skipping the race.")
                                run_ai_only_race(state, race_name, time, season_week, track_profile)
                                return
                            break
                        elif sub_choice == "2":
                            print("Skipping the race.")
                            run_ai_only_race(state, race_name, time, season_week, track_profile)
                            return
                        else:
                            print("Please choose 1 or 2.")

            break

        elif choice == "2":
            print(f"\nYou decide not to enter {race_name} this year.")
            print("You watch from the paddock as other teams take part.")
            input("\nPress Enter to continue...")

            # ❌ NO TRAVEL CHARGE when skipping
            run_ai_only_race(state, race_name, time, season_week, track_profile)
            return
        else:
            print("Please choose 1 to race or 2 to skip.")

    # ------------------------------
    # From here on: full race weekend
    # ------------------------------

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

            # Dump race news NOW so it feels like the race happened before any contract talk
            if state.news:
                print("\n--- Race Weekend News ---")
                for item in state.news:
                    print(item)
                print("-------------------------")
                state.news.clear()

            return  # ✅ leave race week after the race runs (prevents infinite loop)
  
            from gmr.sponsorship import maybe_offer_sponsor
            maybe_offer_sponsor(state, time)
            return
          

           
        else:
            print("Invalid choice. Please select 1 or 2.")