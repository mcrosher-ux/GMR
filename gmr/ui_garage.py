#gmr/ui_garage.py
import random
from gmr.constants import ENZONI_PRESTIGE_REQUIREMENT
from gmr.world_logic import describe_career_phase
from gmr.data import engines, chassis_list
from gmr.world_logic import calculate_car_speed
from gmr.careers import describe_driver_fame


def show_engine_shop(state):
    print("\n=== Racecar Parts: Engines ===")

    # Show current engine
    if state.current_engine:
        eng = state.current_engine
        print("Current Engine:")
        print(f"  {eng['name']} (Source: {eng['supplier']})")
        print(f"    Speed .............. {eng['speed']}")
        print(f"    Reliability ........ {eng['reliability']}")
        print(f"    Acceleration ....... {eng['acceleration']}")
        print(f"    Heat Tolerance ..... {eng['heat_tolerance']}")
        print(f"    Notes: {eng['description']}")
        print(f"    Condition .......... {state.engine_wear:.0f}% (max rebuild {state.engine_max_condition:.0f}%)")
        print(f"    Long-term health ... {state.engine_health:.0f}%")
    else:
        print("Current Engine: None installed")

    print("\nAvailable Engines:")
    available_engines = [e for e in engines if e.get("for_sale", True)]

    for idx, engine in enumerate(available_engines, start=1):

        marker = " [CURRENT]" if state.current_engine and engine["id"] == state.current_engine["id"] else ""

        # Is this an Enzoni customer engine?
        is_enzoni = (engine.get("supplier") == "Enzoni")
        enzoni_locked = is_enzoni and (state.prestige < ENZONI_PRESTIGE_REQUIREMENT)

        lock_tag = ""
        if enzoni_locked and not marker:
            lock_tag = " [LOCKED – need more prestige]"

        print(f"\n{idx}. {engine['name']}{marker}{lock_tag}")
        print(f"   Supplier: {engine['supplier']}")
        print(f"     Speed .............. {engine['speed']}")
        print(f"     Reliability ........ {engine['reliability']}")
        print(f"     Acceleration ....... {engine['acceleration']}")
        print(f"     Heat Tolerance ..... {engine['heat_tolerance']}")

        if enzoni_locked:
            # Show the requirement instead of a normal price line
            print(
                f"     Price: £{engine['price']} "
                f"(locked – requires Prestige {ENZONI_PRESTIGE_REQUIREMENT:.1f}+)"
            )
        else:
            print(f"     Price: £{engine['price']}")

        print(f"     About: {engine['description']}")


    # Buying logic
    choice = input("\nEnter the number of an engine to buy and install, or press Enter to go back: ").strip()

    if choice == "":
        return  # back to Garage menu

    if not choice.isdigit():
        print("Invalid input. No purchase made.")
        return

    idx = int(choice)
    if idx < 1 or idx > len(available_engines):
        print("Invalid engine selection.")
        return

    selected_engine = available_engines[idx - 1]


    # Already using this engine — allow buying a fresh unit anyway
    if state.current_engine and selected_engine["id"] == state.current_engine["id"]:
        print("\nYou already have this engine model installed.")
        choice = input("Buy a fresh replacement unit of the same engine? (y/n): ").strip().lower()
        if choice != "y":
            print("No purchase made.")
            return
        # If yes, continue into normal purchase flow (treat as new unit)


    # Prestige gate for Enzoni customer engines
    if selected_engine.get("supplier") == "Enzoni" and state.prestige < ENZONI_PRESTIGE_REQUIREMENT:
        print(
            "\nThe Enzoni racing department politely decline your order.\n"
            "They only supply customer engines to teams with a proven reputation.\n"
            f"(You need at least Prestige {ENZONI_PRESTIGE_REQUIREMENT:.1f}.)"
        )
        return

    price = selected_engine["price"]
    if price > state.money:
        print(f"You cannot afford this engine. You need £{price}, but only have £{state.money}.")
        return

    # Perform purchase
    state.money -= price
    state.last_week_purchases += price

    # IMPORTANT: install a *new unit instance* (don't point at the global catalogue dict)
    state.current_engine = dict(selected_engine)

    # Optional: unique unit id for debugging / proof of replacement
    state.engine_unit_id = getattr(state, "engine_unit_id", 0) + 1
    state.current_engine["unit_id"] = state.engine_unit_id

    # Fresh unit resets
    state.engine_wear = 100.0
    state.engine_max_condition = 100.0
    state.engine_health = 100.0

    # Recalculate overall car speed using engine + chassis
    if state.current_chassis:
        state.car_speed = calculate_car_speed(state.current_engine, state.current_chassis)
    else:
        state.car_speed = state.current_engine["speed"]

    state.car_reliability = state.current_engine["reliability"]


    # Recalculate overall car speed using engine + chassis
    if state.current_chassis:
        state.car_speed = calculate_car_speed(state.current_engine, state.current_chassis)
    else:
        state.car_speed = selected_engine["speed"]

    state.car_reliability = selected_engine["reliability"]


    print(f"\nYou have bought and installed the {selected_engine['name']}.")
    print(f"New car stats - Speed: {state.car_speed}, Reliability: {state.car_reliability}")
    print(f"DEBUG: engine wear={state.engine_wear}, health={state.engine_health}, unit={state.current_engine.get('unit_id')}")

    # Player comfort drop: new engine changes power delivery + behaviour
    if state.player_driver:
        old = float(state.player_driver.get("car_xp", 0.0))
        drop = 1.5  # smaller than chassis change
        state.player_driver["car_xp"] = round(max(0.0, old - drop), 2)
        state.news.append(
            f"New engine fitted — {state.player_driver['name']}'s comfort dips ({old:.1f} → {state.player_driver['car_xp']:.1f})."
        )

    # Offer to name/rename the car after an engine change
    maybe_name_or_rename_car(
        state,
        reason="You’ve just installed a new engine – some teams mark each major spec with a new designation."
    )



def show_chassis_shop(state):
    print("\n=== Racecar Parts: Chassis ===")

    # Show current chassis
    if state.current_chassis:
        ch = state.current_chassis
        print("Current Chassis:")
        print(f"  {ch['name']} (Source: {ch['supplier']})")
        print(f"    Weight ............. {ch['weight']}  (lower = lighter = faster)")
        print(f"    Aero ............... {ch['aero']}")
        print(f"    Suspension ......... {ch.get('suspension', 5)}")
        print(f"    Notes: {ch['description']}")

    else:
        print("Current Chassis: None installed")

    print("\nAvailable Chassis:")
    available_chassis = [c for c in chassis_list if c.get("for_sale", True)]

    for idx, ch in enumerate(available_chassis, start=1):

        marker = " [CURRENT]" if state.current_chassis and ch["id"] == state.current_chassis["id"] else ""
        print(f"\n{idx}. {ch['name']}{marker}")
        print(f"   Supplier: {ch['supplier']}")
        print(f"     Weight ............. {ch['weight']}")
        print(f"     Aero ............... {ch['aero']}")
        print(f"     Suspension ......... {ch.get('suspension', 5)}")
        print(f"     Price: £{ch['price']}")
        print(f"     About: {ch['description']}")


    choice = input("\nEnter the number of a chassis to buy and install, or press Enter to go back: ").strip()

    if choice == "":
        return  # back to Car Parts menu

    if not choice.isdigit():
        print("Invalid input. No purchase made.")
        return

    idx = int(choice)
    if idx < 1 or idx > len(available_chassis):
        print("Invalid chassis selection.")
        return

    selected_chassis = available_chassis[idx - 1]


   

    # Already using this chassis — allow buying a fresh replacement unit anyway
    if state.current_chassis and selected_chassis["id"] == state.current_chassis["id"]:
        print("\nYou already have this chassis model installed.")
        choice = input("Buy a fresh replacement chassis of the same model? (y/n): ").strip().lower()
        if choice != "y":
            print("No purchase made.")
            return
        # If yes, continue into normal purchase flow (treat as new chassis)


    price = selected_chassis["price"]
    if price > state.money:
        print(f"You cannot afford this chassis. You need £{price}, but only have £{state.money}.")
        return

    # Perform purchase
    state.money -= price
    state.last_week_purchases += price

    state.current_chassis = dict(selected_chassis)

    # Set the ceiling and current condition for this design
    if selected_chassis["id"] == "dad_chassis":
        # Dad’s frame: it’s an old design, even when “fresh”
        state.chassis_max_condition = 90.0
        state.chassis_health = 70.0
    else:
        # New bought chassis designs can be fully restored (for now)
        state.chassis_max_condition = 100.0
        state.chassis_health = 100.0

    # A new chassis arrives at its max condition
    state.chassis_wear = state.chassis_max_condition


    # Recalculate combined car speed using engine + chassis
    if state.current_engine:
        state.car_speed = calculate_car_speed(state.current_engine, state.current_chassis)
    else:
        # Fallback: rough chassis-only speed if no engine yet
        lightness = 11 - selected_chassis["weight"]
        state.car_speed = selected_chassis["aero"] + lightness


    print(f"\nYou have bought and installed the {selected_chassis['name']}.")
    print(f"New car speed number: {state.car_speed}")

    if state.player_driver:
        old = float(state.player_driver.get("car_xp", 0.0))
        drop = 3.0  # major change
        state.player_driver["car_xp"] = round(max(0.0, old - drop), 2)
        state.news.append(
            f"New chassis fitted — {state.player_driver['name']}'s comfort drops ({old:.1f} → {state.player_driver['car_xp']:.1f})."
        )


    # Offer to name/rename the car after a chassis change
    maybe_name_or_rename_car(
        state,
        reason="A new chassis usually means a new 'model year' – you could give this spec its own name."
    )

def show_garage(state):
    garage = state.garage
    print("\n=== Garage / Car Info ===")
    print(f"Garage Level: {garage.level}")
    print(f"Base Weekly Cost: £{garage.base_cost}")
    print(f"Staff Count: {garage.staff_count} (Salary £{garage.staff_salary} each)")
    print(f"Customer Parts Only: {garage.customer_parts_only}")
    print(f"R&D Enabled: {garage.r_and_d_enabled}")
    print(f"Factory Team: {garage.factory_team}")
    print(f"Mechanic Skill: {garage.mechanic_skill}/10")

    print("\nYour Car:")
     
    if getattr(state, "car_name", None):
        print(f"  Car Name: {state.car_name}")
    else:
        print("  Car Name: (no official designation yet)")

    # Engine
    if state.current_engine:
        eng = state.current_engine
        print(f"  Engine: {eng['name']} (Supplier: {eng['supplier']})")
        print(f"    Speed .............. {eng['speed']}")
        print(f"    Reliability ........ {eng['reliability']}")
        print(f"    Acceleration ....... {eng['acceleration']}")
        print(f"    Heat Tolerance ..... {eng['heat_tolerance']}")
        print(f"    Notes: {eng['description']}")
    else:
        print("  Engine: None installed")

    # Chassis
    if state.current_chassis:
        ch = state.current_chassis        
        print(f"\n  Chassis: {ch['name']} (Supplier: {ch['supplier']})")
        print(f"    Weight ............. {ch['weight']}  (lower = lighter = faster)")
        print(f"    Aero ............... {ch['aero']}")
        print(f"    Suspension ......... {ch.get('suspension', 5)}")
        print(f"    Notes: {ch['description']}")

        # Development status
        if state.chassis_project_active and state.chassis_project_chassis_id == ch["id"]:
            # Clamp progress to 0–100 just for display
            prog = max(0.0, min(100.0, state.chassis_progress))
            print(f"    Development program: ACTIVE (progress {prog:.1f}/100)")
        elif ch.get("dev_done"):
            print("    Development program: Completed for this chassis design")
        else:
            print("    Development program: Inactive")
    else:
        print("  Chassis: None installed")


    print(f"  Overall Speed: {state.car_speed}")
    print(f"  Overall Reliability: {state.car_reliability}")

    # Quick verdict on where this thing probably sits in the field
    speed = state.car_speed
    rel = state.car_reliability

    if speed >= 9:
        pace_label = "potential race winner on the right day"
    elif speed >= 7:
        pace_label = "solid front-runner or strong midfield car"
    elif speed >= 5:
        pace_label = "midfield privateer – needs work to fight Enzoni"
    else:
        pace_label = "backmarker – you'll need luck or rain to shine"

    if rel >= 8:
        rel_label = "rarely lets go mechanically"
    elif rel >= 6:
        rel_label = "fairly dependable if you don't abuse it"
    elif rel >= 4:
        rel_label = "fragile – expect occasional failures"
    else:
        rel_label = "glass cannon – speed will often come at the price of DNFs"

    print(f"  Car verdict: pace – {pace_label}; reliability – {rel_label}")

    # Condition readout
    print(
        f"  Engine condition:  {state.engine_wear:.0f}% "
        f"(max {getattr(state, 'engine_max_condition', 100.0):.0f}%)"
    )
    print(
        f"  Chassis condition: {state.chassis_wear:.0f}% "
        f"(max {getattr(state, 'chassis_max_condition', 100.0):.0f}%)"
    )

    if state.player_driver:
        d = state.player_driver
        fame = d.get("fame", 0)
        age = d.get("age", None)

        print(f"Your Driver: {d['name']}")
        if age is not None:
            print(f"  Age: {age}")
        print(f"  Pace: {d['pace']}  Consistency: {d['consistency']}")
        print(
            f"  Aggression: {d['aggression']}  "
            f"Mech Sympathy: {d['mechanical_sympathy']}  "
            f"Wet Skill: {d['wet_skill']}"
        )
        print(f"  Fame: {fame} ({describe_driver_fame(fame)})")

        # Soft hint at where they are in their career curve
        print(f"  Career stage: {describe_career_phase(d)}")

        # Simple career summary with your constructor
        print("\n  Results with your team:")
        print(f"    Races entered: {state.races_entered_with_team}")
        print(f"    Wins: {state.wins_with_team}  Podiums: {state.podiums_with_team}")
        print(f"    Points scored with your team: {state.points_with_team}")


    else:
        print("No driver currently hired.")
        if state.prestige < 1.0:
            tier = "Unknown privateer"
        elif state.prestige < 3.0:
            tier = "Up-and-coming team"
        elif state.prestige < 6.0:
            tier = "Respected contender"
        elif state.prestige < 10.0:
            tier = "Premium racing outfit"
        else:
            tier = "Elite powerhouse"
        print(f"Team Prestige: {state.prestige:.1f} ({tier})")


    print(f"\nTeam Prestige: {state.prestige:.1f}  (growing with results & reliability)")

def rename_car(state):
    """
    Let the player give the current car an official designation,
    e.g. 'Bramwell X1' or 'Bramwell 47/1'.
    """
    print("\n=== Name / Rename Car ===")

    if state.current_engine is None or state.current_chassis is None:
        print("You need a complete car (engine + chassis fitted) before naming it.")
        input("\nPress Enter to return to the Garage menu...")
        return

    print(f"Current car name: {getattr(state, 'car_name', '')}")
    new_name = input("Enter a new official designation (or press Enter to cancel): ").strip()

    if new_name == "":
        print("You decide to keep the current name for now.")
    else:
        state.car_name = new_name
        print(f"Your car is now officially designated: {state.car_name}")

    input("\nPress Enter to return to the Garage menu...")


def can_book_test_day(state, time):
    """
    You can only book a proper private test day every ~2 months (8 weeks).
    """
    if state.last_test_abs_week == 0:
        return True

    weeks_since = time.absolute_week - state.last_test_abs_week
    return weeks_since >= 8

def apply_chassis_test(state):
    """
    Apply a single test day's worth of learning to the current chassis.
    Uses diminishing returns so the first few sessions matter most.
    """
    if not state.current_chassis:
        return 0.0  # nothing to learn about

    # Base raw gain
    base_gain = random.uniform(0.8, 1.6)

    # Diminishing returns – once you have ~10 insight, extra tests give smaller gains
    decay = max(0.3, 1.0 - state.chassis_insight / 12.0)
    gain = base_gain * decay

    state.chassis_insight += gain
    # Hard cap for the early-era demo
    state.chassis_insight = min(state.chassis_insight, 12.0)

    return gain


def handle_test_day(state, time):
    """
    Book and run a local test day.
    Costs money, gated by cooldown, and increases chassis_insight.
    """
    print("\n=== Private Test Day ===")

    if not state.current_chassis or not state.current_engine:
        print("You need a complete car (engine + chassis) before you can go testing.")
        input("\nPress Enter to return to the Garage menu...")
        return

    if not can_book_test_day(state, time):
        print("Marblethorpe's managers shake their heads – they can't give you")
        print("another private slot so soon. Try again later in the year.")
        input("\nPress Enter to return to the Garage menu...")
        return

    # Cost for a day hiring a small local circuit + fuel + tyres, etc.
    TEST_DAY_COST = 150

    print(f"A local circuit offers you a private test day for £{TEST_DAY_COST}.")
    print("You and your mechanics will spend the day pounding around,")
    print("collecting notes and gradually understanding the chassis better.")
    print("\nProceed with booking this test day? (y/n)")

    choice = input("> ").strip().lower()
    if choice != "y":
        print("You decide not to spend the money today.")
        input("\nPress Enter to return to the Garage menu...")
        return

    if state.money < TEST_DAY_COST:
        print("\nYou simply can't afford the track hire fee right now.")
        input("\nPress Enter to return to the Garage menu...")
        return

    # Pay and log as a 'purchase' for weekly finances
    state.money -= TEST_DAY_COST
    state.last_week_purchases += TEST_DAY_COST

    # Time stamp the test so we can't spam it
    state.last_test_abs_week = time.absolute_week

    # Apply learning
    before = state.chassis_insight
    gained = apply_chassis_test(state)
    after = state.chassis_insight

    print(f"\nYou spend the day lapping, scribbling notes and arguing with your mechanic.")
    print(f"Chassis insight improves from {before:.1f} to {after:.1f}.")

    # News item for flavour
    team_name = state.player_constructor or "Your team"
    state.news.append(
        f"{team_name} complete a private test day, gaining a better feel for the chassis "
        f"(insight {before:.1f} → {after:.1f})."
    )

    input("\nPress Enter to return to the Garage menu...")




def manage_chassis_development(state):
    """
    Toggle a long-term chassis development program on/off.
    Uses dev_slots / dev_runs_done instead of dev_done.
    """
    print("\n=== Chassis Development Program ===")

    if not state.current_chassis:
        print("You have no chassis installed. Fit a chassis before starting development.")
        input("\nPress Enter to return to the Garage menu...")
        return

    ch = state.current_chassis

    # Ensure slot fields exist (safe for old saves)
    if "dev_slots" not in ch:
        ch["dev_slots"] = 1
    if "dev_runs_done" not in ch:
        ch["dev_runs_done"] = 0

    slots_left = ch["dev_slots"] - ch["dev_runs_done"]

    if slots_left <= 0:
        print("Your current chassis has already reached its development limit.")
        print("Further improvements on this design are unlikely.")
        input("\nPress Enter to return to the Garage menu...")
        return

    status = "ACTIVE" if state.chassis_project_active else "inactive"
    print(f"Current status: {status}")
    print(f"Development slots remaining on this chassis: {slots_left}")
    print("When active, you pay extra each week for your mechanics")
    print("to work on the current chassis. Occasionally they will")
    print("find gains (or make a mistake) that permanently changes its stats.")
    print("\n1. Toggle program on/off")
    print("2. Back to Garage menu")

    choice = input("> ").strip()

    if choice == "1":
        state.chassis_project_active = not state.chassis_project_active
        if state.chassis_project_active:
            print("\nYour mechanics begin a long-term development program on the current chassis.")
            state.chassis_progress = 0.0
            state.chassis_project_chassis_id = ch["id"]
        else:
            print("\nYou suspend the chassis development program for now.")
        input("\nPress Enter to return to the Garage menu...")
    else:
        return


def handle_repairs(state):
    """
    Simple maintenance menu: spend money to restore engine/chassis condition.
    Uses last_week_purchases to log the spend for finances.
    """
    while True:
        print("\n=== Repairs & Maintenance ===")
        print(f"Current engine condition:  {state.engine_wear:.0f}%")
        print(f"Current chassis condition: {state.chassis_wear:.0f}%")

        # Use the current caps instead of hard-coded 100%
        engine_cap = getattr(state, "engine_max_condition", 100.0)
        chassis_cap = getattr(state, "chassis_max_condition", 100.0)

        print(f"\n1. Refurbish engine up to {engine_cap:.0f}%")
        print(f"2. Overhaul chassis up to {chassis_cap:.0f}%")
        print("3. Back to Garage menu")


        choice = input("> ").strip()

        if choice == "1":
            # Use the max for this engine, not hard-coded 100
            if state.engine_wear >= state.engine_max_condition:
                print("The engine is already at its current best possible condition.")
                continue

            missing = state.engine_max_condition - state.engine_wear
            # Each % point costs £4 – not pocket change, but cheaper than a new engine
            cost = int(missing * 4)

            print(
                f"\nEngine refurbish cost: £{cost} to restore from "
                f"{state.engine_wear:.0f}% to {state.engine_max_condition:.0f}%."
            )
            confirm = input("Proceed with engine refurbish? (y/n): ").strip().lower()
            if confirm == "y":
                if cost > state.money:
                    print("You cannot afford this refurbish right now.")
                else:
                    state.money -= cost
                    state.last_week_purchases += cost
                    state.engine_wear = state.engine_max_condition
                    print("Your mechanics strip and rebuild the engine. It feels fresh again.")
                    state.news.append(
                        "Your crew complete a full engine refurbish, restoring it to its current peak condition."
                    )

                    # Each full rebuild fatigues the hardware: future ceiling comes down
                    if state.engine_max_condition > 60.0:
                        state.engine_max_condition -= 10.0



        elif choice == "2":
            cap = state.chassis_max_condition

            if state.chassis_wear >= cap:
                print("The chassis is already in as good a shape as it can realistically be.")
                continue

            missing = cap - state.chassis_wear
            # Chassis work is a bit cheaper per % than engine internals
            cost = int(missing * 3)

            print(f"\nChassis overhaul cost: £{cost} to restore from {state.chassis_wear:.0f}% to {cap:.0f}%.")
            confirm = input("Proceed with chassis overhaul? (y/n): ").strip().lower()
            if confirm == "y":
                if cost > state.money:
                    print("You cannot afford this overhaul right now.")
                else:
                    state.money -= cost
                    state.last_week_purchases += cost
                    # Restore up to the current ceiling
                    state.chassis_wear = cap
                    print("Your mechanics straighten, reinforce and refresh the chassis.")
                    state.news.append(
                        "A full chassis overhaul leaves your car feeling tight and responsive again."
                    )

                    # Each major rebuild fatigues the metal – future ceiling drops.
                    if cap > 60.0:
                        state.chassis_max_condition = max(60.0, cap - 10.0)

            continue

        elif choice == "3" or choice == "":
            break
        else:
            print("Invalid choice.")

def maybe_name_or_rename_car(state, reason=None):
    """
    If you have a complete car (engine + chassis), let the player
    name or rename it.

    'reason' is just a flavour string like 'after installing a new engine'.
    """
    if not state.current_engine or not state.current_chassis:
        return  # nothing to name yet

    print("\n--- Car Designation ---")
    current_name = getattr(state, "car_name", "")
    if current_name:
        print(f"Current car name: {current_name}")
    else:
        print("Your car doesn't have an official name yet.")

    if reason:
        print(reason)

    # Suggest something like 'TeamName X1' if they have nothing yet
    default_suggestion = None
    if not current_name and state.player_constructor:
        default_suggestion = f"{state.player_constructor} X1"


    if default_suggestion:
        print(f"(Suggestion: {default_suggestion})")

    new_name = input("Enter a new car name (or press Enter to keep current): ").strip()

    if new_name == "":
        print("You keep the existing designation.")
        return

    state.car_name = new_name
    print(f"Car will be known as: {state.car_name}")
