# gmr/sponsorship.py
# Expanded sponsorship system - supports multiple sponsors with goals and events

import random
from gmr.sponsors_data import (
    SPONSORS, SPONSOR_TIERS, SPONSOR_EVENTS,
    get_max_sponsor_slots, get_available_sponsors, get_sponsor_by_tier
)

# =============================================================================
# LEGACY SPONSOR_TYPES (for backwards compatibility with tests and old code)
# =============================================================================

SPONSOR_TYPES = {
    "Gallant Leaf Tobacco": {
        "personality": "aggressive_marketing",
        "media_focus": "advertising_campaigns",
        "press_events": ["promo_days", "advert_shoot", "press_conference"],
        "flavor_text": "The ambitious tobacco brand pushing into motorsport",
        "rivalries": ["health_campaigns", "rival_tobacco"],
    },
    "Valdieri Wines": {
        "personality": "elegant_traditional",
        "media_focus": "luxury_lifestyle",
        "press_events": ["wine_tasting", "vip_events", "charity_gala"],
        "flavor_text": "The prestigious Italian wine family branching into racing",
        "rivalries": ["rival_wine_brands"],
    },
    "Marconi Electronics": {
        "personality": "innovative_technical",
        "media_focus": "technology_showcase",
        "press_events": ["tech_demo", "innovation_awards", "future_vision"],
        "flavor_text": "The electronics giant showcasing cutting-edge technology",
        "rivalries": ["competitor_brands"],
    },
    "Castello Banking": {
        "personality": "prestigious_elite",
        "media_focus": "exclusive_networking",
        "press_events": ["private_dinner", "elite_gathering", "philanthropy_event"],
        "flavor_text": "The international banking house with racing ambitions",
        "rivalries": ["rival_banks"],
    },
    "Rossi Tires": {
        "personality": "performance_driven",
        "media_focus": "technical_excellence",
        "press_events": ["tire_tech_demo", "performance_test", "engineering_showcase"],
        "flavor_text": "The tire manufacturer proving their rubber on the track",
        "rivalries": ["competitor_tire_brands"],
    },
    "Aero Dynamics Ltd": {
        "personality": "cutting_edge_research",
        "media_focus": "aerodynamic_innovation",
        "press_events": ["wind_tunnel_demo", "research_presentation", "future_design"],
        "flavor_text": "The aviation spin-off bringing aerospace tech to racing",
        "rivalries": ["traditional_engineers"],
    },
}


def generate_media_event(sponsor_name, event_type, state, time):
    """
    Generate media coverage for sponsor events with more flavor and atmosphere.
    """
    sponsor_info = SPONSOR_TYPES.get(sponsor_name, {})
    team_name = state.player_constructor or "Your team"
    driver_name = state.player_driver.get("name", "your driver") if state.player_driver else "your driver"

    media_events = {
        "press_conference": [
            f"PRESS CONFERENCE: {sponsor_name} executives field questions about their racing partnership with {team_name}.",
            f"MEDIA SCRUM: Journalists surround {driver_name} after the {sponsor_name} press conference.",
            f"EXCLUSIVE INTERVIEW: {driver_name} speaks passionately about the {sponsor_name} partnership in a one-on-one with Racing Weekly.",
        ],
        "promo_day": [
            f"PROMO DAY: {driver_name} spends the day with {sponsor_name} marketing team, posing for photos and meeting fans.",
            f"BEHIND THE SCENES: Cameras capture {team_name}'s garage during the {sponsor_name} promotional shoot.",
            f"FAN EVENT: {sponsor_name} hosts a meet-and-greet with {driver_name}, drawing hundreds of enthusiastic supporters.",
        ],
        "advert_shoot": [
            f"ADVERTISING SHOOT: {driver_name} and the {team_name} car feature in a glamorous {sponsor_name} campaign.",
            f"PHOTO CALL: Professional photographers capture {driver_name} with the {sponsor_name} livery gleaming under studio lights.",
            f"COMMERCIAL BREAK: {sponsor_name} releases teaser images from their racing advert featuring {team_name}.",
        ],
        "wine_tasting": [
            f"WINE TASTING: {sponsor_name} hosts an exclusive tasting for {team_name} and select media at the {time.year} racing season.",
            f"VIP EVENT: {driver_name} attends a {sponsor_name} wine tasting, charming guests with racing anecdotes.",
            f"LUXURY LIFESTYLE: {sponsor_name} showcases their premium wines alongside {team_name}'s racing pedigree.",
        ],
        "tech_demo": [
            f"TECH DEMO: {sponsor_name} demonstrates cutting-edge electronics in the {team_name} garage.",
            f"INNOVATION SHOWCASE: Journalists witness {sponsor_name} technology integrated into {team_name}'s setup.",
            f"FUTURE TECH: {driver_name} tests {sponsor_name} prototype equipment during a media demonstration.",
        ],
        "tire_tech_demo": [
            f"TIRE TECH: {sponsor_name} engineers explain their compound secrets to {team_name} mechanics.",
            f"PERFORMANCE DEMO: {driver_name} participates in a {sponsor_name} tire testing session for media cameras.",
            f"ENGINEERING EXCELLENCE: {sponsor_name} showcases tire technology that helped {team_name} achieve podium results.",
        ],
    }

    if event_type in media_events:
        event_description = random.choice(media_events[event_type])
        state.news.append(f"MEDIA: {event_description}")

        # Add atmospheric flavor based on sponsor personality
        personality = sponsor_info.get("personality", "")
        if personality == "aggressive_marketing":
            state.news.append("The air fills with cigarette smoke as journalists mingle with racing personalities.")
        elif personality == "elegant_traditional":
            state.news.append("Crystal glasses clink as the event takes on an air of sophisticated celebration.")
        elif personality == "innovative_technical":
            state.news.append("The hum of prototype equipment provides a backdrop to technical discussions.")
        elif personality == "prestigious_elite":
            state.news.append("Discreet security ensures only the most exclusive guests attend the gathering.")
        elif personality == "performance_driven":
            state.news.append("The scent of rubber and oil mixes with the excitement of performance discussions.")
        elif personality == "cutting_edge_research":
            state.news.append("White-coated engineers discuss aerodynamics with intense technical precision.")


def maybe_weather_preparation(state, time):
    """
    Opportunity to prepare for upcoming weather conditions.
    """
    # Check if there's a pending race
    if not hasattr(state, 'pending_race_week') or not state.pending_race_week:
        return

    # 8% chance when there's a pending race
    if random.random() > 0.08:
        return

    from gmr.calendar import generate_calendar_for_year
    from gmr.data import tracks

    race_calendar = generate_calendar_for_year(time.year)
    if state.pending_race_week not in race_calendar:
        return

    race_name = race_calendar[state.pending_race_week]
    track_profile = tracks.get(race_name, {})
    wet_chance = track_profile.get("wet_chance", 0.2)
    hot_chance = track_profile.get("base_hot_chance", 0.2)

    team_name = state.player_constructor or "Your team"

    print(f"\n=== Weather Preparation for {race_name} ===")
    print("Your meteorologists have analyzed the forecast for the upcoming race.")
    print("You have time to make specific preparations.\n")

    options = []

    if wet_chance > 0.3:
        options.append(("Focus on wet-weather setup and tires", "wet_prep", "Better performance in rain"))
    if hot_chance > 0.3:
        options.append(("Prepare for high temperatures and overheating", "heat_prep", "Better performance in heat"))
    if wet_chance <= 0.3 and hot_chance <= 0.3:
        options.append(("Standard preparation for dry conditions", "dry_prep", "Optimized for normal weather"))

    # Always have a balanced option
    options.append(("Balanced preparation for any conditions", "balanced", "Good performance in all weather"))

    for i, (desc, prep_type, benefit) in enumerate(options, 1):
        print(f"{i}) {desc}")
        print(f"   Benefit: {benefit}\n")

    choice = input("How would you like to prepare? (1-4): ").strip()

    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(options):
            choice_idx = len(options) - 1  # Default to balanced
    except ValueError:
        choice_idx = len(options) - 1

    prep_desc, prep_type, benefit_desc = options[choice_idx]

    # Apply preparation effects
    if prep_type == "wet_prep":
        state.weather_preparation = "wet"
        state.news.append(f"WEATHER PREP: {team_name} focuses on wet-weather preparation for {race_name}.")
    elif prep_type == "heat_prep":
        state.weather_preparation = "heat"
        state.news.append(f"WEATHER PREP: {team_name} prepares for high temperatures at {race_name}.")
    elif prep_type == "dry_prep":
        state.weather_preparation = "dry"
        state.news.append(f"WEATHER PREP: {team_name} optimizes for dry conditions at {race_name}.")
    else:  # balanced
        state.weather_preparation = "balanced"
        state.news.append(f"WEATHER PREP: {team_name} takes balanced approach for {race_name}.")

    print(f"\nPreparation complete. {benefit_desc}.")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_active_sponsors(state):
    """Get list of currently active sponsors."""
    if not hasattr(state, 'sponsors'):
        state.sponsors = []
    return state.sponsors


def count_sponsors_by_tier(sponsors, tier):
    """Count how many sponsors of a given tier the team has."""
    return sum(1 for s in sponsors if s.get("tier") == tier)


def can_accept_sponsor(state, sponsor_info, year):
    """Check if team can accept another sponsor of this type."""
    sponsors = get_active_sponsors(state)
    tier = sponsor_info.get("tier", "associate")
    tier_info = SPONSOR_TIERS.get(tier, {})
    
    # Check max slots overall
    max_slots = get_max_sponsor_slots(year, state.prestige)
    if len(sponsors) >= max_slots:
        return False, f"Maximum {max_slots} sponsor slot(s) filled"
    
    # Check max per tier
    max_per_tier = tier_info.get("max_per_team", 1)
    current_of_tier = count_sponsors_by_tier(sponsors, tier)
    if current_of_tier >= max_per_tier:
        return False, f"Already have maximum {tier_info['name']} sponsor(s)"
    
    return True, "OK"


def create_sponsor_contract(name, sponsor_info, start_year, duration=2):
    """Create a new sponsor contract dictionary."""
    return {
        "name": name,
        "tier": sponsor_info.get("tier", "associate"),
        "start_year": start_year,
        "end_year": start_year + duration,
        "races_started": 0,
        "podiums": 0,
        "wins": 0,
        "fastest_laps": 0,
        "best_finish": None,
        "no_engine_failures": 0,
        "happiness": 50,  # Start neutral
        "rate_multiplier": 1.0,
        "goals_completed": {},
        "bonus_events_done": set(),
    }


def get_sponsor_payment_multiplier(sponsor):
    """Get the payment multiplier for a sponsor based on tier and happiness."""
    tier = sponsor.get("tier", "associate")
    tier_info = SPONSOR_TIERS.get(tier, {})
    base_mult = tier_info.get("payment_mult", 0.35)
    
    # Happiness affects payments (50 = neutral, higher = better)
    happiness = sponsor.get("happiness", 50)
    happiness_mult = 0.8 + (happiness / 100) * 0.4  # 0.8 to 1.2
    
    # Rate multiplier from negotiations
    rate_mult = sponsor.get("rate_multiplier", 1.0)
    
    return base_mult * happiness_mult * rate_mult


# =============================================================================
# SPONSOR OFFER SYSTEM
# =============================================================================

def maybe_offer_sponsor(state, time):
    """
    Main entry point for sponsor offers.
    Can offer multiple sponsors over time, respecting slot limits.
    """
    # Get current season week
    from gmr.core_time import get_season_week
    current_week = get_season_week(time)
    
    # Track offers per year using absolute week to handle year transitions
    last_offer_year = getattr(state, 'sponsor_last_offer_year', 0)
    last_offer_week = getattr(state, 'sponsor_last_offer_week', 0)
    
    # Reset offered list at year start
    if time.year > last_offer_year:
        state.sponsors_offered_this_year = set()
        state.sponsor_last_offer_week = 0
        last_offer_week = 0
    
    # Need at least 3 weeks between offers (within same year)
    if time.year == last_offer_year and current_week - last_offer_week < 3 and last_offer_week > 0:
        return
    
    # Need minimum prestige
    if state.prestige < 1.5:
        return
    
    # Need to have completed at least one race
    if not getattr(state, "ever_completed_vallone", False) and len(getattr(state, 'race_history', [])) < 1:
        return
    
    # Random chance (35% per eligible week - increased for better gameplay)
    if random.random() > 0.35:
        return
    
    # Check if we have room for more sponsors
    sponsors = get_active_sponsors(state)
    max_slots = get_max_sponsor_slots(time.year, state.prestige)
    
    if len(sponsors) >= max_slots:
        return  # Full up
    
    # Get available sponsors
    available = get_available_sponsors(time.year, state.prestige, sponsors)
    
    # Filter out ones we've already been offered this year
    offered_this_year = getattr(state, 'sponsors_offered_this_year', set())
    available = [(n, i) for n, i in available if n not in offered_this_year]
    
    if not available:
        return
    
    # Decide what tier to offer based on current sponsors and prestige
    # Prefer to fill title slot first, then technical, then associate
    offer_tier = None
    
    if state.prestige >= 3.0 and count_sponsors_by_tier(sponsors, "title") == 0:
        title_options = get_sponsor_by_tier(available, "title")
        if title_options:
            offer_tier = "title"
            available = title_options
    
    if offer_tier is None and state.prestige >= 2.0 and count_sponsors_by_tier(sponsors, "technical") == 0:
        tech_options = get_sponsor_by_tier(available, "technical")
        if tech_options:
            offer_tier = "technical"
            available = tech_options
    
    if offer_tier is None:
        # Just pick from whatever's available
        pass
    
    if not available:
        return
    
    # Pick 1-2 sponsors to offer choice between
    num_offers = min(2, len(available))
    offers = random.sample(available, num_offers)
    
    # Present the offer(s)
    state.sponsor_last_offer_week = current_week
    state.sponsor_last_offer_year = time.year
    present_sponsor_offers(state, time, offers)


def present_sponsor_offers(state, time, offers):
    """Present sponsor offer(s) to the player."""
    team_name = state.player_constructor or "Your team"
    
    print(f"\n{'='*60}")
    print(f"  💼 SPONSORSHIP {'OFFERS' if len(offers) > 1 else 'OFFER'}")
    print(f"{'='*60}")
    
    if len(offers) == 1:
        name, info = offers[0]
        present_single_offer(state, time, name, info, team_name)
    else:
        present_multiple_offers(state, time, offers, team_name)


def present_single_offer(state, time, name, info, team_name):
    """Present a single sponsor offer."""
    tier = info.get("tier", "associate")
    tier_info = SPONSOR_TIERS.get(tier, {})
    payments = info.get("base_payments", {})
    goals = info.get("goals", {})
    
    print(f"\nA representative from {name} approaches your team.")
    print(f'"{info.get("flavor", "We want to sponsor your racing team")}."')
    print(f"\nThey offer a {tier_info.get('name', 'Sponsorship')} deal:")
    
    print(f"\n  PAYMENTS:")
    print(f"    • £{payments.get('signing_bonus', 0):,} signing bonus")
    print(f"    • £{payments.get('appearance', 0)} per race started")
    print(f"    • £{payments.get('points', 0)} per championship point")
    print(f"    • £{payments.get('podium', 0)} per podium finish")
    print(f"    • £{payments.get('win', 0)} per race win")
    
    print(f"\n  GOALS (by end of contract):")
    if "races_to_start" in goals:
        print(f"    • Start at least {goals['races_to_start']} races")
    if "podiums_required" in goals:
        print(f"    • Achieve {goals['podiums_required']} podium(s)")
    if "wins_required" in goals:
        print(f"    • Win {goals['wins_required']} race(s)")
    if "min_finish" in goals:
        print(f"    • Finish in the top {goals['min_finish']} at least once")
    if "fastest_laps" in goals:
        print(f"    • Set {goals['fastest_laps']} fastest lap(s)")
    if "championship_position" in goals:
        print(f"    • Finish top {goals['championship_position']} in championship")
    if "no_engine_failures" in goals:
        print(f"    • Complete {goals['no_engine_failures']} races without engine failure")
    
    # Show special bonuses if any
    special = info.get("special_bonus", {})
    if special:
        print(f"\n  SPECIAL BENEFITS:")
        if "engine_reliability" in special:
            print(f"    • +{special['engine_reliability']*100:.1f}% engine reliability bonus")
        if "free_tyres" in special:
            print(f"    • {special['free_tyres']} free tyre sets per race")
        if "aero_development" in special:
            print(f"    • +{special['aero_development']*100:.1f}% aero development speed")
    
    contract_years = 2
    print(f"\n  Contract: {time.year} - {time.year + contract_years}")
    
    # Mark as offered
    if not hasattr(state, 'sponsors_offered_this_year'):
        state.sponsors_offered_this_year = set()
    state.sponsors_offered_this_year.add(name)
    
    choice = input("\n  Accept this sponsorship? (y/n): ").strip().lower()
    
    if choice == "y":
        accept_sponsor(state, time, name, info, contract_years)
    else:
        decline_sponsor(state, time, name, info)


def present_multiple_offers(state, time, offers, team_name):
    """Present multiple sponsor offers for player to choose from."""
    print(f"\nMultiple sponsors are interested in {team_name}!")
    print("Choose which offer to pursue:\n")
    
    for i, (name, info) in enumerate(offers, 1):
        tier = info.get("tier", "associate")
        tier_info = SPONSOR_TIERS.get(tier, {})
        payments = info.get("base_payments", {})
        
        print(f"  {i}) {name} ({tier_info.get('name', 'Sponsor')})")
        print(f"     \"{info.get('flavor', '')}\"")
        print(f"     Signing bonus: £{payments.get('signing_bonus', 0):,}")
        print(f"     Per race: £{payments.get('appearance', 0)} | Per podium: £{payments.get('podium', 0)}")
        
        # Show a key goal
        goals = info.get("goals", {})
        if "wins_required" in goals:
            print(f"     Key goal: Win {goals['wins_required']} race(s)")
        elif "podiums_required" in goals:
            print(f"     Key goal: {goals['podiums_required']} podium(s)")
        elif "races_to_start" in goals:
            print(f"     Key goal: Start {goals['races_to_start']} races")
        print()
    
    print(f"  {len(offers) + 1}) Decline all offers")
    
    # Mark all as offered
    if not hasattr(state, 'sponsors_offered_this_year'):
        state.sponsors_offered_this_year = set()
    for name, _ in offers:
        state.sponsors_offered_this_year.add(name)
    
    try:
        choice = int(input("\n  Your choice: ").strip())
    except ValueError:
        choice = len(offers) + 1
    
    if 1 <= choice <= len(offers):
        name, info = offers[choice - 1]
        # Show full details then confirm
        print(f"\n--- {name} Full Details ---")
        present_single_offer(state, time, name, info, team_name)
    else:
        print("\nYou decline all offers for now.")
        state.news.append(f"{team_name} turns down sponsorship approaches.")


def accept_sponsor(state, time, name, info, duration):
    """Accept a sponsor and add to active list."""
    team_name = state.player_constructor or "Your team"
    
    # Create the contract
    contract = create_sponsor_contract(name, info, time.year, duration)
    
    # Add to sponsors list
    sponsors = get_active_sponsors(state)
    sponsors.append(contract)
    
    # Pay signing bonus
    payments = info.get("base_payments", {})
    bonus = payments.get("signing_bonus", 0)
    if bonus > 0:
        state.money += bonus
        state.last_week_income += bonus
        state.last_week_sponsor_income += bonus
        state.constructor_earnings += bonus
    
    # Update legacy fields for compatibility
    if contract["tier"] == "title":
        state.sponsor_active = True
        state.sponsor_name = name
        state.sponsor_start_year = time.year
        state.sponsor_end_year = time.year + duration
        state.sponsor_races_started = 0
        state.sponsor_podiums = 0
    
    tier_info = SPONSOR_TIERS.get(contract["tier"], {})
    
    print(f"\n✅ Deal signed with {name}!")
    print(f"   £{bonus:,} signing bonus received.")
    state.news.append(f"SPONSORSHIP: {team_name} signs {tier_info.get('name', 'sponsorship')} deal with {name}!")


def decline_sponsor(state, time, name, info):
    """Decline a sponsor offer."""
    team_name = state.player_constructor or "Your team"
    
    # Small prestige boost for independence
    before = state.prestige
    state.prestige = min(100.0, state.prestige + 0.3)
    
    print(f"\nYou politely decline {name}'s offer.")
    print(f"   (Prestige +0.3 for maintaining independence)")
    state.news.append(f"{team_name} declines sponsorship from {name}.")


# =============================================================================
# SPONSOR PAYMENT PROCESSING
# =============================================================================

def process_sponsor_race_start(state, time, race_name):
    """Process sponsor payments for starting a race."""
    sponsors = get_active_sponsors(state)
    total_appearance = 0
    
    for sponsor in sponsors:
        # Check contract is still active
        if time.year > sponsor.get("end_year", 0):
            continue
        
        sponsor_name = sponsor.get("name")
        sponsor_info = SPONSORS.get(sponsor_name, {})
        payments = sponsor_info.get("base_payments", {})
        
        # Calculate appearance payment
        mult = get_sponsor_payment_multiplier(sponsor)
        appearance = int(payments.get("appearance", 0) * mult)
        
        if appearance > 0:
            total_appearance += appearance
        
        # Track race started
        sponsor["races_started"] = sponsor.get("races_started", 0) + 1
        
        # Update legacy tracking for title sponsor
        if sponsor["tier"] == "title":
            state.sponsor_races_started = sponsor["races_started"]
    
    if total_appearance > 0:
        state.money += total_appearance
        state.last_week_income += total_appearance
        state.last_week_sponsor_income += total_appearance
        state.constructor_earnings += total_appearance
    
    return total_appearance


def process_sponsor_race_finish(state, time, finish_pos, is_podium, is_win, got_fastest_lap, had_engine_failure):
    """Process sponsor payments and goal tracking after a race."""
    sponsors = get_active_sponsors(state)
    total_payment = 0
    
    for sponsor in sponsors:
        if time.year > sponsor.get("end_year", 0):
            continue
        
        sponsor_name = sponsor.get("name")
        sponsor_info = SPONSORS.get(sponsor_name, {})
        payments = sponsor_info.get("base_payments", {})
        goals = sponsor_info.get("goals", {})
        goal_bonuses = sponsor_info.get("goal_bonuses", {})
        
        mult = get_sponsor_payment_multiplier(sponsor)
        
        # Track best finish
        if finish_pos is not None:
            current_best = sponsor.get("best_finish")
            if current_best is None or finish_pos < current_best:
                sponsor["best_finish"] = finish_pos
        
        # Podium payment and tracking
        if is_podium:
            sponsor["podiums"] = sponsor.get("podiums", 0) + 1
            podium_pay = int(payments.get("podium", 0) * mult)
            total_payment += podium_pay
            
            # Update legacy
            if sponsor["tier"] == "title":
                state.sponsor_podiums = sponsor["podiums"]
        
        # Win payment and tracking
        if is_win:
            sponsor["wins"] = sponsor.get("wins", 0) + 1
            win_pay = int(payments.get("win", 0) * mult)
            total_payment += win_pay
        
        # Fastest lap tracking
        if got_fastest_lap:
            sponsor["fastest_laps"] = sponsor.get("fastest_laps", 0) + 1
        
        # Engine failure tracking
        if had_engine_failure:
            sponsor["no_engine_failures"] = 0
        else:
            sponsor["no_engine_failures"] = sponsor.get("no_engine_failures", 0) + 1
        
        # Check and award goal completion bonuses
        total_payment += check_and_award_goal_bonuses(state, sponsor, sponsor_info)
        
        # Happiness adjustments
        if is_win:
            sponsor["happiness"] = min(100, sponsor.get("happiness", 50) + 10)
        elif is_podium:
            sponsor["happiness"] = min(100, sponsor.get("happiness", 50) + 5)
        elif finish_pos and finish_pos <= 6:
            sponsor["happiness"] = min(100, sponsor.get("happiness", 50) + 2)
        elif had_engine_failure:
            sponsor["happiness"] = max(0, sponsor.get("happiness", 50) - 5)
    
    if total_payment > 0:
        state.money += total_payment
        state.last_week_income += total_payment
        state.last_week_sponsor_income += total_payment
        state.constructor_earnings += total_payment
    
    return total_payment


def process_sponsor_championship_points(state, time, points_earned):
    """Process sponsor payments for championship points."""
    if points_earned <= 0:
        return 0
    
    sponsors = get_active_sponsors(state)
    total_payment = 0
    
    for sponsor in sponsors:
        if time.year > sponsor.get("end_year", 0):
            continue
        
        sponsor_name = sponsor.get("name")
        sponsor_info = SPONSORS.get(sponsor_name, {})
        payments = sponsor_info.get("base_payments", {})
        
        mult = get_sponsor_payment_multiplier(sponsor)
        points_pay = int(payments.get("points", 0) * points_earned * mult)
        total_payment += points_pay
    
    if total_payment > 0:
        state.money += total_payment
        state.last_week_income += total_payment
        state.last_week_sponsor_income += total_payment
        state.constructor_earnings += total_payment
    
    return total_payment


def check_and_award_goal_bonuses(state, sponsor, sponsor_info):
    """Check if sponsor goals have been met and award bonuses."""
    goals = sponsor_info.get("goals", {})
    goal_bonuses = sponsor_info.get("goal_bonuses", {})
    goals_completed = sponsor.get("goals_completed", {})
    
    total_bonus = 0
    
    # Races started goal
    races_req = goals.get("races_to_start", 0)
    if races_req > 0 and not goals_completed.get("races_started"):
        if sponsor.get("races_started", 0) >= races_req:
            goals_completed["races_started"] = True
            bonus = goal_bonuses.get("races_completed", 0)
            total_bonus += bonus
            if bonus > 0:
                state.news.append(f"SPONSOR GOAL: {sponsor['name']} - Completed {races_req} races! +£{bonus}")
    
    # Podiums goal
    pods_req = goals.get("podiums_required", 0)
    if pods_req > 0 and not goals_completed.get("podiums"):
        if sponsor.get("podiums", 0) >= pods_req:
            goals_completed["podiums"] = True
            bonus = goal_bonuses.get("podium_achieved", 0)
            total_bonus += bonus
            if bonus > 0:
                state.news.append(f"SPONSOR GOAL: {sponsor['name']} - Achieved {pods_req} podium(s)! +£{bonus}")
    
    # Wins goal
    wins_req = goals.get("wins_required", 0)
    if wins_req > 0 and not goals_completed.get("wins"):
        if sponsor.get("wins", 0) >= wins_req:
            goals_completed["wins"] = True
            bonus = goal_bonuses.get("win_achieved", 0)
            total_bonus += bonus
            if bonus > 0:
                state.news.append(f"SPONSOR GOAL: {sponsor['name']} - Won {wins_req} race(s)! +£{bonus}")
    
    # Min finish goal
    min_finish = goals.get("min_finish")
    if min_finish and not goals_completed.get("min_finish"):
        best = sponsor.get("best_finish")
        if best is not None and best <= min_finish:
            goals_completed["min_finish"] = True
            bonus = goal_bonuses.get("finish_bonus", 0)
            total_bonus += bonus
            if bonus > 0:
                state.news.append(f"SPONSOR GOAL: {sponsor['name']} - Finished top {min_finish}! +£{bonus}")
    
    # Fastest laps goal
    fl_req = goals.get("fastest_laps", 0)
    if fl_req > 0 and not goals_completed.get("fastest_laps"):
        if sponsor.get("fastest_laps", 0) >= fl_req:
            goals_completed["fastest_laps"] = True
            bonus = goal_bonuses.get("fastest_lap_bonus", 0)
            total_bonus += bonus
            if bonus > 0:
                state.news.append(f"SPONSOR GOAL: {sponsor['name']} - Set {fl_req} fastest lap(s)! +£{bonus}")
    
    # No engine failures goal
    clean_req = goals.get("no_engine_failures", 0)
    if clean_req > 0 and not goals_completed.get("reliability"):
        if sponsor.get("no_engine_failures", 0) >= clean_req:
            goals_completed["reliability"] = True
            bonus = goal_bonuses.get("reliability_bonus", 0)
            total_bonus += bonus
            if bonus > 0:
                state.news.append(f"SPONSOR GOAL: {sponsor['name']} - {clean_req} clean races! +£{bonus}")
    
    sponsor["goals_completed"] = goals_completed
    
    # Update legacy goal tracking
    if sponsor["tier"] == "title":
        state.sponsor_goals_races_started = goals_completed.get("races_started", False)
        state.sponsor_goals_podium = goals_completed.get("podiums", False)
    
    return total_bonus


# =============================================================================
# SPONSOR EVENTS SYSTEM
# =============================================================================

def maybe_trigger_sponsor_event(state, time):
    """Randomly trigger sponsor events."""
    sponsors = get_active_sponsors(state)
    
    if not sponsors:
        return
    
    # 8% chance per week for an event
    if random.random() > 0.08:
        return
    
    # Pick a random active sponsor
    active = [s for s in sponsors if time.year <= s.get("end_year", 0)]
    if not active:
        return
    
    sponsor = random.choice(active)
    sponsor_name = sponsor.get("name")
    sponsor_info = SPONSORS.get(sponsor_name, {})
    
    # Get possible events for this sponsor
    possible_events = sponsor_info.get("events", [])
    if not possible_events:
        return
    
    # Filter out events already done
    done_events = sponsor.get("bonus_events_done", set())
    available_events = [e for e in possible_events if e not in done_events]
    
    if not available_events:
        return
    
    event_id = random.choice(available_events)
    event_info = SPONSOR_EVENTS.get(event_id)
    
    if not event_info:
        return
    
    # Special trigger conditions
    trigger = event_info.get("trigger")
    if trigger == "after_podium" and sponsor.get("podiums", 0) < 1:
        return
    
    present_sponsor_event(state, time, sponsor, event_id, event_info)


def present_sponsor_event(state, time, sponsor, event_id, event_info):
    """Present a sponsor event to the player."""
    sponsor_name = sponsor.get("name")
    team_name = state.player_constructor or "Your team"
    driver_name = state.player_driver.get("name", "your driver") if state.player_driver else "your driver"
    
    print(f"\n{'='*60}")
    print(f"  📋 SPONSOR EVENT: {sponsor_name}")
    print(f"{'='*60}")
    print(f"\n  {event_info.get('name', 'Event')}")
    print(f"  {event_info.get('description', '')}")
    
    options = event_info.get("options", [])
    
    print("\n  Options:")
    for i, opt in enumerate(options, 1):
        text = opt.get("text", "Option")
        money = opt.get("money", 0)
        prestige = opt.get("prestige", 0)
        happiness = opt.get("sponsor_happiness", 0)
        
        print(f"\n  {i}) {text}")
        if money != 0:
            sign = "+" if money >= 0 else ""
            print(f"      Money: {sign}£{money}")
        if prestige != 0:
            sign = "+" if prestige >= 0 else ""
            print(f"      Prestige: {sign}{prestige:.1f}")
        if happiness != 0:
            sign = "+" if happiness >= 0 else ""
            print(f"      Sponsor happiness: {sign}{happiness}")
    
    try:
        choice = int(input("\n  Your choice: ").strip())
        if choice < 1 or choice > len(options):
            choice = 1
    except ValueError:
        choice = 1
    
    chosen = options[choice - 1]
    apply_event_outcome(state, sponsor, event_id, chosen, team_name, driver_name)


def apply_event_outcome(state, sponsor, event_id, outcome, team_name, driver_name):
    """Apply the outcome of a sponsor event."""
    # Mark event as done
    if "bonus_events_done" not in sponsor:
        sponsor["bonus_events_done"] = set()
    sponsor["bonus_events_done"].add(event_id)
    
    # Apply money
    money = outcome.get("money", 0)
    if money != 0:
        state.money += money
        if money > 0:
            state.last_week_income += money
            state.last_week_sponsor_income += money
            state.constructor_earnings += money
    
    # Apply prestige
    prestige = outcome.get("prestige", 0)
    if prestige != 0:
        state.prestige = max(0.0, min(100.0, state.prestige + prestige))
    
    # Apply sponsor happiness
    happiness = outcome.get("sponsor_happiness", 0)
    if happiness != 0:
        sponsor["happiness"] = max(0, min(100, sponsor.get("happiness", 50) + happiness))
    
    # Apply fatigue (small engine/chassis health penalty)
    fatigue = outcome.get("fatigue", 0)
    if fatigue > 0:
        state.engine_health = max(0.0, getattr(state, 'engine_health', 100) - fatigue * 0.5)
        state.chassis_health = max(0.0, getattr(state, 'chassis_health', 100) - fatigue * 0.3)
    
    # Apply special bonuses
    special = outcome.get("special", {})
    if "free_tyres" in special:
        state.tyre_sets = getattr(state, 'tyre_sets', 0) + special["free_tyres"]
        state.news.append(f"Received {special['free_tyres']} free tyre sets from sponsor!")
    
    # Generate news
    sponsor_name = sponsor.get("name")
    if money > 0:
        state.news.append(f"SPONSOR: {sponsor_name} event - {team_name} receives £{money}.")
    elif money < 0:
        state.news.append(f"SPONSOR: {sponsor_name} event - {team_name} pays £{abs(money)}.")
    else:
        state.news.append(f"SPONSOR: {sponsor_name} event completed.")
    
    print(f"\n  Outcome applied.")


# =============================================================================
# END OF SEASON REVIEW
# =============================================================================

def review_sponsor_contracts(state, time):
    """End of season sponsor contract review."""
    sponsors = get_active_sponsors(state)
    
    expiring = [s for s in sponsors if s.get("end_year", 0) == time.year]
    
    for sponsor in expiring:
        review_single_sponsor(state, time, sponsor)


def review_single_sponsor(state, time, sponsor):
    """Review a single expiring sponsor contract."""
    sponsor_name = sponsor.get("name")
    sponsor_info = SPONSORS.get(sponsor_name, {})
    goals = sponsor_info.get("goals", {})
    goals_completed = sponsor.get("goals_completed", {})
    
    print(f"\n{'='*60}")
    print(f"  📊 SPONSOR REVIEW: {sponsor_name}")
    print(f"{'='*60}")
    
    # Check which goals were met
    all_goals_met = True
    
    print("\n  Goal Status:")
    
    if "races_to_start" in goals:
        met = goals_completed.get("races_started", False)
        status = "✅" if met else "❌"
        print(f"    {status} Races started: {sponsor.get('races_started', 0)}/{goals['races_to_start']}")
        if not met:
            all_goals_met = False
    
    if "podiums_required" in goals:
        met = goals_completed.get("podiums", False)
        status = "✅" if met else "❌"
        print(f"    {status} Podiums: {sponsor.get('podiums', 0)}/{goals['podiums_required']}")
        if not met:
            all_goals_met = False
    
    if "wins_required" in goals:
        met = goals_completed.get("wins", False)
        status = "✅" if met else "❌"
        print(f"    {status} Wins: {sponsor.get('wins', 0)}/{goals['wins_required']}")
        if not met:
            all_goals_met = False
    
    if "min_finish" in goals:
        met = goals_completed.get("min_finish", False)
        best = sponsor.get("best_finish", "N/A")
        status = "✅" if met else "❌"
        print(f"    {status} Best finish: P{best} (needed top {goals['min_finish']})")
        if not met:
            all_goals_met = False
    
    if "fastest_laps" in goals:
        met = goals_completed.get("fastest_laps", False)
        status = "✅" if met else "❌"
        print(f"    {status} Fastest laps: {sponsor.get('fastest_laps', 0)}/{goals['fastest_laps']}")
        if not met:
            all_goals_met = False
    
    happiness = sponsor.get("happiness", 50)
    print(f"\n  Sponsor satisfaction: {happiness}/100")
    
    if all_goals_met:
        print("\n  ✅ ALL GOALS MET!")
        state.prestige = min(100.0, state.prestige + 1.5)
        print("     Prestige +1.5")
        
        # Offer renewal with better terms
        offer_sponsor_renewal(state, time, sponsor, sponsor_info, improved=True)
    elif happiness >= 40:
        print("\n  ⚠️ Some goals missed, but sponsor is satisfied enough to continue.")
        offer_sponsor_renewal(state, time, sponsor, sponsor_info, improved=False)
    else:
        print("\n  ❌ SPONSOR DISAPPOINTED")
        state.prestige = max(0.0, state.prestige - 2.0)
        print("     Prestige -2.0")
        print(f"     {sponsor_name} will not renew.")
        
        # Remove from sponsors list
        sponsors = get_active_sponsors(state)
        if sponsor in sponsors:
            sponsors.remove(sponsor)
        
        state.news.append(f"SPONSOR: {sponsor_name} ends partnership after disappointing results.")


def offer_sponsor_renewal(state, time, sponsor, sponsor_info, improved):
    """Offer sponsor contract renewal."""
    sponsor_name = sponsor.get("name")
    payments = sponsor_info.get("base_payments", {})
    
    if improved:
        print(f"\n  {sponsor_name} offers improved renewal terms:")
        rate_bonus = 0.25
        renewal_bonus = int(payments.get("signing_bonus", 0) * 0.5)
    else:
        print(f"\n  {sponsor_name} offers standard renewal:")
        rate_bonus = 0
        renewal_bonus = 0
    
    print(f"    • {2}-year extension")
    if renewal_bonus > 0:
        print(f"    • £{renewal_bonus} renewal bonus")
    if rate_bonus > 0:
        print(f"    • +{int(rate_bonus*100)}% improved payment rates")
    
    choice = input("\n  Renew contract? (y/n): ").strip().lower()
    
    if choice == "y":
        # Extend contract
        sponsor["start_year"] = time.year + 1
        sponsor["end_year"] = time.year + 3
        sponsor["races_started"] = 0
        sponsor["podiums"] = 0
        sponsor["wins"] = 0
        sponsor["fastest_laps"] = 0
        sponsor["best_finish"] = None
        sponsor["no_engine_failures"] = 0
        sponsor["goals_completed"] = {}
        
        if improved:
            sponsor["rate_multiplier"] = sponsor.get("rate_multiplier", 1.0) + rate_bonus
        
        if renewal_bonus > 0:
            state.money += renewal_bonus
            state.last_week_income += renewal_bonus
            state.last_week_sponsor_income += renewal_bonus
            state.constructor_earnings += renewal_bonus
        
        print(f"\n  ✅ Contract renewed through {sponsor['end_year']}!")
        state.news.append(f"SPONSOR: {sponsor_name} renews partnership!")
    else:
        # Remove sponsor
        sponsors = get_active_sponsors(state)
        if sponsor in sponsors:
            sponsors.remove(sponsor)
        
        print(f"\n  Partnership with {sponsor_name} ends.")
        state.news.append(f"SPONSOR: {sponsor_name} partnership ends - no renewal.")


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def show_sponsor_status(state, time):
    """Display current sponsorship status."""
    sponsors = get_active_sponsors(state)
    max_slots = get_max_sponsor_slots(time.year, state.prestige)
    
    print(f"\n{'='*60}")
    print(f"  💼 SPONSORSHIP STATUS")
    print(f"{'='*60}")
    print(f"\n  Sponsor slots: {len(sponsors)}/{max_slots}")
    
    if not sponsors:
        print("\n  No active sponsors.")
        print("  Complete races and build prestige to attract sponsors.")
        return
    
    for sponsor in sponsors:
        if time.year > sponsor.get("end_year", 0):
            continue
        
        sponsor_name = sponsor.get("name")
        sponsor_info = SPONSORS.get(sponsor_name, {})
        tier = sponsor.get("tier", "associate")
        tier_info = SPONSOR_TIERS.get(tier, {})
        goals = sponsor_info.get("goals", {})
        goals_completed = sponsor.get("goals_completed", {})
        
        print(f"\n  ─── {sponsor_name} ({tier_info.get('name', 'Sponsor')}) ───")
        print(f"  Contract: {sponsor.get('start_year')}-{sponsor.get('end_year')}")
        print(f"  Happiness: {sponsor.get('happiness', 50)}/100")
        
        print("  Goals:")
        if "races_to_start" in goals:
            met = goals_completed.get("races_started", False)
            status = "✅" if met else f"{sponsor.get('races_started', 0)}/{goals['races_to_start']}"
            print(f"    Races: {status}")
        
        if "podiums_required" in goals:
            met = goals_completed.get("podiums", False)
            status = "✅" if met else f"{sponsor.get('podiums', 0)}/{goals['podiums_required']}"
            print(f"    Podiums: {status}")
        
        if "wins_required" in goals:
            met = goals_completed.get("wins", False)
            status = "✅" if met else f"{sponsor.get('wins', 0)}/{goals['wins_required']}"
            print(f"    Wins: {status}")
        
        if "min_finish" in goals:
            met = goals_completed.get("min_finish", False)
            best = sponsor.get("best_finish", "N/A")
            status = "✅" if met else f"P{best} (need top {goals['min_finish']})"
            print(f"    Best finish: {status}")


def get_sponsor_special_bonuses(state):
    """Get cumulative special bonuses from all sponsors."""
    sponsors = get_active_sponsors(state)
    bonuses = {
        "engine_reliability": 0,
        "free_tyres": 0,
        "aero_development": 0,
    }
    
    for sponsor in sponsors:
        sponsor_name = sponsor.get("name")
        sponsor_info = SPONSORS.get(sponsor_name, {})
        special = sponsor_info.get("special_bonus", {})
        
        for key in bonuses:
            if key in special:
                bonuses[key] += special[key]
    
    return bonuses


# =============================================================================
# LEGACY COMPATIBILITY - Keep old functions working
# =============================================================================

def maybe_gallant_driver_promo(state, time):
    """Legacy: Gallant driver promo event (now handled by general event system)."""
    # Check if Gallant is a sponsor
    sponsors = get_active_sponsors(state)
    gallant = next((s for s in sponsors if s.get("name") == "Gallant Leaf Tobacco"), None)
    
    if not gallant:
        return
    
    # Only trigger once
    if "driver_promo" in gallant.get("bonus_events_done", set()):
        return
    
    # Need a driver with fame 2+
    if not state.player_driver:
        return
    
    if state.player_driver.get("fame", 0) < 2:
        return
    
    # Trigger the event
    event_info = SPONSOR_EVENTS.get("driver_promo")
    if event_info:
        present_sponsor_event(state, time, gallant, "driver_promo", event_info)


def maybe_gallant_leaf_advert(state, time):
    """Legacy: Gallant advert event (now handled by general event system)."""
    sponsors = get_active_sponsors(state)
    gallant = next((s for s in sponsors if s.get("name") == "Gallant Leaf Tobacco"), None)
    
    if not gallant:
        return
    
    if "advert_shoot" in gallant.get("bonus_events_done", set()):
        return
    
    if state.prestige < 5.0:
        return
    
    event_info = SPONSOR_EVENTS.get("advert_shoot")
    if event_info:
        present_sponsor_event(state, time, gallant, "advert_shoot", event_info)


def maybe_sponsor_media_event(state, time):
    """Generate random media flavor events for sponsors."""
    maybe_trigger_sponsor_event(state, time)


# =============================================================================
# TYRE SPONSORSHIP SYSTEM (Keep existing)
# =============================================================================

TYRE_SPONSORS = {
    "Roadmaster Rubber Co.": {
        "flavor": "A budget rubber manufacturer looking to break into motorsport",
        "personality": "methodical_german",
        "min_prestige": 1.0,
        "tyres_per_race": 2,
        "goals": {
            "races_to_complete": 5,
            "min_finish_position": 10,
        },
    },
    "Veloce Gomme": {
        "flavor": "The Italian tyre company wants to prove their rubber on the track",
        "personality": "passionate_italian",
        "min_prestige": 3.0,
        "tyres_per_race": 3,
        "goals": {
            "races_to_complete": 4,
            "min_finish_position": 6,
            "podiums_required": 1,
        },
    },
    "Eagle Tyre Company": {
        "flavor": "The American tyre company expanding from domestic racing to Europe",
        "personality": "ambitious_american",
        "min_prestige": 5.0,
        "tyres_per_race": 4,
        "goals": {
            "races_to_complete": 6,
            "min_finish_position": 5,
            "podiums_required": 2,
        },
    },
    "Blackwall Racing": {
        "flavor": "The prestigious British tyre brand seeking championship contenders",
        "personality": "traditional_british",
        "min_prestige": 8.0,
        "tyres_per_race": 5,
        "goals": {
            "races_to_complete": 8,
            "wins_required": 1,
            "podiums_required": 3,
        },
    },
}


def maybe_offer_tyre_sponsorship(state, time):
    """Offer a tyre sponsorship deal."""
    if getattr(state, 'tyre_sponsor_active', False):
        return
    
    if getattr(state, 'tyre_sponsor_offer_seen_year', 0) == time.year:
        return
    
    races_completed = getattr(state, 'season_races_completed', 0)
    if races_completed < 1:
        return
    
    if random.random() > 0.30:
        return
    
    available = []
    for name, info in TYRE_SPONSORS.items():
        if state.prestige >= info["min_prestige"]:
            available.append((name, info))
    
    if not available:
        return
    
    sponsor_name, sponsor_info = random.choice(available)
    state.tyre_sponsor_offer_seen_year = time.year
    
    print(f"\n{'='*60}")
    print(f"  🛞 TYRE SPONSORSHIP OFFER")
    print(f"{'='*60}")
    print(f"\nA representative from {sponsor_name} approaches your team.")
    print(f'"{sponsor_info["flavor"]}."')
    print(f"\nThey offer a tyre supply deal for the {time.year} season:")
    print(f"  • {sponsor_info['tyres_per_race']} FREE tyre sets delivered before each race")
    print(f"\nGoals by season end:")
    
    goals = sponsor_info["goals"]
    print(f"  • Complete at least {goals['races_to_complete']} races")
    if "min_finish_position" in goals:
        print(f"  • Finish in the top {goals['min_finish_position']} at least once")
    if "podiums_required" in goals:
        print(f"  • Achieve {goals['podiums_required']} podium(s)")
    if "wins_required" in goals:
        print(f"  • Win {goals['wins_required']} race(s)")
    
    choice = input("\nAccept the tyre sponsorship? (y/n): ").strip().lower()
    
    if choice == "y":
        state.tyre_sponsor_active = True
        state.tyre_sponsor_name = sponsor_name
        state.tyre_sponsor_year = time.year
        state.tyre_sponsor_tyres_per_race = sponsor_info["tyres_per_race"]
        state.tyre_sponsor_goals = dict(goals)
        state.tyre_sponsor_races_completed = 0
        state.tyre_sponsor_best_finish = 99
        state.tyre_sponsor_podiums = 0
        state.tyre_sponsor_wins = 0
        
        initial_tyres = sponsor_info["tyres_per_race"] * 2
        state.tyre_sets = getattr(state, 'tyre_sets', 0) + initial_tyres
        
        print(f"\n✅ Deal signed with {sponsor_name}!")
        print(f"   {initial_tyres} tyre sets delivered immediately.")
        state.news.append(f"TYRE DEAL: {sponsor_name} signs with your team!")
    else:
        print(f"\nYou decline {sponsor_name}'s offer.")


def deliver_tyre_sponsor_tyres(state, time, race_name):
    """Deliver sponsor tyres before a race."""
    if not getattr(state, 'tyre_sponsor_active', False):
        return
    
    if time.year != getattr(state, 'tyre_sponsor_year', 0):
        return
    
    sponsor_name = getattr(state, 'tyre_sponsor_name', 'Unknown')
    tyres = getattr(state, 'tyre_sponsor_tyres_per_race', 0)
    
    if tyres > 0:
        state.tyre_sets = getattr(state, 'tyre_sets', 0) + tyres
        print(f"\n🛞 {sponsor_name} delivers {tyres} tyre sets for {race_name}.")


def update_tyre_sponsor_progress(state, finish_position, is_podium, is_win):
    """Update tyre sponsor goal progress after a race."""
    if not getattr(state, 'tyre_sponsor_active', False):
        return
    
    state.tyre_sponsor_races_completed = getattr(state, 'tyre_sponsor_races_completed', 0) + 1
    
    if finish_position < getattr(state, 'tyre_sponsor_best_finish', 99):
        state.tyre_sponsor_best_finish = finish_position
    
    if is_podium:
        state.tyre_sponsor_podiums = getattr(state, 'tyre_sponsor_podiums', 0) + 1
    
    if is_win:
        state.tyre_sponsor_wins = getattr(state, 'tyre_sponsor_wins', 0) + 1


def check_tyre_sponsor_goals(state, time):
    """Check tyre sponsor goals at end of season."""
    if not getattr(state, 'tyre_sponsor_active', False):
        return
    
    if time.year != getattr(state, 'tyre_sponsor_year', 0):
        return
    
    sponsor_name = getattr(state, 'tyre_sponsor_name', 'Unknown')
    goals = getattr(state, 'tyre_sponsor_goals', {})
    
    races_done = getattr(state, 'tyre_sponsor_races_completed', 0)
    best_finish = getattr(state, 'tyre_sponsor_best_finish', 99)
    podiums = getattr(state, 'tyre_sponsor_podiums', 0)
    wins = getattr(state, 'tyre_sponsor_wins', 0)
    
    goals_met = True
    failed = []
    
    if races_done < goals.get('races_to_complete', 0):
        goals_met = False
        failed.append(f"Races: {races_done}/{goals['races_to_complete']}")
    
    if 'min_finish_position' in goals and best_finish > goals['min_finish_position']:
        goals_met = False
        failed.append(f"Best finish: P{best_finish}, needed top {goals['min_finish_position']}")
    
    if 'podiums_required' in goals and podiums < goals['podiums_required']:
        goals_met = False
        failed.append(f"Podiums: {podiums}/{goals['podiums_required']}")
    
    if 'wins_required' in goals and wins < goals['wins_required']:
        goals_met = False
        failed.append(f"Wins: {wins}/{goals['wins_required']}")
    
    print(f"\n{'='*60}")
    print(f"  🛞 TYRE SPONSOR REVIEW — {sponsor_name}")
    print(f"{'='*60}")
    
    if goals_met:
        print(f"\n✅ GOALS MET! {sponsor_name} is pleased.")
        state.prestige = min(100.0, state.prestige + 1.0)
        state.tyre_sponsor_goals_met = True
    else:
        print(f"\n❌ GOALS NOT MET!")
        for f in failed:
            print(f"   • {f}")
        state.prestige = max(0.0, state.prestige - 2.0)
        state.tyre_sponsor_goals_met = False
    
    state.tyre_sponsor_active = False


def show_tyre_sponsor_status(state):
    """Display tyre sponsor status."""
    if not getattr(state, 'tyre_sponsor_active', False):
        print("\n  No active tyre sponsorship.")
        return
    
    sponsor_name = getattr(state, 'tyre_sponsor_name', 'Unknown')
    goals = getattr(state, 'tyre_sponsor_goals', {})
    
    print(f"\n  🛞 Tyre Sponsor: {sponsor_name}")
    print(f"     Tyres per race: {getattr(state, 'tyre_sponsor_tyres_per_race', 0)} sets")
    print(f"\n     Goals:")
    
    races = getattr(state, 'tyre_sponsor_races_completed', 0)
    req = goals.get('races_to_complete', 0)
    status = "✅" if races >= req else f"{races}/{req}"
    print(f"       Races: {status}")
    
    if 'min_finish_position' in goals:
        best = getattr(state, 'tyre_sponsor_best_finish', 99)
        req = goals['min_finish_position']
        status = "✅" if best <= req else f"P{best} (need top {req})"
        print(f"       Best finish: {status}")
    
    if 'podiums_required' in goals:
        pods = getattr(state, 'tyre_sponsor_podiums', 0)
        req = goals['podiums_required']
        status = "✅" if pods >= req else f"{pods}/{req}"
        print(f"       Podiums: {status}")


# =============================================================================
# LEGACY FUNCTIONS (backwards compatibility)
# =============================================================================

def maybe_offer_sponsor_renewal(state, time):
    """
    At start of new year, check if any sponsor contracts expired.
    Uses new multi-sponsor system but maintains old interface for main.py.
    """
    # Use the new system's review function
    review_sponsor_contracts(state, time)
