#main.py
import random
from gmr.data import (
    constructors,
    drivers,
    tracks,
    engines,
    chassis_list,
)

from gmr.careers import reset_driver_pool, init_driver_careers
from gmr.constants import MONTHS, TEST_DRIVERS_ENABLED, DEBUG_MODE, PAUSE_ON_CRASH
from gmr.core_time import GameTime, get_season_week
from gmr.core_state import GameState
from gmr.careers import (
    init_driver_careers,
    spawn_new_rookies,
    warn_if_contract_last_race,
    apply_offseason_ageing_and_retirement,
    offseason_fame_decay,
    maybe_expand_enzoni_to_three_cars,
    maybe_refill_valdieri_drivers,

)
from gmr.sponsorship import maybe_offer_sponsor, maybe_gallant_leaf_advert
from gmr.world_logic import maybe_add_weekly_rumour, calculate_car_speed, maybe_spawn_scuderia_valdieri
from gmr.calendar import show_calendar
from gmr.ui_finances import show_finances
from gmr.ui_garage import (
    show_garage,
    show_engine_shop,
    show_chassis_shop,
    manage_chassis_development,
    handle_repairs,
    handle_test_day,
    can_book_test_day,
    rename_car,
)
from gmr.careers import show_driver_market
from gmr.race_day import handle_race_week
from gmr.story import inject_demo_prologue, handle_bankruptcy_rescue
from gmr.ui_business import show_business
from gmr.ui_business import can_do_pr_trip
from gmr.calendar import generate_calendar_for_year
from gmr.core_state import ensure_state_fields

def normalise_country_name(raw: str) -> str:
    """
    Takes whatever the player typed and turns it into a consistent label.
    Keep it simple for now: UK/England/Great Britain -> UK, etc.
    """
    s = (raw or "").strip().lower()

    aliases = {
        "uk": "UK",
        "u.k.": "UK",
        "united kingdom": "UK",
        "great britain": "UK",
        "britain": "UK",
        "england": "UK",
        "scotland": "UK",
        "wales": "UK",
        "northern ireland": "UK",

        "usa": "USA",
        "u.s.a.": "USA",
        "us": "USA",
        "u.s.": "USA",
        "united states": "USA",
        "united states of america": "USA",

        "france": "France",
        "italy": "Italy",
        "germany": "Germany",
        "belgium": "Belgium",
        "spain": "Spain",
        "netherlands": "Netherlands",
        "switzerland": "Switzerland",
        "austria": "Austria",
        "sweden": "Sweden",
    }

    # If we know the alias, return it
    if s in aliases:
        return aliases[s]

    # Otherwise, return a "Title Case" version so it's at least clean
    return raw.strip().title()


def setup_player(state):
    print("\nYour father passed away, leaving you his old racing chassis and a worn Level 1 engine.")
    print("You inherit a small shed for a garage and a single mechanic.")
    print("This is the start of your racing adventure.\n")

    state.player_constructor = input("Enter the name of your racing company: ")
    while True:
        country = input("What country is your team based in? ").strip()
        if country:
            state.country = normalise_country_name(country)
            break
        print("Please enter a country name.")


    state.garage.level = 0
    state.garage.base_cost = 25
    state.garage.staff_count = 1
    state.garage.staff_salary = 10

def run_game():
    global race_calendar
    global TEST_DRIVERS_ENABLED
    reset_driver_pool()
    init_driver_careers()
    time = GameTime()
    state = GameState()
    setup_player(state)

    # Initialise driver career fields (age, peak, decline, XP, etc.)
    init_driver_careers()

    state.reset_championship()

    # Demo opening story
    inject_demo_prologue(state, time)

    # 🔹 INITIAL calendar for the starting year
    race_calendar = generate_calendar_for_year(time.year)



    while True:
        # -------- NEWS --------
        if state.news:
            print("\n=== News ===")
            for item in state.news:
                print(item)
            print("----------------")
            state.news.clear()


        # If we've moved into a new year, clear last season's data
        if state.podiums_year < time.year:
            apply_offseason_ageing_and_retirement(state, time)
            offseason_fame_decay(time)

            # Clear last season
            state.podiums.clear()
            state.completed_races.clear()
            state.podiums_year = time.year
            state.reset_championship()

            # New blood first (so hiring pool exists)
            spawn_new_rookies(state, time)

            # Works-team offseason updates
            maybe_expand_enzoni_to_three_cars(state, time)
            maybe_refill_valdieri_drivers(state, time)

            from gmr.world_logic import apply_ai_works_chassis_development
            apply_ai_works_chassis_development(state, time)

            # New calendar for the new year
            race_calendar = generate_calendar_for_year(time.year)

            


        # Work out which week of the 'season' we're in (1..WEEKS_PER_YEAR)
        season_week = get_season_week(time)


        maybe_spawn_scuderia_valdieri(state, time, season_week, race_calendar)


        # Warn if this is the final race on the current driver contract
        if season_week in race_calendar:
            warn_if_contract_last_race(state)


        

        # If we're on a race week and it hasn't been run yet, mark it as pending.
        if season_week in race_calendar and season_week not in state.completed_races:
            if state.pending_race_week is None:
                state.pending_race_week = season_week



        # Sponsorship checks (offer if conditions met)
        maybe_offer_sponsor(state, time)
        maybe_gallant_leaf_advert(state, time)


        # -------- MAIN MENU --------
        season_week = get_season_week(time)

        print(f"\n--- Week {time.week}, {MONTHS[time.month]} {time.year} ---")
        print(f"Money: £{state.money}")

        # Race status for this week
        if season_week in race_calendar:
            race_name = race_calendar[season_week]

            if season_week in state.completed_races:
                print(f"(Completed race week: {race_name})")
            elif state.pending_race_week == season_week:
                print(f"(Race weekend in progress: {race_name})")
            else:
                print(f"(Race this week: {race_name})")
        else:
            print("(No major race scheduled this week)")

        # Hints about what actions are available this week
        if can_book_test_day(state, time):
            print("  Note: Test day available – Garage (4) → Book Test Day (5).")

        if can_do_pr_trip(state, time):
            print("  Note: Sponsor PR trip available – Business (6) → PR/networking trip.")

        print("\n1. Calendar")
        print("2. Season Results")
        print("3. Finances")
        print("4. Garage")
        print("5. Driver Market")
        print("6. Business & Contracts")

        # Patch F: debug toggle for Test drivers
        test_label = "ON" if TEST_DRIVERS_ENABLED else "OFF"
        print(f"8. Toggle Test Drivers (debug) [{test_label}]")


        if state.pending_race_week is None:
            # Normal case: no race locked in yet, you can advance time
            print("7. Advance Week")
        else:
            # Race is waiting this week; you *must* run the weekend before time can move on
            race_name = race_calendar[state.pending_race_week]
            print(f"7. Enter race weekend ({race_name})")

        choice = input("> ").strip()


        if choice == "1":
            show_calendar(state, time, race_calendar)


        elif choice == "2":
            print("\n=== Season Results (No Official Championship Yet) ===")
            if state.podiums:
                for week in sorted(state.podiums.keys()):
                    race_name = race_calendar.get(week, "Unknown Race")
                    podium = state.podiums.get(week)
                    if podium:
                        winner_name, winner_ctor = podium[0]
                        print(f"{race_name}: winner – {winner_name} ({winner_ctor})")
            else:
                print("No races have been completed this season yet.")



        elif choice == "3":
            show_finances(state)

        elif choice == "4":
            # Garage menu
            while True:
                print("\n=== Garage Menu ===")

                # Hint about testing availability
                if can_book_test_day(state, time):
                    print("   (Private test day available – option 5)")
                else:
                    weeks_since = time.absolute_week - state.last_test_abs_week
                    weeks_until = max(0, 8 - weeks_since)
                    print(f"   (Next private test window in about {weeks_until} week(s))")

                print("1. View Garage Info")
                print("2. Racecar Parts")
                print("3. Chassis Development Program")
                print("4. Repairs & Maintenance")
                print("5. Book a Test Day")
                print("6. Name / rename car")
                print("7. Back to Main Menu")

                sub_choice = input("> ").strip()

                if sub_choice == "1":
                    show_garage(state)
                elif sub_choice == "2":
                    # Car Parts submenu
                    while True:
                        print("\n=== Racecar Parts ===")
                        print("1. Engines")
                        print("2. Chassis")
                        print("3. Back to Garage Menu")

                        parts_choice = input("> ").strip()

                        if parts_choice == "1":
                            show_engine_shop(state)
                        elif parts_choice == "2":
                            show_chassis_shop(state)
                        elif parts_choice == "3":
                            break
                        else:
                            print("Invalid choice.")
                elif sub_choice == "3":
                    manage_chassis_development(state)
                elif sub_choice == "4":
                    handle_repairs(state)
                elif sub_choice == "5":
                    handle_test_day(state, time)
                elif sub_choice == "6":
                    rename_car(state)      # 👈 new option
                elif sub_choice == "7":
                    break
                else:
                    print("Invalid choice.")


        elif choice == "5":
            show_driver_market(state)

        elif choice == "6":
            # NEW: Business & Contracts screen
            show_business(state, time)

        elif choice == "8":
            # Patch F: toggle Test drivers (debug)            
            TEST_DRIVERS_ENABLED = not TEST_DRIVERS_ENABLED

            if TEST_DRIVERS_ENABLED:
                state.news.append("DEBUG: Test drivers ENABLED (they will enter events).")
            else:
                state.news.append("DEBUG: Test drivers DISABLED (kept out of real events).")


        elif choice == "7":
            # Advance time OR, if we're already locked into a race weekend, run the race
            if state.pending_race_week is None:
                # ---- Normal: advance the calendar ----
                ensure_state_fields(state)

                # New week: clear last week's income & one-off tracking
                state.last_week_income = 0
                state.last_week_prize_income = 0
                state.last_week_sponsor_income = 0
                state.last_week_appearance_income = 0

                state.last_week_purchases = 0
                state.last_week_driver_pay = 0
                state.last_week_rnd = 0
                state.last_week_loan_interest = 0

                state.last_week_travel_cost = 0
                state.last_week_outgoings = 0


                # Base running costs (garage + staff)
                staff_cost = state.garage.staff_count * state.garage.staff_salary
                base_outgoings = state.garage.base_cost + staff_cost

                # Pay base running costs
                state.money -= base_outgoings




                # ------------------------------
                # Chassis development program (SLOTS)
                # ------------------------------
                if state.chassis_project_active and state.current_chassis:
                    ch = state.current_chassis

                    # Ensure slot fields exist (safe for old saves)
                    if "dev_slots" not in ch:
                        ch["dev_slots"] = 1
                    if "dev_runs_done" not in ch:
                        ch["dev_runs_done"] = 0

                    # If this chassis has no slots left, stop the project
                    if ch["dev_runs_done"] >= ch["dev_slots"]:
                        state.chassis_project_active = False
                        state.chassis_progress = 0.0
                        state.chassis_project_chassis_id = None
                    else:
                        # Tie progress to a specific chassis; reset if you changed chassis
                        if state.chassis_project_chassis_id is None:
                            state.chassis_project_chassis_id = ch["id"]
                        elif ch["id"] != state.chassis_project_chassis_id:
                            # Swapped to a different chassis: lose old progress, start fresh
                            state.chassis_project_chassis_id = ch["id"]
                            state.chassis_progress = 0.0

                        dev_weekly_cost = 20  # extra money spent on experiments/materials
                        state.money -= dev_weekly_cost
                        state.last_week_rnd += dev_weekly_cost

                        # Progress increases each week based on mechanic skill, with randomness.
                        weekly_gain = random.uniform(0.3, 1.0) * state.garage.mechanic_skill * 2.0
                        state.chassis_progress += weekly_gain

                        # Enough progress for a breakthrough?
                        if state.chassis_progress >= 100.0:
                            insight = getattr(state, "chassis_insight", 0.0)  # 0–12 in this demo
                            mech = state.garage.mechanic_skill               # 1–10-ish

                            # ------------------------------
                            # Decide what kind of development this is
                            # ------------------------------
                            # Most work improves aero, sometimes suspension, rarely weight
                            stat_roll = random.random()
                            if stat_roll < 0.70:
                                stat_target = "aero"
                            elif stat_roll < 0.92:
                                stat_target = "suspension"
                            else:
                                stat_target = "weight"


                            # ------------------------------
                            # Works-constructor dev bonus
                            # ------------------------------
                            supplier = ch.get("supplier", "")

                            # Normalise supplier names to constructor keys
                            supplier_key = supplier
                            if supplier == "Enzoni Works":
                                supplier_key = "Enzoni"
                            elif supplier == "Scuderia Valdieri":
                                supplier_key = "Scuderia Valdieri"

                            dev_bonus = 0.0
                            if supplier_key in constructors:
                                dev_bonus = constructors[supplier_key].get("dev_bonus", 0.0)

                            # ------------------------------
                            # Final development quality
                            # ------------------------------
                            quality = (insight / 12.0) + (mech / 12.0) + dev_bonus
                            quality = max(0.0, min(quality, 1.4))

                            # Base chances before quality:
                            #   25% disaster, 55% small gain, 20% big gain
                            base_bad = 0.25
                            base_big = 0.20

                            # More quality = fewer disasters, more big breakthroughs
                            bad_chance = max(0.05, base_bad - 0.15 * quality)
                            big_chance = min(0.35, base_big + 0.15 * quality)
                            small_chance = 1.0 - bad_chance - big_chance

                            roll = random.random()
                            if roll < bad_chance:
                                # ---- BAD OUTCOME ----
                                if stat_target == "aero":
                                    ch["aero"] = max(1, ch.get("aero", 1) - 1)
                                    outcome = "A development misstep harms airflow (-1 aero)."

                                elif stat_target == "suspension":
                                    ch["suspension"] = max(1, ch.get("suspension", 3) - 1)
                                    outcome = "A development misstep ruins the suspension geometry (-1 suspension)."

                                else:  # weight
                                    # Weight going UP is bad (heavier)
                                    ch["weight"] = min(10, ch.get("weight", 7) + 1)
                                    outcome = "A redesign adds unwanted bracing (+1 weight)."

                            elif roll < bad_chance + small_chance:
                                # ---- SMALL GAIN ----
                                if stat_target == "aero":
                                    ch["aero"] = ch.get("aero", 1) + 1
                                    outcome = "Your mechanics find modest aerodynamic gains (+1 aero)."

                                elif stat_target == "suspension":
                                    ch["suspension"] = ch.get("suspension", 3) + 1
                                    outcome = "Small handling gains from suspension refinement (+1 suspension)."

                                else:  # weight
                                    ch["weight"] = max(3, ch.get("weight", 7) - 1)
                                    outcome = "Weight trimmed from the frame (-1 weight)."

                            else:
                                # ---- BIG GAIN ----
                                if stat_target == "aero":
                                    delta = 2
                                    if quality > 1.1 and random.random() < 0.25:
                                        delta = 3
                                    ch["aero"] = ch.get("aero", 1) + delta
                                    outcome = f"Major aerodynamic breakthrough on your chassis (+{delta} aero)."

                                elif stat_target == "suspension":
                                    delta = 2
                                    if quality > 1.1 and random.random() < 0.20:
                                        delta = 3
                                    ch["suspension"] = ch.get("suspension", 3) + delta
                                    outcome = f"Major suspension breakthrough (+{delta} suspension)."

                                else:  # weight (big gain = bigger reduction)
                                    delta = 1
                                    if quality > 1.1 and random.random() < 0.25:
                                        delta = 2
                                    ch["weight"] = max(3, ch.get("weight", 7) - delta)
                                    outcome = f"A big weight-saving redesign (-{delta} weight)."

                            # ---- Clamp stats ----
                            ch["aero"] = max(1, min(ch.get("aero", 1), 12))
                            ch["suspension"] = max(1, min(ch.get("suspension", 3), 10))
                            ch["weight"] = max(3, min(ch.get("weight", 7), 10))


                            # Recalculate car speed
                            if state.current_engine and state.current_chassis:
                                state.car_speed = calculate_car_speed(state.current_engine, state.current_chassis)
                            elif state.current_chassis:
                                lightness = 11 - state.current_chassis["weight"]
                                state.car_speed = state.current_chassis["aero"] + lightness

                            # Consume ONE slot run
                            ch["dev_runs_done"] += 1
                            slots_left = max(0, ch["dev_slots"] - ch["dev_runs_done"])

                            team_name = state.player_constructor or "Your team"
                            if slots_left > 0:
                                state.news.append(
                                    f"{team_name}'s chassis program: {outcome} "
                                    f"(program complete — {slots_left} development slot(s) remaining)."
                                )
                            else:
                                state.news.append(
                                    f"{team_name}'s chassis program: {outcome} "
                                    f"(program complete — this chassis has reached its development limit)."
                                )

                            # Optional: flavour for works teams if you're improving THEIR works chassis
                            if supplier_key in ("Enzoni", "Scuderia Valdieri"):
                                state.news.append(
                                    f"Paddock talk: {supplier_key}'s engineers unveil updates to their works chassis."
                                )

                            # End the current program after a completed run
                            state.chassis_project_active = False
                            state.chassis_progress = 0.0
                            state.chassis_project_chassis_id = None

                        else:
                            # No breakthrough yet – weekly flavour update
                            prog_display = max(0.0, min(100.0, state.chassis_progress))
                            team_name = state.player_constructor or "Your team"

                            if weekly_gain < 3:
                                flavour = "progress stalls as your chief mechanic nurses a terrible hangover"
                            elif weekly_gain < 7:
                                flavour = "the crew make steady, methodical progress on the chassis"
                            else:
                                flavour = "a good week in the workshop – your mechanics seem to have found something"

                            slots_left = max(0, ch["dev_slots"] - ch["dev_runs_done"])
                            state.news.append(
                                f"{team_name}'s chassis shop: {flavour} "
                                f"(development progress {prog_display:.1f}/100, slots remaining: {slots_left})."
                            )

                # ------------------------------
                # Weekly loan interest (flat, non-compounding)
                # ------------------------------
                if state.loan_balance > 0 and state.loan_interest_rate > 0:
                    interest = int(state.loan_balance * state.loan_interest_rate)
                    if interest < 1:
                        interest = 1  # at least something each week

                    state.money -= interest
                    state.last_week_loan_interest = interest

                    team_name = state.player_constructor or "Your team"
                    state.news.append(
                        f"{team_name} pay £{interest} in loan interest this week."
                    )

                # ------------------------------
                # Weekly paddock rumour (pure flavour)
                # ------------------------------
                maybe_add_weekly_rumour(state, time)

                # ------------------------------
                # Bankruptcy check AFTER all weekly costs
                # ------------------------------
                if state.money < -1000:
                    rescued = handle_bankruptcy_rescue(state, time)
                    if not rescued or state.money < -1000:
                      state.bankrupt = True
                      state.demo_complete = True
                      


                # Start a new week: clear one-offs for the coming week (defensive)
                state.last_week_purchases = 0
                state.last_week_driver_pay = 0

                # Actually move time forward
                time.advance_week()
                # Next main-loop iteration will detect if the NEW week is a race week
            else:
                # ---- Locked into race weekend: run it ----
                handle_race_week(state, time)
                # handle_race_week runs quali+race and marks the race complete;
                # once it's done, unlock time progression.
                state.pending_race_week = None



        else:
            print("Invalid choice.")




        # If the demo has finished (end of 1951 season or bankruptcy), handle exit / restart
        if state.demo_complete:
            if state.bankrupt:
                # Bankruptcy-specific game over screen
                print("\n💥 BANKRUPT 💥")
                print("Your mechanics walk, the landlord locks the workshop,")
                print("the landlord bolts the workshop doors, and your driver disappears into the night.")
                print("\nYou're out of money, out of luck, and out of the sport.")

                print("\nWhat would you like to do?")
                print("1. Start a new game")
                print("2. Exit")

                choice = input("> ").strip()
                if choice == "1":
                    # Re-initialise everything and go again
                    time = GameTime()
                    state = GameState()
                    setup_player(state)
                    state.reset_championship()
                    continue
                else:
                    break
            else:
                # Normal demo completion (scripted finale etc.)
                # Show any queued story/news before exiting.
                if state.news:
                    print("\n=== News ===")
                    for item in state.news:
                        print(item)
                    print("----------------")
                    state.news.clear()

                print("\nDemo complete. Press Enter to exit.")
                input()
                break


    



if __name__ == "__main__":
    run_game()