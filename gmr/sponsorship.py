# gmr/sponsorship.py
# Sponsorship system for drivers


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

    # Goals met bonus
    goals_met = state.sponsor_goals_races_started and state.sponsor_goals_podium
    renewal_bonus = 1000 if goals_met else 0
    rate_increase = 0.25 if goals_met else 0.0

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

    print("\nA representative from Gallant Leaf Tobacco approaches you.")
    print("They're a small but ambitious brand looking to break into racing.")
    print("They offer a sponsorship deal through 1949 with:")
    print("  • £2000 signing bonus immediately")
    print("  • £60 appearance payment per race started")
    print("  • £10 per championship point")
    print("  • £120 per podium")
    print("Goals:")
    print("  • Start at least 3 races")
    print("  • Achieve at least 1 podium by end of 1949")

    choice = input("\nDo you accept the sponsorship? (y/n): ").strip().lower()

    state.sponsor_seen_offer = True

    if choice == "y":
        state.sponsor_active = True
        state.sponsor_name = "Gallant Leaf Tobacco"
        state.sponsor_start_year = time.year
        state.sponsor_end_year = 1949
        signing_bonus = 2000
        state.money += signing_bonus
        state.last_week_income += signing_bonus
        state.last_week_sponsor_income += signing_bonus
        state.news.append(f"Gallant Leaf Tobacco signs with your team! £{signing_bonus} paid upfront.")
        state.constructor_earnings += signing_bonus
    else:
        # You turn them down – small respect boost
        before = state.prestige
        state.prestige = min(100.0, state.prestige + 0.5)
        team_name = state.player_constructor or "Your team"
        state.news.append(
            f"{team_name} decline a tobacco sponsorship from Gallant Leaf "
            f"(prestige {before:.1f} → {state.prestige:.1f})."
        )
