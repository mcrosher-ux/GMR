# gmr/finances.py

def show_finances(state):
    garage = state.garage
    staff_cost = garage.staff_count * garage.staff_salary

    print("\n=== Finances ===")
    print("Weekly Outgoings:")
    print(f"  Base garage cost: £{garage.base_cost}")
    print(f"  Staff cost ({garage.staff_count} staff): £{staff_cost}")
    if state.last_week_driver_pay > 0:
        print(f"  Driver pay (race fees): £{state.last_week_driver_pay}")
    if state.last_week_purchases > 0:
        print(f"  One-off purchases (engines/parts/PR/tests): £{state.last_week_purchases}")
    if state.last_week_rnd > 0:
        print(f"  Chassis development (R&D): £{state.last_week_rnd}")
    if getattr(state, "last_week_travel_cost", 0) > 0:
        print(f"  Travel & logistics: £{state.last_week_travel_cost}")
    if state.last_week_loan_interest > 0:
        print(f"  Loan interest: £{state.last_week_loan_interest}")

    total_outgoings = (
        garage.base_cost
        + staff_cost
        + state.last_week_driver_pay
        + state.last_week_purchases
        + state.last_week_rnd
        + getattr(state, "last_week_travel_cost", 0)
        + state.last_week_loan_interest
    )


    print(f"Total Outgoings this week: £{total_outgoings}")

    print("\nIncome this week:")
    if state.last_week_prize_income > 0:
        print(f"  Prize money: £{state.last_week_prize_income}")
    if getattr(state, "last_week_appearance_income", 0) > 0:
        print(f"  Appearance money: £{state.last_week_appearance_income}")
    if state.last_week_sponsor_income > 0:
        print(f"  Sponsorship: £{state.last_week_sponsor_income}")
    other_income = state.last_week_income - (
        state.last_week_prize_income
        + state.last_week_sponsor_income
        + getattr(state, "last_week_appearance_income", 0)
    )

    if other_income > 0:
        print(f"  Other: £{other_income}")
    print(f"Total Income this week: £{state.last_week_income}")

    print(f"\nTotal Money: £{state.money}")
    print(f"Cumulative Constructor Earnings: £{state.constructor_earnings}")
    print(f"Team Prestige: {state.prestige:.1f}")

    if state.loan_balance > 0:
        rate_pct = int(state.loan_interest_rate * 100)
        print(f"\nOutstanding Loan: £{state.loan_balance} at {rate_pct}% weekly interest.")
        if state.loan_due_year:
            print(f"Loan expected to be settled by the end of the {state.loan_due_year} season.")
