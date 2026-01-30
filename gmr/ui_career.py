# gmr/ui_career.py
"""
Player career management: personal stats, company transitions, retirement.
"""

import random


def show_career_menu(state, time):
    """Main career management menu."""
    while True:
        player = state.player_character
        age = player.get_age(time.year)
        title = player.get_title(time.year)
        
        print("\n" + "="*60)
        print(f"  CAREER: {title} {player.name}")
        print("="*60)
        
        # Personal info
        print(f"\n  Age: {age} (born {player.birth_year})")
        print(f"  Home country: {player.home_country}")
        print(f"  Personal savings: £{player.personal_savings:,}")
        
        # Current role
        print(f"\n  Current role: {player.current_role.title()}")
        if state.player_constructor:
            print(f"  Company: {state.player_constructor}")
            print(f"  Company funds: £{state.money:,}")
        
        # Career stats
        print(f"\n  Career Statistics:")
        print(f"    Races managed: {player.career_races}")
        print(f"    Career wins: {player.career_wins}")
        print(f"    Career podiums: {player.career_podiums}")
        print(f"    Companies founded: {len(player.companies_founded)}")
        
        # Personal stats
        print(f"\n  Personal Attributes:")
        print(f"    Business acumen: {player.business_acumen}/10")
        print(f"    Technical knowledge: {player.technical_knowledge}/10")
        print(f"    Reputation: {player.reputation}/10")
        if age >= 70:
            print(f"    Health: {player.health}/10")
        
        # Menu options
        print("\n  Options:")
        print("  1. Transfer money (personal ↔ company)")
        print("  2. Leave current company")
        print("  3. Found a new company")
        print("  4. Back to main menu")
        
        choice = input("\n> ").strip()
        
        if choice == "1":
            transfer_money_menu(state, time)
        elif choice == "2":
            leave_company_menu(state, time)
        elif choice == "3":
            found_new_company_menu(state, time)
        elif choice == "4" or choice == "":
            return
        else:
            print("Invalid choice.")


def transfer_money_menu(state, time):
    """Transfer money between personal savings and company."""
    player = state.player_character
    
    print("\n" + "-"*40)
    print("  MONEY TRANSFER")
    print("-"*40)
    print(f"\n  Personal savings: £{player.personal_savings:,}")
    print(f"  Company funds: £{state.money:,}")
    
    print("\n  1. Invest personal savings into company")
    print("  2. Take dividend from company")
    print("  3. Cancel")
    
    choice = input("\n> ").strip()
    
    if choice == "1":
        if player.personal_savings <= 0:
            print("\n  You have no personal savings to invest.")
            input("\n  Press Enter to continue...")
            return
        
        max_invest = player.personal_savings
        print(f"\n  How much to invest? (max £{max_invest:,})")
        try:
            amount = int(input("  Amount: £").strip())
            if amount <= 0:
                print("  Cancelled.")
            elif amount > max_invest:
                print("  You don't have that much.")
            else:
                player.personal_savings -= amount
                state.money += amount
                print(f"\n  ✓ Invested £{amount:,} into {state.player_constructor}.")
                state.news.append(f"{player.name} invests £{amount:,} of personal funds into {state.player_constructor}.")
        except ValueError:
            print("  Invalid amount.")
    
    elif choice == "2":
        if state.money <= 0:
            print("\n  The company has no funds to distribute.")
            input("\n  Press Enter to continue...")
            return
        
        # Can only take a dividend if company is profitable
        max_dividend = max(0, state.money - 1000)  # Leave at least £1000 in company
        if max_dividend <= 0:
            print("\n  Company needs at least £1000 in reserves.")
            print("  Cannot take a dividend right now.")
            input("\n  Press Enter to continue...")
            return
        
        print(f"\n  How much dividend to take? (max £{max_dividend:,})")
        print("  (Company will retain at least £1000)")
        try:
            amount = int(input("  Amount: £").strip())
            if amount <= 0:
                print("  Cancelled.")
            elif amount > max_dividend:
                print("  That would leave the company with insufficient reserves.")
            else:
                state.money -= amount
                player.personal_savings += amount
                print(f"\n  ✓ Took £{amount:,} dividend from {state.player_constructor}.")
                state.news.append(f"{player.name} takes a £{amount:,} dividend from {state.player_constructor}.")
        except ValueError:
            print("  Invalid amount.")
    
    input("\n  Press Enter to continue...")


def leave_company_menu(state, time):
    """Leave the current company - AI takes over or it folds."""
    player = state.player_character
    
    if not state.player_constructor:
        print("\n  You're not currently running a company.")
        input("\n  Press Enter to continue...")
        return
    
    company_name = state.player_constructor
    
    print("\n" + "-"*40)
    print(f"  LEAVE {company_name.upper()}?")
    print("-"*40)
    
    # Assess what will happen to the company
    can_survive = state.money >= 2000 and state.sponsor_active and state.prestige >= 10
    
    print(f"\n  Company funds: £{state.money:,}")
    print(f"  Active sponsor: {'Yes' if state.sponsor_active else 'No'}")
    print(f"  Prestige: {state.prestige:.1f}")
    
    if can_survive:
        print(f"\n  If you leave, {company_name} has enough resources to continue.")
        print("  A new manager will be found to run the team.")
    else:
        print(f"\n  ⚠️ WARNING: {company_name} cannot survive without you!")
        reasons = []
        if state.money < 2000:
            reasons.append("insufficient funds")
        if not state.sponsor_active:
            reasons.append("no sponsorship")
        if state.prestige < 10:
            reasons.append("low prestige")
        print(f"  Reasons: {', '.join(reasons)}")
        print("  The company will FOLD if you leave.")
    
    print(f"\n  Your personal savings: £{player.personal_savings:,}")
    print("  You will keep your personal savings if you leave.")
    
    confirm = input(f"\n  Are you sure you want to leave {company_name}? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("  You decide to stay.")
        input("\n  Press Enter to continue...")
        return
    
    # Process the departure
    if can_survive:
        # Company survives with AI manager
        ai_manager = generate_ai_manager_name()
        state.news.append(f"📰 {player.name} steps down from {company_name}.")
        state.news.append(f"📰 {ai_manager} appointed as new team principal of {company_name}.")
        print(f"\n  You step down from {company_name}.")
        print(f"  {ai_manager} takes over as team principal.")
    else:
        # Company folds
        state.news.append(f"📰 {player.name} steps down from {company_name}.")
        state.news.append(f"📰 {company_name} ceases operations due to financial difficulties.")
        print(f"\n  You step down from {company_name}.")
        print(f"  Without leadership and resources, {company_name} closes its doors.")
        
        # Release the driver
        if state.player_driver:
            driver_name = state.player_driver.get("name", "The driver")
            state.news.append(f"📰 {driver_name} is released and joins the free agent pool.")
            state.player_driver = None
    
    # Clear company association
    state.player_constructor = None
    state.is_player_owned = False
    player.current_role = "unemployed"
    player.years_in_current_role = 0
    
    # Reset company-specific stuff (keep player character intact)
    state.sponsor_active = False
    state.sponsor_name = None
    
    print("\n  You are now unemployed.")
    print("  You can found a new company from the Career menu.")
    
    input("\n  Press Enter to continue...")


def found_new_company_menu(state, time):
    """Found a new racing company."""
    player = state.player_character
    
    if state.player_constructor:
        print(f"\n  You already run {state.player_constructor}.")
        print("  Leave your current company first before starting a new one.")
        input("\n  Press Enter to continue...")
        return
    
    print("\n" + "-"*40)
    print("  FOUND A NEW RACING COMPANY")
    print("-"*40)
    
    # Cost to start a new company
    startup_cost = 3000
    minimum_capital = 5000  # Need this much to have a viable company
    total_needed = startup_cost + minimum_capital
    
    print(f"\n  Starting a new racing operation requires:")
    print(f"    Startup costs (permits, equipment): £{startup_cost:,}")
    print(f"    Minimum operating capital: £{minimum_capital:,}")
    print(f"    Total needed: £{total_needed:,}")
    
    print(f"\n  Your personal savings: £{player.personal_savings:,}")
    
    if player.personal_savings < total_needed:
        shortfall = total_needed - player.personal_savings
        print(f"\n  ❌ You need £{shortfall:,} more to start a new company.")
        print("  Build up your savings by working or investing wisely.")
        input("\n  Press Enter to continue...")
        return
    
    print(f"\n  You have enough funds to start fresh!")
    
    company_name = input("\n  Enter the name of your new racing company: ").strip()
    if not company_name:
        company_name = f"{player.name.split()[0]} Racing" if " " in player.name else f"{player.name} Racing"
    
    while True:
        country = input("  What country will the team be based in? ").strip()
        if country:
            from main import normalise_country_name
            country = normalise_country_name(country)
            break
        print("  Please enter a country name.")
    
    confirm = input(f"\n  Found '{company_name}' based in {country}? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("  Company founding cancelled.")
        input("\n  Press Enter to continue...")
        return
    
    # Deduct costs from personal savings
    player.personal_savings -= startup_cost
    
    # Set up the new company
    state.player_constructor = company_name
    state.country = country
    state.money = minimum_capital  # Transfer from personal savings
    player.personal_savings -= minimum_capital
    
    state.company_founder = player.name
    state.company_founded_year = time.year
    state.is_player_owned = True
    
    # Reset company state
    state.prestige = max(2.0, player.reputation * 0.5)  # Some prestige from personal reputation
    state.sponsor_active = False
    state.sponsor_name = None
    state.player_driver = None
    state.driver_contract_races = 0
    
    # Reset garage to basic
    state.garage.level = 0
    state.garage.base_cost = 25
    state.garage.staff_count = 1
    state.garage.staff_salary = 10
    state.garage.upgrade_level = 0
    state.garage.upgrades = []
    
    # Reset car (no equipment yet)
    state.current_engine = None
    state.current_chassis = None
    state.car_name = None
    state.engine_wear = 100.0
    state.chassis_wear = 100.0
    state.tyre_sets = 1
    
    # Update player career
    player.companies_founded.append(company_name)
    player.companies_managed.append(company_name)
    player.current_role = "owner"
    player.years_in_current_role = 0
    
    # Reset team-specific career stats
    state.races_entered_with_team = 0
    state.wins_with_team = 0
    state.podiums_with_team = 0
    state.points_with_team = 0
    
    state.news.append(f"📰 {player.name} founds new racing team: {company_name}!")
    state.news.append(f"📰 {company_name} is based in {country} and enters the racing world.")
    
    print(f"\n  ✓ {company_name} has been founded!")
    print(f"  Based in {country}. Starting funds: £{state.money:,}")
    print("\n  You'll need to:")
    print("    • Buy an engine and chassis")
    print("    • Hire a driver")
    print("    • Find sponsors")
    print("  Good luck!")
    
    input("\n  Press Enter to continue...")


def generate_ai_manager_name():
    """Generate a random AI manager name."""
    first_names = [
        "Alberto", "Bernard", "Charles", "David", "Eduardo",
        "Franco", "Giorgio", "Hans", "Ivan", "Jacques",
        "Klaus", "Lorenzo", "Marcel", "Nigel", "Oscar",
        "Pierre", "Roberto", "Stefan", "Thomas", "Victor"
    ]
    last_names = [
        "Aldini", "Beaumont", "Castellani", "Dietrich", "Eriksson",
        "Fontaine", "Gruber", "Hoffmann", "Jensen", "Kowalski",
        "Laurent", "Moretti", "Nielsen", "Oliveira", "Petrov",
        "Richter", "Svensson", "Tanaka", "Vogel", "Weber"
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def show_player_status_brief(state, time):
    """Show a brief player status for the main menu header."""
    player = state.player_character
    age = player.get_age(time.year)
    title = player.get_title(time.year)
    
    lines = []
    lines.append(f"{title} {player.name}, age {age}")
    
    if state.player_constructor:
        lines.append(f"Running: {state.player_constructor}")
    else:
        lines.append("Currently unemployed")
    
    return " | ".join(lines)
