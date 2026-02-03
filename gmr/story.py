# gmr/story
from gmr.data import engines, chassis_list
from gmr.world_logic import calculate_car_speed
from gmr.data import drivers
import random


# =============================================================================
# FIA WORLD CHAMPIONSHIP ANNOUNCEMENT (End of 1950 / Start of 1951)
# =============================================================================

def maybe_announce_world_championship(state, time):
    """
    At the start of 1951, the FIA announces the first World Championship.
    This is a scripted story event that sets up the 1951 season.
    Triggers when entering 1951 (after demo finishes).
    """
    # Only trigger at start of 1951 (when time.year becomes 1951)
    if time.year != 1951:
        return
    
    # Only trigger once
    if getattr(state, 'seen_championship_announcement', False):
        return
    
    state.seen_championship_announcement = True
    
    # Clear news for dramatic effect
    team_name = state.player_constructor or "your team"
    
    print("\n" + "=" * 70)
    print("  📜 A HISTORIC ANNOUNCEMENT")
    print("=" * 70)
    
    print("""
  Paris, December 1950.

  The letter arrives bearing the seal of the Fédération Internationale
  de l'Automobile. Your hands tremble slightly as you break the wax.

  "To all registered constructors and entrants,

   The FIA is pleased to announce the creation of the WORLD CHAMPIONSHIP
   OF DRIVERS, to commence with the 1951 racing season.

   Seven races shall determine the champion:
   
   • BRITISH GRAND PRIX - Marblethorpe
   • MONACO GRAND PRIX - The streets of Monte Carlo  
   • FRENCH GRAND PRIX - Château-des-Prés
   • UNION 500 - Union Speedway, USA
   • GERMAN GRAND PRIX - Schwarzwald Ring
   • BELGIAN GRAND PRIX - Ardennes Endurance Circuit
   • ITALIAN GRAND PRIX - Vallone
   
   Points shall be awarded: 8-6-4-3-2-1 for the first six finishers.
   The driver with most points at season's end shall be crowned
   WORLD CHAMPION.

   Note regarding the Union 500: Owing to the considerable expense of
   transatlantic passage, the Commission understands that many European
   entrants may be unable to participate. Only well-financed operations
   are expected to make the crossing.

   The age of the gentleman racer draws to a close.
   The era of the World Champion begins.

   Yours faithfully,
   The FIA Sporting Commission"
""")
    
    input("\n  Press Enter to continue...")
    
    print(f"""
  You set down the letter. {team_name}'s cramped workshop feels smaller
  than ever. Outside, winter rain patters against grimy windows.

  A World Championship. Points. A title.
  
  Everything changes now. The privateers, the gentlemen racers, the
  weekend warriors - they'll be measured against the might of Enzoni,
  the precision of the works teams, the ambition of nations.

  Some see opportunity. Others see the beginning of the end.

  Which will it be for {team_name}?
""")
    
    input("  Press Enter to begin the 1951 season...")
    
    # Add to news
    state.news.append("=" * 50)
    state.news.append("🏆 THE FIA WORLD CHAMPIONSHIP BEGINS IN 1951")
    state.news.append("=" * 50)
    state.news.append("Seven races will decide the first World Champion.")
    state.news.append("Points: 8-6-4-3-2-1 for top six finishers.")
    state.news.append("")
    state.news.append("Championship Calendar:")
    state.news.append("  • British GP (Marblethorpe)")
    state.news.append("  • Monaco GP (Monte Carlo) ✨ NEW VENUE")
    state.news.append("  • French GP (Château-des-Prés)")
    state.news.append("  • Union 500 (USA) 🚢 TRANSATLANTIC")
    state.news.append("  • German GP (Schwarzwald Ring)")
    state.news.append("  • Belgian GP (Ardennes)")
    state.news.append("  • Italian GP (Vallone)")
    state.news.append("")
    state.news.append("⚠️ The Union 500 requires expensive transatlantic travel.")
    state.news.append("   Most privateers cannot afford to participate.")


def announce_championship_calendar(state, time):
    """
    Announce the World Championship calendar at the start of each championship year.
    Called from main.py at the start of each year from 1951 onwards.
    """
    from gmr.constants import is_championship_year
    from gmr.calendar import get_world_championship_races
    
    if not is_championship_year(time.year):
        return
    
    # Don't double-announce in 1951 (already handled by maybe_announce_world_championship)
    if time.year == 1951 and getattr(state, 'seen_championship_announcement', False):
        return
    
    champ_races = get_world_championship_races(time.year)
    
    state.news.append("")
    state.news.append("=" * 50)
    state.news.append(f"🏆 {time.year} FIA WORLD CHAMPIONSHIP CALENDAR")
    state.news.append("=" * 50)
    state.news.append("")
    
    for race_name, week, is_transatlantic in champ_races:
        marker = " 🚢" if is_transatlantic else ""
        state.news.append(f"  • Week {week}: {race_name}{marker}")
    
    state.news.append("")
    state.news.append("Points: 8-6-4-3-2-1 for top six finishers.")
    state.news.append("All constructors are expected to attend championship races!")
    if any(t[2] for t in champ_races):  # If any transatlantic races
        state.news.append("⚠️ Transatlantic races have limited European participation.")


def inject_demo_prologue(state, time):
    """
    One-shot opening story beat for the demo.
    Adds a few news items the first time the game starts.
    """
    if state.seen_prologue:
        return

    team_name = state.player_constructor or "your team"

    state.news.append(
        "An uncle’s garage. A borrowed spanner set. "
        "A car held together by wire and optimism."
    )
    state.news.append(
        "It is 1947. Motorsport has no real rules and barely has roads."
    )
    state.news.append(
        f"You inherit your father’s Harper Type-1 and a dusty shed – the birth of {team_name}."
    )
    state.news.append(
        "Across Europe, marques like Enzoni begin to wake up. "
        "Their new V12 monsters loom over the privateer scene."
    )
    state.news.append(
        "No championships. No officials. No safety barriers. "
        "Just whoever shows up, races hard, and makes it home in one piece."
    )
    state.news.append(
        "Survive the chaos, earn a name, and prove your garage belongs on the grid."
    )

    state.seen_prologue = True


    # FIXED: no stray ']'
    starting_engine = next(e for e in engines if e["id"] == "dad_old")
    state.current_engine = starting_engine

    # Starting chassis: inherited frame
    starting_chassis = next(c for c in chassis_list if c["id"] == "dad_chassis")
    state.current_chassis = starting_chassis

    # Dad's old chassis is already well used
    state.chassis_wear = 70.0   # 70% condition to start with
    # Engine starts mechanically "refreshed" for now
    state.engine_wear = 100.0
    state.engine_max_condition = 100.0


    # Combine into initial car stats
    state.car_speed = calculate_car_speed(starting_engine, starting_chassis)
    state.car_reliability = starting_engine["reliability"]

    # Player driver is None for now
    state.player_driver = None

    print(f"\nWelcome to {state.player_constructor}! Your journey begins...\n")

def pick_demo_finale_victim(state):
    """
    Choose which driver dies in the scripted demo finale.

    Primary rule for the demo:
    - It should feel like an 'Ascari moment' – a star Enzoni works driver
      paying the ultimate price at a brutal circuit.

    So:
      1) Prefer the highest-fame Enzoni driver (works team)
      2) If none exist (edge case), fall back to the most famous driver in the pool
      3) If absolutely nobody exists, return None
    """
    # 1) Look for Enzoni works drivers first
    enzoni_drivers = [d for d in drivers if d.get("constructor") == "Enzoni"]
    if enzoni_drivers:
        return max(enzoni_drivers, key=lambda d: d.get("fame", 0))

    # 2) Fallback: no Enzoni drivers? Use global fame instead
    if drivers:
        return max(drivers, key=lambda d: d.get("fame", 0))

    # 3) Last resort: nothing to kill
    return None

def maybe_trigger_demo_finale(state, time, race_name):
    """
    Scripted end-of-demo event:
    After the 1950 Ardennes Endurance GP, a fatal crash forces the sport to change.

    IMPORTANT:
    - This function now RETURNS the victim driver dict if it triggers.
    - It does NOT remove them from driver lists or alter classification.
      Race code must apply the DNF / removal from results.
    """
    # Already done? Don't fire twice.
    if getattr(state, "demo_driver_death_done", False) or getattr(state, "demo_complete", False):
        return None

    from gmr.constants import DEV_BYPASS_DEMO

    # Only trigger at Ardennes in 1950
    if time.year != 1950:
        return None
    if race_name != "Ardennes Endurance GP":
        return None

    victim = pick_demo_finale_victim(state)
    if victim is None:
        return None

    name = victim["name"]
    ctor = victim.get("constructor", "Unknown")

    state.news.append(f"Tragedy at Ardennes. {name} ({ctor}) leaves the road at Les Rivieres.")
    state.news.append(
        "Marshals and mechanics scramble through the smoke and twisted guardrail, "
        "but there is nothing to be done."
    )
    state.news.append(
        f"{name} is killed instantly. The paddock falls silent; even the loudest voices "
        "struggle to find words."
    )
    state.news.append(
        "In taverns and boardrooms across Europe, team owners and organisers finally admit "
        "the sport cannot go on like this."
    )
    state.news.append(
        "Talk begins of a unified governing body, safer circuits, and – at last – "
        "a true international championship."
    )
    state.news.append(
        "Your era was the age before rules. Whatever comes next will be built on "
        "the courage and the blood of drivers like this."
    )
    
    # Mark death as done
    state.demo_driver_death_done = True
    
    # Only end the demo if bypass is off
    if not DEV_BYPASS_DEMO:
        state.news.append(
            "DEMO COMPLETE – You have survived the chaos years leading up to organised Grand Prix racing."
        )
        state.demo_complete = True
    else:
        state.news.append(
            "The racing world mourns, but the calendar moves on. The FIA will soon announce their response."
        )

    return victim

def take_emergency_loan(state, time, min_amount=500, max_amount=2000):
    """
    Give the player a simple way to take on high-interest debt.
    Returns True if a loan was taken, False otherwise.
    """
    if state.loan_balance > 0:
        print("\nYou already owe money to a lender. No one will extend you more credit right now.")
        input("\nPress Enter to continue...")
        return False

    print("\n--- Emergency Loan ---")
    print("A local industrial lender is willing to extend you a short-term loan.")
    print(f"You may borrow between £{min_amount} and £{max_amount}.")
    print("Weekly interest will be between 5% and 10%, and they expect you to")
    print("have things settled by the end of this season.")

    while True:
        amount_str = input(f"\nHow much do you want to borrow? (or press Enter to cancel): ").strip()
        if amount_str == "":
            print("You decide against taking on new debt for now.")
            return False

        if not amount_str.isdigit():
            print("Please enter a whole number.")
            continue

        amount = int(amount_str)
        if amount < min_amount or amount > max_amount:
            print(f"Please choose an amount between £{min_amount} and £{max_amount}.")
            continue

        break

    # Lock in the loan
    state.loan_balance = amount
    state.loan_interest_rate = random.uniform(0.03, 0.10)
    state.loan_due_year = time.year
    state.loan_lender_name = "Marblethorpe Industrial Finance"

    state.money += amount
    state.last_week_income += amount  # shows up as 'Other' income

    rate_pct = int(state.loan_interest_rate * 100)
    print(f"\nYou sign a rough-looking contract for £{amount} at {rate_pct}% weekly interest.")
    print("It'll keep the doors open – for now.")

    team_name = state.player_constructor or "Your team"
    state.news.append(
        f"{team_name} take an emergency loan of £{amount} at {rate_pct}% weekly interest."
    )

    input("\nPress Enter to continue...")
    return True

def handle_bankruptcy_rescue(state, time):
    """
    Called when funds drop below -1000.
    Offer a last-ditch rescue: sell engine or take a loan.
    Returns True if the team survives, False if we should trigger full bankruptcy.
    """
    if state.bankruptcy_offered:
        # Don't loop this endlessly
        return False

    state.bankruptcy_offered = True

    print("\n💥 Financial Crisis 💥")
    print("Your books are deep in the red. Without drastic action, the team will fold.")
    print(f"Current balance: £{state.money}")

    # Check what we can offer
    can_sell_engine = state.current_engine is not None and state.current_engine["price"] > 0

    print("\nYou have a few desperate options:")
    option_map = {}

    opt_num = 1
    if can_sell_engine:
        print(f"{opt_num}. Sell your current engine (raise emergency cash, but lose the unit).")
        option_map[str(opt_num)] = "sell_engine"
        opt_num += 1

    print(f"{opt_num}. Take an emergency high-interest loan.")
    option_map[str(opt_num)] = "loan"
    opt_num += 1

    print(f"{opt_num}. Do nothing and accept bankruptcy.")
    option_map[str(opt_num)] = "accept"

    while True:
        choice = input("\nChoose an option: ").strip()
        if choice in option_map:
            action = option_map[choice]
            break
        else:
            print("Please choose one of the listed options.")

    if action == "sell_engine":
        eng = state.current_engine
        resale = int(eng["price"] * 0.6)  # you won't get full value in a fire-sale

        print(f"\nYou sell the {eng['name']} at a painful discount, raising £{resale}.")
        state.money += resale
        state.last_week_income += resale
        state.news.append(
            f"{state.player_constructor or 'Your team'} sell their {eng['name']} "
            f"to stay afloat financially."
        )

        # Remove engine from car
        state.current_engine = None
        state.car_speed = 0
        state.car_reliability = 0
        state.engine_wear = 0
        state.engine_health = 0

        # Small prestige hit – everyone sees you're on your knees
        state.prestige = max(0.0, state.prestige - 0.5)

    elif action == "loan":
        took_loan = take_emergency_loan(state, time)
        if not took_loan:
            # Player backed out – treat as no rescue
            return False

    else:  # accept bankruptcy
        print("\nYou allow the numbers to speak for themselves. The team collapses.")
        return False

    # After the chosen action, see if we're still catastrophically negative
    if state.money < -1000:
        print("\nEven after desperate measures, the debts are too deep.")
        return False

    # We survived – clear the rescue flag so a future crisis can trigger again
    state.bankruptcy_offered = False
    return True