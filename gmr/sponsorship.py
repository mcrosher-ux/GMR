# gmr/sponsorship.py
# Sponsorship system for drivers

import random

# Enhanced sponsor types with more personality and media presence
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

        # Add some atmospheric flavor based on sponsor personality
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

def maybe_sponsor_media_event(state, time):
    """
    Random sponsor media events that add flavor and atmosphere to the game world.
    """
    if not state.sponsor_active:
        return

    sponsor_name = state.sponsor_name
    sponsor_info = SPONSOR_TYPES.get(sponsor_name, {})

    # 8% chance per week for a media event (reduced from 15%)
    if random.random() > 0.08:
        return

    press_events = sponsor_info.get("press_events", ["press_conference"])
    event_type = random.choice(press_events)

    generate_media_event(sponsor_name, event_type, state, time)

    # Occasionally add sponsor-specific rivalries or drama
    if random.random() < 0.3:  # 30% chance for additional drama
        rivalries = sponsor_info.get("rivalries", [])
        if rivalries and random.random() < 0.5:
            rivalry_type = random.choice(rivalries)
            drama_events = {
                "health_campaigns": [
                    "CONTROVERSY: Health advocates protest outside the circuit, targeting tobacco sponsorships.",
                    "DEBATE: Medical experts question the ethics of tobacco brands in motorsport.",
                ],
                "rival_tobacco": [
                    "COMPETITION: A rival tobacco brand launches a competing racing sponsorship.",
                    "MARKET WARS: Tobacco companies battle for motorsport supremacy through team backing.",
                ],
                "rival_wine_brands": [
                    "WINE RIVALRY: Competing vintners question the quality of sponsor's racing partnership.",
                    "TRADITION CLASH: Old-world wine houses view the sponsorship as undignified.",
                ],
                "competitor_brands": [
                    "TECH RIVALRY: Competing electronics firms criticize the sponsor's racing involvement.",
                    "MARKET SHARE: Electronics giants vie for attention through motorsport exposure.",
                ],
                "rival_banks": [
                    "BANKING POLITICS: Rival financial institutions question the sponsor's racing motives.",
                    "CORPORATE RIVALRY: Banking houses compete for prestige through team sponsorships.",
                ],
                "competitor_tire_brands": [
                    "TIRE WARS: Rival manufacturers challenge the sponsor's performance claims.",
                    "RUBBER RIVALRY: Tire companies battle for supremacy in the racing marketplace.",
                ],
                "traditional_engineers": [
                    "TRADITION vs INNOVATION: Old-school engineers dismiss the sponsor's 'radical' ideas.",
                    "METHODOLOGY DEBATE: Aerospace techniques spark controversy in traditional racing circles.",
                ],
            }

            if rivalry_type in drama_events:
                drama = random.choice(drama_events[rivalry_type])
                state.news.append(f"INDUSTRY NEWS: {drama}")


def maybe_gallant_driver_promo(state, time):
    """
    One-time sponsor event:
    If Gallant Leaf are sponsoring you AND your current driver reaches Fame 2,
    Gallant want to use them for promo. Player chooses how to respond.

    This is separate from the Prestige 5 advert event.
    """

    # Need an active Gallant Leaf deal
    if not state.sponsor_active or state.sponsor_name != "Gallant Leaf Tobacco":
        return

    # Need a current driver
    if not state.player_driver:
        return

    # Only once per save
    if getattr(state, "gallant_driver_promo_done", False):
        return

    # Trigger condition: driver reaches fame 2+
    fame = state.player_driver.get("fame", 0)
    if fame < 2:
        return

    team_name = state.player_constructor or "Your team"
    driver_name = state.player_driver.get("name", "your driver")

    # --- Numbers (simple + readable) ---
    # Base team cut scales a bit with fame so it stays relevant.
    base_team_cut = 120 + fame * 30

    # Options
    option1_cash = base_team_cut                 # standard advert
    option2_cash = int(base_team_cut * 1.25)     # hard bargain
    option3_cash = 0                             # refuse

    # Prestige impacts
    option1_prestige = +0.3
    option2_prestige = -0.2
    option3_prestige = +0.6

    # Sponsor relationship impacts (affects future sponsor payments)
    option2_mult_delta = +0.05
    option3_mult_delta = -0.10

    # Small “time lost to promo” fatigue (long-term health, NOT wear/condition)
    option1_engine_health_hit = 1.5
    option1_chassis_health_hit = 1.0

    print("\n=== Sponsor Request: Driver Promotion ===")
    print("A Gallant Leaf representative approaches your garage.")
    print(f"\"{driver_name} is starting to get noticed. We want them in a promotional campaign.\"")
    print("They’ll pay your team for access to the driver.\n")

    print("Choose your response:")
    print(f"1) Do the promo day")
    print(f"   +£{option1_cash} to the team, prestige {option1_prestige:+.1f}")
    print("   Minor fatigue hit to long-term car health\n")

    print(f"2) Hard bargain for more money")
    print(f"   +£{option2_cash} to the team, prestige {option2_prestige:+.1f}")
    print(f"   Sponsor rate multiplier {option2_mult_delta:+.2f} (future sponsor pay)\n")

    print(f"3) Refuse — keep focus on racing")
    print(f"   +£{option3_cash}, prestige {option3_prestige:+.1f}")
    print(f"   Sponsor rate multiplier {option3_mult_delta:+.2f} (future sponsor pay)\n")

    choice = input("> ").strip()

    # Default to 1 if Enter
    if choice == "" or choice == "1":
        # Money
        state.money += option1_cash
        state.last_week_income += option1_cash
        state.last_week_sponsor_income += option1_cash
        state.constructor_earnings += option1_cash

        # Prestige
        state.prestige = max(0.0, min(100.0, state.prestige + option1_prestige))

        # Fatigue
        state.engine_health = max(0.0, state.engine_health - option1_engine_health_hit)
        state.chassis_health = max(0.0, state.chassis_health - option1_chassis_health_hit)

        state.news.append(
            f"{team_name} agree to a Gallant Leaf promo day featuring {driver_name}, "
            f"earning £{option1_cash}."
        )
        state.news.append(
            f"The long day of media commitments costs the garage focus: "
            f"engine health -{option1_engine_health_hit:.1f}, chassis health -{option1_chassis_health_hit:.1f}."
        )

    elif choice == "2":
        # Money
        state.money += option2_cash
        state.last_week_income += option2_cash
        state.last_week_sponsor_income += option2_cash
        state.constructor_earnings += option2_cash

        # Prestige
        state.prestige = max(0.0, min(100.0, state.prestige + option2_prestige))

        # Sponsor multiplier up
        mult = getattr(state, "sponsor_rate_multiplier", 1.0)
        state.sponsor_rate_multiplier = max(0.5, min(2.0, mult + option2_mult_delta))

        state.news.append(
            f"{team_name} squeeze Gallant Leaf for a better promo fee: £{option2_cash} paid."
        )
        state.news.append(
            f"Paddock whispers you’re ruthless (prestige {option2_prestige:+.1f}). "
            f"Sponsor rate multiplier now {state.sponsor_rate_multiplier:.2f}."
        )

    else:
        # Refuse
        state.prestige = max(0.0, min(100.0, state.prestige + option3_prestige))

        # Sponsor multiplier down
        mult = getattr(state, "sponsor_rate_multiplier", 1.0)
        state.sponsor_rate_multiplier = max(0.5, min(2.0, mult + option3_mult_delta))

        state.news.append(
            f"{team_name} refuse Gallant Leaf’s promo request and keep focus on racing "
            f"(prestige {option3_prestige:+.1f})."
        )
        state.news.append(
            f"Gallant Leaf are unimpressed. Sponsor rate multiplier now {state.sponsor_rate_multiplier:.2f}."
        )

    # Mark event as done
    state.gallant_driver_promo_done = True


def maybe_gallant_leaf_advert(state, time):
    """
    Once you reach Prestige ~5 with Gallant Leaf on board, they
    invite you to star in a cigarette advert.

    One-off cheque + slightly better payments on the existing deal.
    """
    # Need an active Gallant Leaf deal
    if not state.sponsor_active or state.sponsor_name != "Gallant Leaf Tobacco":
        return

    # Only once
    if state.sponsor_bonus_event_done:
        return

    # Only once you're vaguely "somebody" in the paddock
    if state.prestige < 5.0:
        return

    print("\nA familiar Gallant Leaf representative finds you in the paddock hospitality tent.")
    print("\"Your recent form has turned a few heads,\" he says with a smile.")
    print("They'd like you and your car to feature in a cigarette advert campaign.")
    print("In return, they'll sweeten your existing deal:")
    print("  • £800 one-off payment for the advert")
    print("  • Around 25% better appearance / points / podium money going forward.")
    choice = input("\nDo you agree to the advert? (y/n): ").strip().lower()

    state.sponsor_bonus_event_done = True

    if choice != "y":
        print("\nYou politely decline – you didn't get into racing to sell cigarettes.")
        team_name = state.player_constructor or "Your team"
        state.news.append(
            f"{team_name} turn down a more aggressive Gallant Leaf advertising campaign."
        )
        return

    # Pay the advert fee
    advert_fee = 800
    state.money += advert_fee
    state.last_week_income += advert_fee
    state.last_week_sponsor_income += advert_fee
    state.constructor_earnings += advert_fee

    # Sweeten future payments a bit
    state.sponsor_rate_multiplier = 1.25

    team_name = state.player_constructor or "Your team"
    state.news.append(
        f"{team_name} star in a Gallant Leaf advertising campaign, "
        f"pocketing £{advert_fee} and improving the terms of their deal."
    )

    print("\nYou spend a long day posing with the car, a packet of cigarettes,")
    print("and a forced smile. At least the cheque clears.")




def maybe_weather_preparation(state, time):
    """
    Opportunity to prepare for upcoming weather conditions.
    """
    # Check if there's a pending race
    if not hasattr(state, 'pending_race_week') or not state.pending_race_week:
        return

    # 8% chance when there's a pending race (reduced from 15%)
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
# TYRE SPONSORSHIP SYSTEM
# =============================================================================

TYRE_SPONSORS = {
    "Roadmaster Rubber Co.": {
        "flavor": "A budget rubber manufacturer looking to break into motorsport",
        "personality": "methodical_german",
        "min_prestige": 1.0,
        "tyres_per_race": 2,
        "goals": {
            "races_to_complete": 5,
            "min_finish_position": 10,  # Must finish in top 10 at least once
        },
    },
    "Veloce Gomme": {
        "flavor": "The Italian tyre company wants to prove their rubber on the track",
        "personality": "passionate_italian",
        "min_prestige": 3.0,
        "tyres_per_race": 3,
        "goals": {
            "races_to_complete": 4,
            "min_finish_position": 6,  # Must finish in top 6
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
    """
    Offer a tyre sponsorship deal to teams that don't have one.
    Triggered after races, similar to regular sponsors.
    """
    # Already have tyre sponsorship
    if getattr(state, 'tyre_sponsor_active', False):
        return
    
    # Already seen an offer this season
    if getattr(state, 'tyre_sponsor_offer_seen_year', 0) == time.year:
        return
    
    # Need at least one race completed
    races_completed = getattr(state, 'season_races_completed', 0)
    if races_completed < 1:
        return
    
    # Random chance (30% per race after first)
    if random.random() > 0.30:
        return
    
    # Find eligible sponsors based on prestige
    available = []
    for name, info in TYRE_SPONSORS.items():
        if state.prestige >= info["min_prestige"]:
            available.append((name, info))
    
    if not available:
        return
    
    # Pick one randomly (weighted toward lower prestige ones for early game)
    sponsor_name, sponsor_info = random.choice(available)
    
    state.tyre_sponsor_offer_seen_year = time.year
    
    print(f"\n{'='*60}")
    print(f"  🛞 TYRE SPONSORSHIP OFFER")
    print(f"{'='*60}")
    print(f"\nA representative from {sponsor_name} approaches your team.")
    print(f'"{sponsor_info["flavor"]}."')
    print(f"\nThey offer a tyre supply deal for the {time.year} season:")
    print(f"  • {sponsor_info['tyres_per_race']} FREE tyre sets delivered before each race")
    print(f"\nIn exchange, you must complete these goals by season end:")
    
    goals = sponsor_info["goals"]
    print(f"  • Complete at least {goals['races_to_complete']} races")
    if "min_finish_position" in goals:
        print(f"  • Finish in the top {goals['min_finish_position']} at least once")
    if "podiums_required" in goals:
        print(f"  • Achieve {goals['podiums_required']} podium finish{'es' if goals['podiums_required'] > 1 else ''}")
    if "wins_required" in goals:
        print(f"  • Win {goals['wins_required']} race{'s' if goals['wins_required'] > 1 else ''}")
    
    print(f"\n⚠️  WARNING: Failing to meet goals will damage your reputation!")
    
    choice = input("\nAccept the tyre sponsorship? (y/n): ").strip().lower()
    
    if choice == "y":
        state.tyre_sponsor_active = True
        state.tyre_sponsor_name = sponsor_name
        state.tyre_sponsor_year = time.year
        state.tyre_sponsor_tyres_per_race = sponsor_info["tyres_per_race"]
        state.tyre_sponsor_goals = dict(goals)
        
        # Track progress
        state.tyre_sponsor_races_completed = 0
        state.tyre_sponsor_best_finish = 99
        state.tyre_sponsor_podiums = 0
        state.tyre_sponsor_wins = 0
        
        # Give initial tyres
        initial_tyres = sponsor_info["tyres_per_race"] * 2
        state.tyre_sets = getattr(state, 'tyre_sets', 0) + initial_tyres
        
        print(f"\n✅ Deal signed with {sponsor_name}!")
        print(f"   {initial_tyres} tyre sets delivered to your garage immediately.")
        state.news.append(f"TYRE DEAL: {sponsor_name} signs tyre supply agreement with your team!")
    else:
        print(f"\nYou politely decline {sponsor_name}'s offer.")
        state.news.append(f"Your team declines a tyre sponsorship offer from {sponsor_name}.")


def deliver_tyre_sponsor_tyres(state, time, race_name):
    """
    Called before each race to deliver sponsor tyres.
    """
    if not getattr(state, 'tyre_sponsor_active', False):
        return
    
    # Check if still in contract year
    if time.year != getattr(state, 'tyre_sponsor_year', 0):
        return
    
    sponsor_name = getattr(state, 'tyre_sponsor_name', 'Unknown')
    tyres = getattr(state, 'tyre_sponsor_tyres_per_race', 0)
    
    if tyres > 0:
        state.tyre_sets = getattr(state, 'tyre_sets', 0) + tyres
        print(f"\n🛞 {sponsor_name} delivers {tyres} tyre sets for {race_name}.")
        state.news.append(f"TYRES: {sponsor_name} delivers {tyres} sets for {race_name}.")


def update_tyre_sponsor_progress(state, finish_position, is_podium, is_win):
    """
    Called after each race to update tyre sponsor goal progress.
    """
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
    """
    Called at end of season to check if tyre sponsor goals were met.
    """
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
    
    # Check each goal
    goals_met = True
    failed_goals = []
    
    if races_done < goals.get('races_to_complete', 0):
        goals_met = False
        failed_goals.append(f"Only completed {races_done}/{goals['races_to_complete']} races")
    
    if 'min_finish_position' in goals and best_finish > goals['min_finish_position']:
        goals_met = False
        failed_goals.append(f"Best finish was P{best_finish}, needed top {goals['min_finish_position']}")
    
    if 'podiums_required' in goals and podiums < goals['podiums_required']:
        goals_met = False
        failed_goals.append(f"Only {podiums}/{goals['podiums_required']} podiums")
    
    if 'wins_required' in goals and wins < goals['wins_required']:
        goals_met = False
        failed_goals.append(f"Only {wins}/{goals['wins_required']} wins")
    
    print(f"\n{'='*60}")
    print(f"  🛞 TYRE SPONSORSHIP REVIEW — {sponsor_name}")
    print(f"{'='*60}")
    
    if goals_met:
        print(f"\n✅ GOALS MET! {sponsor_name} is pleased with your performance.")
        print(f"   They may offer an improved deal next season.")
        state.news.append(f"TYRE SPONSOR: {sponsor_name} satisfied — goals achieved!")
        
        # Small prestige boost
        state.prestige = min(100.0, state.prestige + 1.0)
        
        # Mark for potential renewal
        state.tyre_sponsor_goals_met = True
    else:
        print(f"\n❌ GOALS NOT MET! {sponsor_name} is disappointed.")
        print(f"   Failed requirements:")
        for fail in failed_goals:
            print(f"     • {fail}")
        
        # Prestige penalty
        penalty = 2.0
        state.prestige = max(0.0, state.prestige - penalty)
        print(f"\n   Your reputation suffers. (Prestige -{penalty:.1f})")
        state.news.append(f"TYRE SPONSOR: {sponsor_name} disappointed — goals missed! Prestige -{penalty:.1f}")
        state.tyre_sponsor_goals_met = False
    
    # Clear active status (contract ended)
    state.tyre_sponsor_active = False


def show_tyre_sponsor_status(state):
    """
    Display current tyre sponsor status and progress.
    """
    if not getattr(state, 'tyre_sponsor_active', False):
        print("\n  No active tyre sponsorship.")
        return
    
    sponsor_name = getattr(state, 'tyre_sponsor_name', 'Unknown')
    goals = getattr(state, 'tyre_sponsor_goals', {})
    
    races_done = getattr(state, 'tyre_sponsor_races_completed', 0)
    best_finish = getattr(state, 'tyre_sponsor_best_finish', 99)
    podiums = getattr(state, 'tyre_sponsor_podiums', 0)
    wins = getattr(state, 'tyre_sponsor_wins', 0)
    
    print(f"\n  🛞 Tyre Sponsor: {sponsor_name}")
    print(f"     Tyres per race: {getattr(state, 'tyre_sponsor_tyres_per_race', 0)} sets")
    print(f"\n     Goal Progress:")
    
    # Races completed
    req_races = goals.get('races_to_complete', 0)
    status = "✅" if races_done >= req_races else "❌"
    print(f"       {status} Races: {races_done}/{req_races}")
    
    # Best finish
    if 'min_finish_position' in goals:
        req_pos = goals['min_finish_position']
        status = "✅" if best_finish <= req_pos else "❌"
        finish_str = f"P{best_finish}" if best_finish < 99 else "N/A"
        print(f"       {status} Best finish: {finish_str} (need top {req_pos})")
    
    # Podiums
    if 'podiums_required' in goals:
        req_pods = goals['podiums_required']
        status = "✅" if podiums >= req_pods else "❌"
        print(f"       {status} Podiums: {podiums}/{req_pods}")
    
    # Wins
    if 'wins_required' in goals:
        req_wins = goals['wins_required']
        status = "✅" if wins >= req_wins else "❌"
        print(f"       {status} Wins: {wins}/{req_wins}")


def maybe_offer_sponsor_renewal(state, time):
    """
    At the start of a new year, if the sponsor contract has expired,
    offer renewal with better terms if goals were met.
    """
    if not state.sponsor_active:
        return

    # Only check when the contract year has passed
    if time.year <= state.sponsor_end_year:
        return

    sponsor_name = state.sponsor_name
    sponsor_info = SPONSOR_TYPES.get(sponsor_name, {})

    # Goals met bonus
    goals_met = state.sponsor_goals_races_started and state.sponsor_goals_podium
    renewal_bonus = 1000 if goals_met else 0

    # Base rate increase
    rate_increase = 0.25 if goals_met else 0.0

    # Sponsor-specific bonuses
    sponsor_bonuses = {
        "Gallant Leaf Tobacco": {"bonus_mult": 1.0, "media_event": "advert_shoot"},
        "Valdieri Wines": {"bonus_mult": 1.2, "media_event": "wine_tasting"},
        "Rossi Tires": {"bonus_mult": 1.1, "media_event": "tire_tech_demo"},
        "Marconi Electronics": {"bonus_mult": 1.3, "media_event": "tech_demo"},
        "Aero Dynamics Ltd": {"bonus_mult": 1.25, "media_event": "press_conference"},
        "Castello Banking": {"bonus_mult": 1.4, "media_event": "press_conference"},
    }

    bonus_info = sponsor_bonuses.get(sponsor_name, {"bonus_mult": 1.0, "media_event": "press_conference"})
    renewal_bonus = int(renewal_bonus * bonus_info["bonus_mult"])

    print(f"\n{state.sponsor_name} contacts you about renewing the sponsorship deal.")
    print(f"Your contract expired at the end of {state.sponsor_end_year}.")

    if goals_met:
        print("Goals completed: ✓ 3 races started, ✓ 1 podium achieved")
        print(f"They offer improved terms: £{renewal_bonus} signing bonus + {rate_increase:.0f}% better payments.")
    else:
        print("Goals not fully completed. They offer standard renewal terms.")

    choice = input("\nRenew the sponsorship? (y/n): ").strip().lower()

    if choice == "y":
        # Extend contract
        state.sponsor_end_year = time.year + 2  # extend for 2 more years
        state.sponsor_start_year = time.year

        # Reset counters for new contract
        state.sponsor_races_started = 0
        state.sponsor_podiums = 0
        state.sponsor_goals_races_started = False
        state.sponsor_goals_podium = False

        # Apply bonuses
        if renewal_bonus > 0:
            state.money += renewal_bonus
            state.last_week_income += renewal_bonus
            state.last_week_sponsor_income += renewal_bonus
            state.constructor_earnings += renewal_bonus

            mult = getattr(state, "sponsor_rate_multiplier", 1.0)
            state.sponsor_rate_multiplier = min(2.0, mult + rate_increase)

        team_name = state.player_constructor or "Your team"
        state.news.append(f"{team_name} renews sponsorship with {state.sponsor_name} through {state.sponsor_end_year}.")
        if renewal_bonus > 0:
            state.news.append(f"Bonus for meeting goals: £{renewal_bonus} + improved payment rates.")

        # Add media coverage for successful renewal
        if goals_met:
            generate_media_event(sponsor_name, bonus_info["media_event"], state, time)

    else:
        # End sponsorship
        state.sponsor_active = False
        state.news.append(f"{state.sponsor_name} sponsorship ends - no renewal agreed.")


def maybe_offer_sponsor(state, time):
    """
    Offer the first sponsor once the team has:
      - Ever completed Vallone GP
      - Reached a minimum prestige
    Only once per save.
    """
    # Already have or already refused this deal
    if state.sponsor_seen_offer or state.sponsor_active:
        return

    # Only offer starting in year 1947
    if time.year < 1947:
        return

    # Require that Vallone GP has been run at least once in the team's history
    if not getattr(state, "ever_completed_vallone", False):
        return

    # Only offer if you've shown *some* promise
    if state.prestige < 2.0:
        return

    # Select sponsor based on team prestige and random chance
    available_sponsors = []

    if state.prestige >= 2.0:
        available_sponsors.append("Gallant Leaf Tobacco")

    if state.prestige >= 3.0:
        available_sponsors.extend(["Valdieri Wines", "Rossi Tires"])

    if state.prestige >= 6.0:
        available_sponsors.extend(["Marconi Electronics", "Aero Dynamics Ltd"])

    if state.prestige >= 9.0:
        available_sponsors.append("Castello Banking")

    if not available_sponsors:
        return

    sponsor_name = random.choice(available_sponsors)
    sponsor_info = SPONSOR_TYPES.get(sponsor_name, {})

    print(f"\nA representative from {sponsor_name} approaches you.")
    print(f"{sponsor_info.get('flavor_text', 'A company interested in motorsport sponsorship')}.")
    print(f"They offer a sponsorship deal through 1949 with:")

    # Base payments scaled by sponsor type
    base_multipliers = {
        "Gallant Leaf Tobacco": {"appearance": 60, "points": 10, "podium": 120, "bonus": 2000},
        "Valdieri Wines": {"appearance": 80, "points": 15, "podium": 150, "bonus": 2500},
        "Rossi Tires": {"appearance": 70, "points": 12, "podium": 130, "bonus": 2200},
        "Marconi Electronics": {"appearance": 90, "points": 18, "podium": 180, "bonus": 3000},
        "Aero Dynamics Ltd": {"appearance": 85, "points": 16, "podium": 160, "bonus": 2800},
        "Castello Banking": {"appearance": 100, "points": 20, "podium": 200, "bonus": 3500},
    }

    multipliers = base_multipliers.get(sponsor_name, {"appearance": 60, "points": 10, "podium": 120, "bonus": 2000})

    print(f"  • £{multipliers['bonus']} signing bonus immediately")
    print(f"  • £{multipliers['appearance']} appearance payment per race started")
    print(f"  • £{multipliers['points']} per championship point")
    print(f"  • £{multipliers['podium']} per podium")
    print("Goals:")
    print("  • Start at least 3 races")
    print("  • Achieve at least 1 podium by end of 1949")

    choice = input("\nDo you accept the sponsorship? (y/n): ").strip().lower()

    state.sponsor_seen_offer = True

    if choice == "y":
        state.sponsor_active = True
        state.sponsor_name = sponsor_name
        state.sponsor_start_year = time.year
        state.sponsor_end_year = 1949
        signing_bonus = multipliers['bonus']
        state.money += signing_bonus
        state.last_week_income += signing_bonus
        state.last_week_sponsor_income += signing_bonus
        state.news.append(f"{sponsor_name} signs with your team! £{signing_bonus} paid upfront.")

        # Add media coverage for the signing
        generate_media_event(sponsor_name, "press_conference", state, time)

        state.constructor_earnings += signing_bonus
    else:
        # You turn them down – small respect boost
        before = state.prestige
        state.prestige = min(100.0, state.prestige + 0.5)
        team_name = state.player_constructor or "Your team"
        state.news.append(
            f"{team_name} decline a sponsorship from {sponsor_name} "
            f"(prestige {before:.1f} → {state.prestige:.1f})."
        )
