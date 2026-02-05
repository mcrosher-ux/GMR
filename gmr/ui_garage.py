# gmr/ui_garage.py
import random
from gmr.constants import (
    ENZONI_PRESTIGE_REQUIREMENT,
    calculate_garage_benefits,
    clamp_chassis_aero,
    clamp_chassis_suspension,
    clamp_chassis_weight,
)
from gmr.world_logic import describe_career_phase
from gmr.data import engines, chassis_list, gearboxes, brakes
from gmr.world_logic import calculate_car_speed, calculate_car_reliability
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
    state.last_week_outgoings += price

    # IMPORTANT: install a *new unit instance* (don't point at the global catalogue dict)
    state.current_engine = dict(selected_engine)

    # Optional: unique unit id for debugging / proof of replacement
    state.engine_unit_id = getattr(state, "engine_unit_id", 0) + 1
    state.current_engine["unit_id"] = state.engine_unit_id

    # Fresh unit resets - CRITICAL: new engine = fresh condition
    old_wear = getattr(state, 'engine_wear', 0)
    old_health = getattr(state, 'engine_health', 0)
    state.engine_wear = 100.0
    state.engine_max_condition = 100.0
    state.engine_health = 100.0
    
    print(f"\n  [Engine condition reset: {old_wear:.0f}% → 100% (fresh unit)]")

    # Recalculate overall car speed and reliability using engine + chassis + gearbox + brakes
    if state.current_chassis:
        state.car_speed = calculate_car_speed(
            state.current_engine,
            state.current_chassis,
            getattr(state, "current_gearbox", None),
            getattr(state, "current_brakes", None),
        )
    else:
        state.car_speed = state.current_engine["speed"]

    state.car_reliability = calculate_car_reliability(
        state.current_engine,
        getattr(state, "current_gearbox", None),
    )


    print(f"\nYou have bought and installed the {selected_engine['name']}.")
    print(f"New car stats - Speed: {state.car_speed}, Reliability: {state.car_reliability}")

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
    
    # Get developed upgrades dict for display
    developed_upgrades = getattr(state, 'chassis_developed_upgrades', {})

    for idx, ch in enumerate(available_chassis, start=1):

        marker = " [CURRENT]" if state.current_chassis and ch["id"] == state.current_chassis["id"] else ""
        print(f"\n{idx}. {ch['name']}{marker}")
        print(f"   Supplier: {ch['supplier']}")
        print(f"     Weight ............. {ch['weight']}")
        print(f"     Aero ............... {ch['aero']}")
        print(f"     Suspension ......... {ch.get('suspension', 5)}")
        print(f"     Price: £{ch['price']}")
        
        # Show if we have developed upgrades for this chassis
        dev = developed_upgrades.get(ch["id"], {})
        if any(v != 0 for v in dev.values()):
            parts = []
            if dev.get("aero", 0) > 0:
                parts.append(f"+{dev['aero']} aero")
            if dev.get("suspension", 0) > 0:
                parts.append(f"+{dev['suspension']} susp")
            if dev.get("weight", 0) < 0:
                parts.append(f"{dev['weight']} wt")
            print(f"     ★ UPGRADES AVAILABLE: {', '.join(parts)}")
        
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
    state.last_week_outgoings += price

    state.current_chassis = dict(selected_chassis)
    
    # ---- Check for developed upgrades that can be applied ----
    chassis_id = selected_chassis["id"]
    developed = getattr(state, 'chassis_developed_upgrades', {}).get(chassis_id, {})
    
    has_upgrades = any(v != 0 for v in developed.values())
    if has_upgrades:
        print("\n═══════════════════════════════════════════════════════════")
        print("  Your mechanics have developed upgrades for this chassis model!")
        print("═══════════════════════════════════════════════════════════")
        
        upgrade_parts = []
        if developed.get("aero", 0) > 0:
            upgrade_parts.append(f"+{developed['aero']} aero")
        if developed.get("suspension", 0) > 0:
            upgrade_parts.append(f"+{developed['suspension']} suspension")
        if developed.get("weight", 0) < 0:
            upgrade_parts.append(f"{developed['weight']} weight")
        
        print(f"  Available upgrades: {', '.join(upgrade_parts)}")
        
        # Calculate upgrade cost based on mechanic skill and garage upgrades
        mech_skill = state.garage.get_effective_mechanic_skill(state)
        # Base cost £200, reduced by mechanic skill (max discount ~£50 at skill 10)
        upgrade_cost = max(100, int(200 - (mech_skill * 5)))
        
        print(f"  Installation cost: £{upgrade_cost}")
        print(f"  (Your head mechanic's skill reduces this cost)")
        
        if upgrade_cost <= state.money:
            apply_choice = input("\nApply your developed upgrades to this new chassis? (y/n): ").strip().lower()
            if apply_choice == "y":
                state.money -= upgrade_cost
                state.last_week_purchases += upgrade_cost
                state.last_week_outgoings += upgrade_cost
                
                # Apply the upgrades
                if developed.get("aero", 0) > 0:
                    state.current_chassis["aero"] = state.current_chassis.get("aero", 1) + developed["aero"]
                if developed.get("suspension", 0) > 0:
                    state.current_chassis["suspension"] = state.current_chassis.get("suspension", 5) + developed["suspension"]
                if developed.get("weight", 0) < 0:
                    state.current_chassis["weight"] = state.current_chassis.get("weight", 7) + developed["weight"]
                
                print(f"\nUpgrades applied! Your mechanics fitted the developed parts.")
                print(f"  Final chassis stats:")
                print(f"    Weight: {state.current_chassis['weight']}")
                print(f"    Aero: {state.current_chassis['aero']}")
                print(f"    Suspension: {state.current_chassis.get('suspension', 5)}")
            else:
                print("\nNo upgrades applied. You can develop this chassis further later.")
        else:
            print(f"\n  (You cannot afford the £{upgrade_cost} installation fee)")

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

    # Reset chassis insight since this is a new chassis to understand
    state.chassis_insight = 0.0


    # Recalculate combined car speed using engine + chassis + gearbox + brakes
    if state.current_engine:
        state.car_speed = calculate_car_speed(
            state.current_engine,
            state.current_chassis,
            getattr(state, "current_gearbox", None),
            getattr(state, "current_brakes", None),
        )
        state.car_reliability = calculate_car_reliability(
            state.current_engine,
            getattr(state, "current_gearbox", None),
        )
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


def show_gearbox_shop(state, time):
    print("\n=== Racecar Parts: Gearboxes ===")

    # Show current gearbox
    if state.current_gearbox:
        gb = state.current_gearbox
        print("Current Gearbox:")
        print(f"  {gb['name']} (Source: {gb['supplier']})")
        print(f"    Shift Quality ....... {gb['shift_quality']}")
        print(f"    Reliability Bonus ... {gb.get('reliability_bonus', 0)}")
        print(f"    Notes: {gb['description']}")
    else:
        print("Current Gearbox: None installed")

    print("\nAvailable Gearboxes:")
    available_gearboxes = [g for g in gearboxes if g.get("year_available", 1947) <= time.year]

    for idx, gb in enumerate(available_gearboxes, start=1):
        marker = " [CURRENT]" if state.current_gearbox and gb["id"] == state.current_gearbox.get("id") else ""
        print(f"\n{idx}. {gb['name']}{marker}")
        print(f"   Supplier: {gb['supplier']}")
        print(f"     Shift Quality ....... {gb['shift_quality']}")
        print(f"     Reliability Bonus ... {gb.get('reliability_bonus', 0)}")
        print(f"     Price: £{gb['price']}")
        print(f"     About: {gb['description']}")

    choice = input("\nEnter the number of a gearbox to buy and install, or press Enter to go back: ").strip()
    if choice == "":
        return
    if not choice.isdigit():
        print("Invalid input. No purchase made.")
        return

    idx = int(choice)
    if idx < 1 or idx > len(available_gearboxes):
        print("Invalid gearbox selection.")
        return

    selected = available_gearboxes[idx - 1]
    price = selected["price"]
    if price > state.money:
        print(f"You cannot afford this gearbox. You need £{price}, but only have £{state.money}.")
        return

    state.money -= price
    state.last_week_purchases += price
    state.last_week_outgoings += price
    state.current_gearbox = dict(selected)

    # Recalculate car stats if car is complete
    if state.current_engine and state.current_chassis:
        state.car_speed = calculate_car_speed(
            state.current_engine,
            state.current_chassis,
            state.current_gearbox,
            getattr(state, "current_brakes", None),
        )
        state.car_reliability = calculate_car_reliability(
            state.current_engine,
            state.current_gearbox,
        )

    print(f"\nYou have bought and installed the {selected['name']}.")


def show_brake_shop(state, time):
    print("\n=== Racecar Parts: Brakes ===")

    # Show current brakes
    if state.current_brakes:
        br = state.current_brakes
        print("Current Brakes:")
        print(f"  {br['name']} (Source: {br['supplier']})")
        print(f"    Braking ............. {br['braking']}")
        print(f"    Crash Multiplier .... {br.get('crash_mult', 1.0)}")
        print(f"    Notes: {br['description']}")
    else:
        print("Current Brakes: None installed")

    print("\nAvailable Brakes:")
    available_brakes = [b for b in brakes if b.get("year_available", 1947) <= time.year]

    for idx, br in enumerate(available_brakes, start=1):
        marker = " [CURRENT]" if state.current_brakes and br["id"] == state.current_brakes.get("id") else ""
        print(f"\n{idx}. {br['name']}{marker}")
        print(f"   Supplier: {br['supplier']}")
        print(f"     Braking ............. {br['braking']}")
        print(f"     Crash Multiplier .... {br.get('crash_mult', 1.0)}")
        print(f"     Price: £{br['price']}")
        print(f"     About: {br['description']}")

    choice = input("\nEnter the number of brakes to buy and install, or press Enter to go back: ").strip()
    if choice == "":
        return
    if not choice.isdigit():
        print("Invalid input. No purchase made.")
        return

    idx = int(choice)
    if idx < 1 or idx > len(available_brakes):
        print("Invalid brakes selection.")
        return

    selected = available_brakes[idx - 1]
    price = selected["price"]
    if price > state.money:
        print(f"You cannot afford these brakes. You need £{price}, but only have £{state.money}.")
        return

    state.money -= price
    state.last_week_purchases += price
    state.last_week_outgoings += price
    state.current_brakes = dict(selected)

    # Recalculate car stats if car is complete
    if state.current_engine and state.current_chassis:
        state.car_speed = calculate_car_speed(
            state.current_engine,
            state.current_chassis,
            getattr(state, "current_gearbox", None),
            state.current_brakes,
        )
        state.car_reliability = calculate_car_reliability(
            state.current_engine,
            getattr(state, "current_gearbox", None),
        )

    print(f"\nYou have bought and installed the {selected['name']}.")


def show_garage(state):
    garage = state.garage
    print("\n=== Garage / Car Info ===")
    print(f"Garage Level: {garage.upgrade_level} ({len(garage.upgrades)} upgrades installed)")
    print(f"Base Weekly Cost: £{garage.base_cost}")
    print(f"Staff Count: {garage.staff_count} (Salary £{garage.staff_salary} each)")
    print(f"Customer Parts Only: {garage.customer_parts_only}")
    print(f"R&D Enabled: {garage.r_and_d_enabled}")
    print(f"Factory Team: {garage.factory_team}")
    print(f"Mechanic Skill: {garage.get_effective_mechanic_skill()}/10 ({garage.mechanic_skill} base + {garage.get_effective_mechanic_skill() - garage.mechanic_skill} from upgrades)")

    # Show installed upgrades
    if garage.upgrades:
        print(f"Installed Upgrades: {', '.join(garage.upgrades)}")

    # Show current upgrade benefits
    benefits = calculate_garage_benefits(garage)
    if benefits["repair_discount"] > 0 or benefits["repair_speed_bonus"] > 0 or benefits["mechanic_skill_bonus"] > 0:
        print("\nUpgrade Benefits:")
        if benefits["repair_discount"] > 0:
            print(f"  • Repairs {benefits['repair_discount']*100:.0f}% cheaper")
        if benefits["repair_speed_bonus"] > 0:
            print(f"  • Repairs {benefits['repair_speed_bonus']*100:.0f}% more effective")
        if benefits["mechanic_skill_bonus"] > 0:
            print(f"  • +{benefits['mechanic_skill_bonus']} mechanic skill")

    # R&D status
    if getattr(state, "r_and_d_active", False):
        print(f"\nR&D Program: ACTIVE ({state.r_and_d_focus})")
        print(f"  Progress: {state.r_and_d_progress:.1f}/100")
        print(f"  Insight: {state.r_and_d_insight:.1f}/10")
    else:
        print("\nR&D Program: inactive")

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

    # Gearbox
    if state.current_gearbox:
        gb = state.current_gearbox
        print(f"  Gearbox: {gb['name']} (Supplier: {gb['supplier']})")
        print(f"    Shift Quality ....... {gb['shift_quality']}")
        print(f"    Reliability Bonus ... {gb.get('reliability_bonus', 0)}")
        print(f"    Notes: {gb['description']}")
    else:
        print("  Gearbox: None installed")

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

        # Chassis insight (understanding gained from test days)
        insight = getattr(state, "chassis_insight", 0.0)
        insight_desc = "none" if insight < 0.5 else f"{insight:.1f}/12"
        print(f"    Chassis insight: {insight_desc} (improves development quality)")
    else:
        print("  Chassis: None installed")

    # Brakes
    if state.current_brakes:
        br = state.current_brakes
        print(f"  Brakes: {br['name']} (Supplier: {br['supplier']})")
        print(f"    Braking ............. {br['braking']}")
        print(f"    Crash Multiplier .... {br.get('crash_mult', 1.0)}")
        print(f"    Notes: {br['description']}")
    else:
        print("  Brakes: None installed")


    print(f"  Overall Speed: {state.car_speed}")
    print(f"  Overall Reliability: {state.car_reliability}")
    print(f"  Tyre sets in garage: {getattr(state, 'tyre_sets', 0)}")

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
    Increases chassis_insight (0-12), which improves development quality.
    Uses diminishing returns so early tests matter most.
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
    Costs £150, increases chassis_insight (0-12), which improves development quality.
    Available every 8 weeks. Insight resets when you change chassis.
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
    print("This increases your 'chassis insight', which improves development quality.")
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
    state.last_week_outgoings += TEST_DAY_COST

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
    print("Higher chassis insight (from test days) improves success rates.")
    print("\n1. Toggle program on/off")
    print("2. Back to Garage menu")

    choice = input("> ").strip()

    if choice == "1":
        state.chassis_project_active = not state.chassis_project_active
        if state.chassis_project_active:
            print("\nYour mechanics begin a long-term development program on the current chassis.")
            
            # Choose development target
            while True:
                print("\nWhich aspect of the chassis would you like to focus development on?")
                print("1. Aerodynamics (improves cornering speed)")
                print("2. Suspension (improves handling and traction)")
                print("3. Weight reduction (improves acceleration and top speed)")
                
                target_choice = input("> ").strip()
                if target_choice == "1":
                    state.chassis_project_stat_target = "aero"
                    break
                elif target_choice == "2":
                    state.chassis_project_stat_target = "suspension"
                    break
                elif target_choice == "3":
                    state.chassis_project_stat_target = "weight"
                    break
                else:
                    print("Invalid choice. Please select 1-3.")
            
            # Calculate dev bonus (player teams get a base bonus)
            state.chassis_project_dev_bonus = 0.0  # Player teams start with no bonus
            
            state.chassis_progress = 0.0
            state.chassis_project_chassis_id = ch["id"]
            
            target_names = {"aero": "aerodynamics", "suspension": "suspension", "weight": "weight reduction"}
            print(f"\nDevelopment program started, focusing on {target_names[state.chassis_project_stat_target]}.")
        else:
            print("\nYou suspend the chassis development program for now.")
            state.chassis_project_stat_target = None
            state.chassis_project_dev_bonus = 0.0
        input("\nPress Enter to return to the Garage menu...")
    else:
        return


def get_available_rnd_projects(time):
    year = time.year
    projects = [
        ("chassis_refinement", "Chassis refinement (1947+)")
    ]

    if year >= 1951:
        projects.append(("gearbox_development", "Gearbox development (1951+)") )
        projects.append(("brake_development", "Brake development (1951+)") )

    if year >= 1955:
        projects.append(("front_cooling", "Front cooling & radiator ducting (1955+)") )

    if year >= 1958:
        projects.append(("rear_engine_conversion", "Rear-engine conversion (1958+)") )

    return projects


def _rnd_quality_roll(state, garage, time):
    mech = garage.get_effective_mechanic_skill(state)
    insight = getattr(state, "r_and_d_insight", 0.0)
    roll = random.random()
    roll += (mech / 10.0) * 0.25
    roll += (insight / 10.0) * 0.20
    # Early era: higher risk, later era: more reliable R&D
    if time.year <= 1950:
        roll -= 0.10
    elif time.year >= 1958:
        roll += 0.05
    return max(0.0, min(1.0, roll))


def _apply_rnd_outcome(state, focus, quality):
    garage = state.garage
    mech = garage.get_effective_mechanic_skill(state)

    # Outcome tiers
    if quality < 0.45:
        outcome = "fail"
    elif quality < 0.75:
        outcome = "minor"
    else:
        outcome = "major"

    def recalc_car():
        if state.current_engine and state.current_chassis:
            state.car_speed = calculate_car_speed(
                state.current_engine,
                state.current_chassis,
                getattr(state, "current_gearbox", None),
                getattr(state, "current_brakes", None),
            )
            state.car_reliability = calculate_car_reliability(
                state.current_engine,
                getattr(state, "current_gearbox", None),
            )

    # Chassis refinement
    if focus == "chassis_refinement":
        if not state.current_chassis:
            state.news.append("R&D stalled: no chassis installed.")
            return

        ch = state.current_chassis
        stat = random.choice(["aero", "suspension", "weight"])

        if outcome == "fail":
            if stat == "weight":
                ch["weight"] = clamp_chassis_weight(ch.get("weight", 7) + 1)
            elif stat == "aero":
                ch["aero"] = clamp_chassis_aero(ch.get("aero", 2) - 1)
            else:
                ch["suspension"] = clamp_chassis_suspension(ch.get("suspension", 5) - 1)
            state.news.append("R&D setback: chassis changes missed the mark.")
        elif outcome == "minor":
            if stat == "weight":
                ch["weight"] = clamp_chassis_weight(ch.get("weight", 7) - 1)
            elif stat == "aero":
                ch["aero"] = clamp_chassis_aero(ch.get("aero", 2) + 1)
            else:
                ch["suspension"] = clamp_chassis_suspension(ch.get("suspension", 5) + 1)
            state.news.append("R&D success: small chassis gains achieved.")
        else:
            if stat == "weight":
                ch["weight"] = clamp_chassis_weight(ch.get("weight", 7) - 2)
            elif stat == "aero":
                ch["aero"] = clamp_chassis_aero(ch.get("aero", 2) + 2)
            else:
                ch["suspension"] = clamp_chassis_suspension(ch.get("suspension", 5) + 2)
            state.news.append("R&D breakthrough: major chassis improvement unlocked.")

        recalc_car()
        return

    # Gearbox development
    if focus == "gearbox_development":
        gb = getattr(state, "current_gearbox", None)
        if not gb:
            state.news.append("R&D stalled: no gearbox installed.")
            return

        if outcome == "fail":
            gb["shift_quality"] = max(1, gb.get("shift_quality", 5) - 1)
            state.news.append("R&D setback: gearbox revisions reduced shift quality.")
        elif outcome == "minor":
            gb["shift_quality"] = min(10, gb.get("shift_quality", 5) + 1)
            state.news.append("R&D success: improved gearbox shift quality.")
        else:
            gb["shift_quality"] = min(10, gb.get("shift_quality", 5) + 2)
            gb["reliability_bonus"] = gb.get("reliability_bonus", 0) + 1
            state.news.append("R&D breakthrough: sharper shifts and stronger gearbox internals.")

        recalc_car()
        return

    # Brake development
    if focus == "brake_development":
        br = getattr(state, "current_brakes", None)
        if not br:
            state.news.append("R&D stalled: no brakes installed.")
            return

        if outcome == "fail":
            br["braking"] = max(1, br.get("braking", 5) - 1)
            br["crash_mult"] = min(1.15, br.get("crash_mult", 1.0) + 0.05)
            state.news.append("R&D setback: brake tuning worsened stability.")
        elif outcome == "minor":
            br["braking"] = min(10, br.get("braking", 5) + 1)
            br["crash_mult"] = max(0.90, br.get("crash_mult", 1.0) - 0.03)
            state.news.append("R&D success: improved braking consistency.")
        else:
            br["braking"] = min(10, br.get("braking", 5) + 2)
            br["crash_mult"] = max(0.85, br.get("crash_mult", 1.0) - 0.06)
            state.news.append("R&D breakthrough: strong braking upgrade achieved.")

        recalc_car()
        return

    # Front cooling & radiator ducting
    if focus == "front_cooling":
        eng = getattr(state, "current_engine", None)
        if not eng:
            state.news.append("R&D stalled: no engine installed.")
            return

        if outcome == "fail":
            eng["heat_tolerance"] = max(1, eng.get("heat_tolerance", 5) - 1)
            state.news.append("R&D setback: cooling revisions hurt heat management.")
        elif outcome == "minor":
            eng["heat_tolerance"] = min(10, eng.get("heat_tolerance", 5) + 1)
            state.news.append("R&D success: modest cooling improvements found.")
        else:
            eng["heat_tolerance"] = min(10, eng.get("heat_tolerance", 5) + 2)
            eng["reliability"] = min(10, eng.get("reliability", 5) + 1)
            state.news.append("R&D breakthrough: major cooling gains unlock reliability.")

        recalc_car()
        return

    # Rear-engine conversion
    if focus == "rear_engine_conversion":
        ch = getattr(state, "current_chassis", None)
        eng = getattr(state, "current_engine", None)
        if not ch or not eng:
            state.news.append("R&D stalled: rear-engine conversion needs a complete car.")
            return

        if not state.r_and_d_rear_engine_backup:
            state.r_and_d_rear_engine_backup = {
                "weight": ch.get("weight", 7),
                "aero": ch.get("aero", 2),
                "suspension": ch.get("suspension", 5),
                "heat_tolerance": eng.get("heat_tolerance", 5),
            }

        if outcome == "fail":
            ch["weight"] = clamp_chassis_weight(ch.get("weight", 7) + 2)
            ch["aero"] = clamp_chassis_aero(ch.get("aero", 2) - 1)
            ch["suspension"] = clamp_chassis_suspension(ch.get("suspension", 5) - 1)
            eng["heat_tolerance"] = max(1, eng.get("heat_tolerance", 5) - 1)
            state.r_and_d_rear_engine_failed = True
            state.r_and_d_rear_engine_active = False
            state.news.append("R&D failure: rear-engine conversion upset balance and cooling.")
        elif outcome == "minor":
            ch["weight"] = clamp_chassis_weight(ch.get("weight", 7) - 1)
            ch["aero"] = clamp_chassis_aero(ch.get("aero", 2) + 1)
            ch["suspension"] = clamp_chassis_suspension(ch.get("suspension", 5) + 1)
            eng["heat_tolerance"] = min(10, eng.get("heat_tolerance", 5) + 1)
            state.r_and_d_rear_engine_active = True
            state.r_and_d_rear_engine_failed = False
            state.news.append("R&D success: early rear-engine layout shows promise.")
        else:
            ch["weight"] = clamp_chassis_weight(ch.get("weight", 7) - 2)
            ch["aero"] = clamp_chassis_aero(ch.get("aero", 2) + 2)
            ch["suspension"] = clamp_chassis_suspension(ch.get("suspension", 5) + 2)
            eng["heat_tolerance"] = min(10, eng.get("heat_tolerance", 5) + 2)
            state.r_and_d_rear_engine_active = True
            state.r_and_d_rear_engine_failed = False
            state.news.append("R&D breakthrough: rear-engine conversion is a massive leap forward.")

        recalc_car()
        return


def maybe_progress_r_and_d(state, time):
    if not getattr(state, "r_and_d_active", False):
        return

    # Basic gating: allow 1947-50 only chassis refinement
    if time.year <= 1950 and state.r_and_d_focus != "chassis_refinement":
        return

    # Weekly cost and progress
    mech = state.garage.get_effective_mechanic_skill(state)
    # Era tuning: early R&D is costly and slow; later becomes more efficient
    if time.year <= 1950:
        base_cost = 75
        progress_base = 5
    elif time.year <= 1956:
        base_cost = 65
        progress_base = 6
    else:
        base_cost = 55
        progress_base = 7

    if state.garage.r_and_d_enabled:
        base_cost += 10

    if state.money < base_cost:
        return

    state.money -= base_cost
    state.last_week_rnd += base_cost
    state.last_week_outgoings += base_cost

    progress_gain = progress_base + mech * 0.6
    if state.garage.r_and_d_enabled:
        progress_gain += 2
    if state.r_and_d_focus == "rear_engine_conversion":
        progress_gain -= 1

    state.r_and_d_progress += progress_gain

    # Insight gain chance
    insight_chance = 0.28 + mech * 0.02 + (0.10 if state.garage.r_and_d_enabled else 0.0)
    if time.year <= 1950:
        insight_chance -= 0.05
    elif time.year >= 1958:
        insight_chance += 0.05
    if random.random() < min(0.7, insight_chance):
        state.r_and_d_insight = min(10.0, state.r_and_d_insight + random.uniform(0.6, 1.4))

    if state.r_and_d_progress >= 100.0:
        quality = _rnd_quality_roll(state, state.garage, time)
        _apply_rnd_outcome(state, state.r_and_d_focus, quality)
        state.r_and_d_progress = 0.0


def manage_r_and_d_program(state, time):
    print("\n=== R&D Program ===")

    # Lock non-chassis research in 47-50
    if time.year <= 1950:
        print("R&D is in its infancy. You can only refine the chassis until 1951.")

    status = "ACTIVE" if state.r_and_d_active else "inactive"
    print(f"Current status: {status}")
    print(f"Focus: {state.r_and_d_focus or 'none'}")
    print(f"Progress: {state.r_and_d_progress:.1f}/100")
    print(f"Insight: {state.r_and_d_insight:.1f}/10")

    if state.r_and_d_rear_engine_failed and state.r_and_d_rear_engine_backup:
        print("\n⚠️  Rear-engine conversion failed. You may revert to front-engine layout.")

    print("\n1. Start / Change focus")
    print("2. Toggle program on/off")
    if state.r_and_d_rear_engine_failed and state.r_and_d_rear_engine_backup:
        print("3. Revert rear-engine conversion")
        print("4. Back to Garage menu")
    else:
        print("3. Back to Garage menu")

    choice = input("> ").strip()

    if choice == "1":
        projects = get_available_rnd_projects(time)
        print("\nAvailable R&D focuses:")
        for idx, (_, label) in enumerate(projects, start=1):
            print(f"{idx}. {label}")
        pick = input("> ").strip()
        if pick.isdigit():
            idx = int(pick)
            if 1 <= idx <= len(projects):
                focus = projects[idx - 1][0]
                state.r_and_d_focus = focus
                state.r_and_d_active = True
                state.r_and_d_progress = 0.0
                print(f"\nR&D focus set to: {projects[idx - 1][1]}")
        input("\nPress Enter to return to the Garage menu...")
        return

    if choice == "2":
        state.r_and_d_active = not state.r_and_d_active
        status = "ACTIVE" if state.r_and_d_active else "inactive"
        print(f"\nR&D program is now {status}.")
        input("\nPress Enter to return to the Garage menu...")
        return

    if choice == "3" and state.r_and_d_rear_engine_failed and state.r_and_d_rear_engine_backup:
        backup = state.r_and_d_rear_engine_backup
        if state.current_chassis and state.current_engine:
            state.current_chassis["weight"] = clamp_chassis_weight(backup["weight"])
            state.current_chassis["aero"] = clamp_chassis_aero(backup["aero"])
            state.current_chassis["suspension"] = clamp_chassis_suspension(backup["suspension"])
            state.current_engine["heat_tolerance"] = max(1, min(10, backup["heat_tolerance"]))
        state.r_and_d_rear_engine_failed = False
        state.r_and_d_rear_engine_active = False
        state.r_and_d_rear_engine_backup = None
        print("\nConversion reverted. Your car is back to a front-engine layout.")
        input("\nPress Enter to return to the Garage menu...")
        return

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
            base_cost = int(missing * 4)
            cost_multiplier = state.garage.get_repair_cost_multiplier()
            cost = int(base_cost * cost_multiplier)

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
                    state.last_week_outgoings += cost
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
            base_cost = int(missing * 3)
            cost_multiplier = state.garage.get_repair_cost_multiplier()
            cost = int(base_cost * cost_multiplier)

            print(f"\nChassis overhaul cost: £{cost} to restore from {state.chassis_wear:.0f}% to {cap:.0f}%.")
            confirm = input("Proceed with chassis overhaul? (y/n): ").strip().lower()
            if confirm == "y":
                if cost > state.money:
                    print("You cannot afford this overhaul right now.")
                else:
                    state.money -= cost
                    state.last_week_purchases += cost
                    state.last_week_outgoings += cost
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

def handle_garage_upgrades(state, time):
    """
    Menu for purchasing garage upgrades that provide various benefits.
    """
    from gmr.constants import GARAGE_UPGRADES, get_available_garage_upgrades

    while True:
        print("\n=== Garage Upgrades ===")
        print(f"Current garage level: {state.garage.upgrade_level}")
        print(f"Installed upgrades: {', '.join(state.garage.upgrades) if state.garage.upgrades else 'None'}")

        # Show current benefits
        benefits = calculate_garage_benefits(state.garage)
        print("\nCurrent benefits:")
        if benefits["repair_discount"] > 0:
            print(f"  • {benefits['repair_discount']*100:.0f}% repair cost discount")
        if benefits["repair_speed_bonus"] > 0:
            print(f"  • {benefits['repair_speed_bonus']*100:.0f}% faster repairs")
        if benefits["mechanic_skill_bonus"] > 0:
            print(f"  • +{benefits['mechanic_skill_bonus']} mechanic skill")
        if benefits["r_and_d_enabled"]:
            print("  • Research & Development enabled")

        available_upgrades = get_available_garage_upgrades(state.garage, time.year)

        if not available_upgrades:
            print("\nNo upgrades currently available.")
            print("Check back later as technology advances.")
            input("\nPress Enter to return to the Garage menu...")
            return

        print("\nAvailable upgrades:")
        for i, upgrade_id in enumerate(available_upgrades, 1):
            upgrade = GARAGE_UPGRADES[upgrade_id]
            print(f"{i}. {upgrade['name']} - £{upgrade['cost']}")
            print(f"   {upgrade['description']}")

            # Show benefits
            benefits_text = []
            for benefit_key, benefit_value in upgrade["benefits"].items():
                if benefit_key == "repair_discount":
                    benefits_text.append(f"{benefit_value*100:.0f}% cheaper repairs")
                elif benefit_key == "repair_speed_bonus":
                    benefits_text.append(f"{benefit_value*100:.0f}% faster repairs")
                elif benefit_key == "mechanic_skill_bonus":
                    benefits_text.append(f"+{benefit_value} mechanic skill")
                elif benefit_key == "r_and_d_enabled":
                    benefits_text.append("enables R&D")

            if benefits_text:
                print(f"   Benefits: {', '.join(benefits_text)}")

            # Show requirements
            if upgrade["requirements"]:
                print(f"   Requires: {', '.join(upgrade['requirements'])}")

            print(f"   Available from: {upgrade['year_available']}")
            print()

        print(f"{len(available_upgrades) + 1}. Back to Garage menu")

        choice = input("> ").strip()

        if choice == str(len(available_upgrades) + 1) or choice.lower() == "back":
            break

        try:
            upgrade_index = int(choice) - 1
            if 0 <= upgrade_index < len(available_upgrades):
                upgrade_id = available_upgrades[upgrade_index]
                upgrade = GARAGE_UPGRADES[upgrade_id]

                print(f"\nPurchase {upgrade['name']} for £{upgrade['cost']}?")
                confirm = input("Confirm purchase? (y/n): ").strip().lower()

                if confirm == "y":
                    if state.money >= upgrade["cost"]:
                        state.money -= upgrade["cost"]
                        state.last_week_purchases += upgrade["cost"]
                        state.last_week_outgoings += upgrade["cost"]
                        state.garage.upgrades.append(upgrade_id)

                        # Apply immediate benefits
                        if "r_and_d_enabled" in upgrade["benefits"] and upgrade["benefits"]["r_and_d_enabled"]:
                            state.garage.r_and_d_enabled = True

                        print(f"\nUpgrade purchased! {upgrade['name']} is now active.")
                        state.news.append(f"Garage upgraded: {upgrade['name']} installed, improving facilities.")

                        # Update garage level based on upgrades
                        state.garage.upgrade_level = len(state.garage.upgrades)

                    else:
                        print("You don't have enough money for this upgrade.")
                        input("Press Enter to continue...")
                else:
                    print("Purchase cancelled.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid choice.")

    return
