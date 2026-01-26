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

    # 15% chance per week for a media event
    if random.random() > 0.15:
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


def maybe_driver_interview(state, time):
    """
    Random media interview opportunity for the driver.
    Can result in bonuses or penalties based on response.
    """
    if not state.player_driver:
        return

    # 12% chance per week
    if random.random() > 0.12:
        return

    driver_name = state.player_driver.get("name", "your driver")
    team_name = state.player_constructor or "Your team"

    # Different interview types
    interview_types = [
        {
            "scenario": "racing philosophy",
            "question": f"A journalist asks {driver_name} about their approach to racing.",
            "options": [
                ("Passionate response about the thrill of speed", "prestige", 0.3, "positive"),
                ("Technical answer about car setup", "mechanic_skill", 1, "neutral"),
                ("Controversial comment about rival drivers", "prestige", -0.4, "negative"),
            ]
        },
        {
            "scenario": "future plans",
            "question": f"Press inquire about {driver_name}'s career ambitions.",
            "options": [
                ("Express loyalty to the team", "team_morale", 2, "positive"),
                ("Mention interest in bigger opportunities", "prestige", -0.2, "negative"),
                ("Focus on championship goals", "driver_xp", 1, "neutral"),
            ]
        },
        {
            "scenario": "recent performance",
            "question": f"Journalists question {driver_name} about their recent form.",
            "options": [
                ("Take responsibility for mistakes", "driver_xp", 1, "positive"),
                ("Blame team or car issues", "team_morale", -1, "negative"),
                ("Stay diplomatic and focused", "prestige", 0.2, "neutral"),
            ]
        },
        {
            "scenario": "personal life",
            "question": f"A reporter asks about {driver_name}'s life outside racing.",
            "options": [
                ("Share inspiring personal story", "fame", 1, "positive"),
                ("Keep it private and professional", "prestige", 0.1, "neutral"),
                ("Make inappropriate comments", "prestige", -0.5, "negative"),
            ]
        }
    ]

    interview = random.choice(interview_types)

    print(f"\n=== Media Interview: {interview['scenario'].title()} ===")
    print(f"{interview['question']}")
    print(f"{driver_name} looks to you for guidance on how to respond.\n")

    for i, (response, _, _, _) in enumerate(interview['options'], 1):
        print(f"{i}) {response}")

    choice = input("\nHow should they respond? (1-3): ").strip()

    # Default to neutral response if invalid input
    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(interview['options']):
            choice_idx = 1  # Default to middle option
    except ValueError:
        choice_idx = 1

    response_text, stat_type, stat_value, tone = interview['options'][choice_idx]

    # Apply effects
    if stat_type == "prestige":
        old_prestige = state.prestige
        state.prestige = max(0.0, min(100.0, state.prestige + stat_value))
        prestige_change = state.prestige - old_prestige
    elif stat_type == "mechanic_skill":
        # Temporary mechanic skill bonus for next race
        if not hasattr(state, 'temp_mechanic_bonus'):
            state.temp_mechanic_bonus = 0
        state.temp_mechanic_bonus += stat_value
    elif stat_type == "team_morale":
        # Affect effective mechanic skill
        benefits = getattr(state, 'garage_benefits', {})
        current_bonus = benefits.get('mechanic_skill_bonus', 0)
        # Temporary morale effect
        if not hasattr(state, 'temp_morale_bonus'):
            state.temp_morale_bonus = 0
        state.temp_morale_bonus += stat_value
    elif stat_type == "driver_xp":
        # Give driver XP
        if hasattr(state.player_driver, 'xp'):
            state.player_driver['xp'] = state.player_driver.get('xp', 0) + stat_value
    elif stat_type == "fame":
        # Increase driver fame
        state.player_driver['fame'] = state.player_driver.get('fame', 0) + stat_value

    # Generate news based on response
    if tone == "positive":
        state.news.append(f"INTERVIEW: {driver_name} impresses journalists with thoughtful responses, boosting team image.")
    elif tone == "negative":
        state.news.append(f"CONTROVERSY: {driver_name}'s comments spark media debate and concern in the paddock.")
    else:
        state.news.append(f"MEDIA: {driver_name} gives measured responses in recent interview.")

    # Add specific stat change to news if applicable
    if stat_type == "prestige" and abs(stat_value) > 0:
        state.news.append(f"Team prestige {stat_value:+.1f} following the interview.")


def maybe_technical_inspection(state, time):
    """
    FIA-style technical inspection that can find issues or give clean bills of health.
    Only available after governing body is created (post-demo).
    """
    # Only available after demo completion (governing body created)
    if not getattr(state, "demo_complete", False):
        return

    # 10% chance per week
    if random.random() > 0.10:
        return

    team_name = state.player_constructor or "Your team"

    print("\n=== Technical Inspection ===")
    print("FIA technical inspectors are conducting a thorough examination of your car.")
    print("This is a routine check, but they're being particularly meticulous today.\n")

    # Roll for inspection result
    inspection_roll = random.random()

    if inspection_roll < 0.05:  # 5% - Major issues found
        print("CRITICAL FINDINGS: The inspectors have discovered several serious irregularities!")
        print("Your car fails the technical inspection and must be rebuilt.")

        # Major penalties
        state.engine_health = max(0.0, state.engine_health - 15.0)
        state.chassis_health = max(0.0, state.chassis_health - 15.0)
        state.prestige = max(0.0, state.prestige - 1.0)

        state.news.append(f"TECHNICAL DISASTER: {team_name} fails FIA inspection - car must be extensively rebuilt!")
        state.news.append("Major penalties to engine and chassis health, plus prestige hit.")

    elif inspection_roll < 0.20:  # 15% - Minor issues
        print("MINOR ISSUES: Some components are found to be outside tolerances.")
        print("You'll need to make adjustments before the next race.")

        # Minor penalties
        state.engine_health = max(0.0, state.engine_health - 5.0)
        state.chassis_health = max(0.0, state.chassis_health - 5.0)

        state.news.append(f"TECHNICAL ISSUES: {team_name} given warnings in FIA inspection - minor adjustments required.")

    elif inspection_roll < 0.80:  # 60% - Clean bill of health
        print("ALL CLEAR: Your car passes inspection with flying colors!")
        print("The inspectors commend your team's attention to detail.")

        # Small bonus
        state.prestige = min(100.0, state.prestige + 0.3)

        state.news.append(f"TECHNICAL EXCELLENCE: {team_name} receives clean bill of health from FIA inspectors.")

    else:  # 20% - Exceptional performance
        print("OUTSTANDING: The inspectors are impressed by your innovative design solutions!")
        print("You've set a new standard for technical excellence.")

        # Significant bonuses
        state.prestige = min(100.0, state.prestige + 0.8)
        # Temporary performance boost
        if not hasattr(state, 'temp_performance_bonus'):
            state.temp_performance_bonus = 0
        state.temp_performance_bonus += 0.5  # 0.5 speed bonus

        state.news.append(f"TECHNICAL BREAKTHROUGH: {team_name} impresses FIA inspectors with innovative design!")
        state.news.append("Significant prestige boost and temporary performance advantage.")


def maybe_weather_preparation(state, time):
    """
    Opportunity to prepare for upcoming weather conditions.
    """
    # Check if there's a pending race
    if not hasattr(state, 'pending_race_week') or not state.pending_race_week:
        return

    # 15% chance when there's a pending race
    if random.random() > 0.15:
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


def maybe_fan_interaction(state, time):
    """
    Random fan interactions that can boost morale or cause issues.
    """
    # 8% chance per week
    if random.random() > 0.08:
        return

    team_name = state.player_constructor or "Your team"
    driver_name = state.player_driver.get("name", "your driver") if state.player_driver else "your driver"

    fan_scenarios = [
        {
            "scenario": "enthusiastic fan",
            "description": f"An enthusiastic fan recognizes {driver_name} in town and wants an autograph.",
            "options": [
                ("Sign autograph and chat briefly", "morale", 1, "positive"),
                ("Politely decline - need to focus", "prestige", 0.1, "neutral"),
                ("Ignore and walk away", "prestige", -0.3, "negative"),
            ]
        },
        {
            "scenario": "fan club visit",
            "description": f"A local fan club invites {driver_name} to speak at their meeting.",
            "options": [
                ("Accept and give inspiring speech", "fame", 1, "positive"),
                ("Send a team representative instead", "prestige", 0.2, "neutral"),
                ("Decline - too busy with racing", "prestige", -0.2, "negative"),
            ]
        },
        {
            "scenario": "controversial fan",
            "description": f"A fan approaches with controversial opinions about {team_name}'s recent performance.",
            "options": [
                ("Engage respectfully and explain", "driver_xp", 1, "positive"),
                ("Stay diplomatic but firm", "prestige", 0.1, "neutral"),
                ("Get defensive and argumentative", "prestige", -0.4, "negative"),
            ]
        },
        {
            "scenario": "young aspiring driver",
            "description": f"A young aspiring driver seeks advice from {driver_name}.",
            "options": [
                ("Give encouraging mentorship", "fame", 1, "positive"),
                ("Share technical racing tips", "mechanic_skill", 1, "neutral"),
                ("Dismiss them as unrealistic", "prestige", -0.2, "negative"),
            ]
        }
    ]

    scenario = random.choice(fan_scenarios)

    print(f"\n=== Fan Interaction: {scenario['scenario'].title()} ===")
    print(scenario['description'])
    print("How should you handle this situation?\n")

    for i, (response, _, _, _) in enumerate(scenario['options'], 1):
        print(f"{i}) {response}")

    choice = input("\nYour response? (1-3): ").strip()

    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(scenario['options']):
            choice_idx = 1  # Default to middle option
    except ValueError:
        choice_idx = 1

    response_text, stat_type, stat_value, tone = scenario['options'][choice_idx]

    # Apply effects
    if stat_type == "morale":
        if not hasattr(state, 'temp_morale_bonus'):
            state.temp_morale_bonus = 0
        state.temp_morale_bonus += stat_value
    elif stat_type == "prestige":
        state.prestige = max(0.0, min(100.0, state.prestige + stat_value))
    elif stat_type == "fame" and state.player_driver:
        state.player_driver['fame'] = state.player_driver.get('fame', 0) + stat_value
    elif stat_type == "driver_xp" and state.player_driver:
        if hasattr(state.player_driver, 'xp'):
            state.player_driver['xp'] = state.player_driver.get('xp', 0) + stat_value
    elif stat_type == "mechanic_skill":
        if not hasattr(state, 'temp_mechanic_bonus'):
            state.temp_mechanic_bonus = 0
        state.temp_mechanic_bonus += stat_value

    # Generate appropriate news
    if tone == "positive":
        state.news.append(f"FAN INTERACTION: Positive encounter boosts {team_name}'s public image.")
    elif tone == "negative":
        state.news.append(f"FAN INCIDENT: Unfortunate interaction creates negative publicity for {team_name}.")
    else:
        state.news.append(f"PUBLIC RELATIONS: {team_name} handles fan interaction professionally.")


def maybe_supplier_issue(state, time):
    """
    Random supplier problems that can affect car performance.
    """
    # 6% chance per week
    if random.random() > 0.06:
        return

    team_name = state.player_constructor or "Your team"

    supplier_issues = [
        {
            "issue": "engine parts delay",
            "description": "Your engine supplier has delayed delivery of crucial components.",
            "options": [
                ("Pay premium for express delivery", "money", -200, "engine", -3.0),
                ("Use backup supplier (lower quality)", "engine", -5.0, "cost", -50),
                ("Wait and use what you have", "engine", -8.0, "no_cost"),
            ]
        },
        {
            "issue": "chassis parts quality",
            "description": "Quality control issues discovered in your chassis supplier's latest batch.",
            "options": [
                ("Reject batch and pay for replacements", "money", -150, "chassis", -2.0),
                ("Accept with minor modifications", "chassis", -4.0, "mechanic_skill", 1),
                ("Use as-is and hope for best", "chassis", -6.0, "risk"),
            ]
        },
        {
            "issue": "fuel mixture problem",
            "description": "Your fuel supplier reports inconsistencies in the mixture.",
            "options": [
                ("Switch to premium fuel supplier", "money", -100, "performance", 0.3),
                ("Adjust engine mapping to compensate", "mechanic_skill", 1, "engine", -1.0),
                ("Race with current fuel", "performance", -0.5, "unreliable"),
            ]
        }
    ]

    issue = random.choice(supplier_issues)

    print(f"\n=== Supplier Issue: {issue['issue'].title()} ===")
    print(issue['description'])
    print("How do you want to handle this?\n")

    for i, option in enumerate(issue['options'], 1):
        desc = option[0]
        effects = []
        for j in range(1, len(option), 2):
            stat = option[j]
            value = option[j+1]
            if stat == "money":
                effects.append(f"£{value}")
            elif stat in ["engine", "chassis"]:
                effects.append(f"{stat} health {value:+.1f}")
            elif stat == "performance":
                effects.append(f"car speed {value:+.1f}")
            elif stat == "mechanic_skill":
                effects.append(f"mechanic skill +{value}")
            elif stat == "cost":
                effects.append(f"£{value} saved")
            else:
                effects.append(f"{stat}: {value}")

        print(f"{i}) {desc}")
        print(f"   Effects: {', '.join(effects)}\n")

    choice = input("Your decision? (1-3): ").strip()

    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(issue['options']):
            choice_idx = 0  # Default to first option
    except ValueError:
        choice_idx = 0

    option = issue['options'][choice_idx]

    # Apply effects
    for j in range(1, len(option), 2):
        stat = option[j]
        value = option[j+1]

        if stat == "money":
            state.money += value  # value is negative, so this subtracts
            state.last_week_outgoings += abs(value)
        elif stat == "engine":
            state.engine_health = max(0.0, state.engine_health + value)
        elif stat == "chassis":
            state.chassis_health = max(0.0, state.chassis_health + value)
        elif stat == "performance":
            if not hasattr(state, 'temp_performance_bonus'):
                state.temp_performance_bonus = 0
            state.temp_performance_bonus += value
        elif stat == "mechanic_skill":
            if not hasattr(state, 'temp_mechanic_bonus'):
                state.temp_mechanic_bonus = 0
            state.temp_mechanic_bonus += value

    state.news.append(f"SUPPLIER ISSUE: {team_name} deals with {issue['issue']} - {option[0].lower()}.")


def maybe_rival_interaction(state, time):
    """
    Random interactions with rival teams that can create opportunities or conflicts.
    """
    # 7% chance per week
    if random.random() > 0.07:
        return

    team_name = state.player_constructor or "Your team"

    rival_scenarios = [
        {
            "scenario": "technical collaboration",
            "description": "A rival team approaches you about sharing technical data on a common problem.",
            "options": [
                ("Share information openly", "prestige", 0.5, "tech_bonus", 0.3),
                ("Share but request payment", "money", 100, "tech_bonus", 0.2),
                ("Decline - keep secrets", "prestige", -0.2),
            ]
        },
        {
            "scenario": "paddock incident",
            "description": "A heated argument breaks out in the paddock between your team and a rival.",
            "options": [
                ("Defuse situation diplomatically", "prestige", 0.3),
                ("Stand your ground firmly", "prestige", -0.1),
                ("Escalate the confrontation", "prestige", -0.8),
            ]
        },
        {
            "scenario": "driver market rumor",
            "description": "Rumors circulate that a rival team is interested in poaching your driver.",
            "options": [
                ("Offer driver better contract", "money", -50, "loyalty", 1),
                ("Ignore rumors and focus on racing", "prestige", 0.1),
                ("Publicly criticize rival team", "prestige", -0.4),
            ]
        }
    ]

    scenario = random.choice(rival_scenarios)

    print(f"\n=== Rival Team Interaction: {scenario['scenario'].title()} ===")
    print(scenario['description'])
    print("How should your team respond?\n")

    for i, option in enumerate(scenario['options'], 1):
        desc = option[0]
        effects = []
        for j in range(1, len(option), 2):
            stat = option[j]
            value = option[j+1]
            if stat == "money":
                effects.append(f"£{value}")
            elif stat == "prestige":
                effects.append(f"prestige {value:+.1f}")
            elif stat == "tech_bonus":
                effects.append(f"performance +{value}")
            elif stat == "loyalty":
                effects.append(f"driver loyalty +{value}")
            else:
                effects.append(f"{stat}")

        print(f"{i}) {desc}")
        print(f"   Effects: {', '.join(effects)}\n")

    choice = input("Your response? (1-3): ").strip()

    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(scenario['options']):
            choice_idx = 1  # Default to middle option
    except ValueError:
        choice_idx = 1

    option = scenario['options'][choice_idx]

    # Apply effects
    for j in range(1, len(option), 2):
        stat = option[j]
        value = option[j+1]

        if stat == "money":
            state.money += value
            if value < 0:
                state.last_week_outgoings += abs(value)
            else:
                state.last_week_income += value
        elif stat == "prestige":
            state.prestige = max(0.0, min(100.0, state.prestige + value))
        elif stat == "tech_bonus":
            if not hasattr(state, 'temp_performance_bonus'):
                state.temp_performance_bonus = 0
            state.temp_performance_bonus += value
        elif stat == "loyalty" and state.player_driver:
            # Increase driver loyalty/fame
            state.player_driver['fame'] = state.player_driver.get('fame', 0) + value

    # Generate news
    state.news.append(f"RIVAL INTERACTION: {team_name} {option[0].lower()} in {scenario['scenario']} situation.")


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
