#gmr/business.py
import random

from gmr.constants import CHAMPIONSHIP_ACTIVE

def show_business(state, time):
    while True:
        print("\n=== Business & Contracts ===")

        # PR / networking availability
        if can_do_pr_trip(state, time):
            print("   (You could schedule a sponsor PR/networking trip now – option 2)")
        else:
            weeks_since = time.absolute_week - state.last_pr_abs_week
            weeks_until = max(0, 12 - weeks_since)
            print(f"   (Next worthwhile PR window in about {weeks_until} week(s))")

        # Prestige summary
        print(f"\nTeam Prestige: {state.prestige:.1f}/100")

        if state.prestige < 5:
            print("  You're an unknown privateer; only small-time sponsors are watching.")
        elif state.prestige < 20:
            print("  The paddock has started to notice your efforts.")
        elif state.prestige < 40:
            print("  You're a respected midfield outfit – offers are getting better.")
        elif state.prestige < 70:
            print("  A front-line team with growing pull in the paddock.")
        else:
            print("  A legendary name – sponsors and drivers line up to talk to you.")

        print("\n1. Review current sponsorship & driver contract")
        print("2. Do sponsor PR / networking trip")
        print("3. Back to main menu")

        choice = input("> ").strip()

        if choice in ("1", ""):
            # --- Sponsorship ---
            print("\nSponsorship:")
            if state.sponsor_active:
                print(f"  Active sponsor: {state.sponsor_name}")
                print(f"  Deal runs until end of {state.sponsor_end_year}")
                print(f"  Races started under this deal: {state.sponsor_races_started}")
                print(f"  Podiums under this deal: {state.sponsor_podiums}")

                # PATCH 5: show current, multiplier-adjusted terms
                base_appearance = 60
                base_point_rate = 10
                base_podium_bonus = 120
                mult = getattr(state, "sponsor_rate_multiplier", 1.0)

                appearance_now = int(base_appearance * mult)
                point_rate_now = int(base_point_rate * mult)
                podium_now = int(base_podium_bonus * mult)

                print("  Terms:")
                print("    • £2000 signing bonus (already paid)")
                print(f"    • £{appearance_now} per race started")
                if CHAMPIONSHIP_ACTIVE:
                    print(f"    • £{point_rate_now} per championship point")
                else:
                    print("    • (No championship points in this era)")
                print(f"    • £{podium_now} per podium")

                if mult > 1.0:
                    print(f"      (rates boosted by recent advertising work, x{mult:.2f})")

                print("  Goals:")
                print("    • Start at least 3 races")
                print("    • Achieve at least 1 podium by the end of the contract")

            else:
                if state.sponsor_seen_offer:
                    print("  No active sponsor at the moment.")
                    print("  Gallant Leaf previously made an offer; that deal is no longer on the table.")
                else:
                    print("  You have no sponsors yet.")
                    print("  Perform well and keep an eye out for offers after major events.")

            # --- Driver contract ---
            print("\nDriver Contract:")
            if state.player_driver:
                d = state.player_driver
                print(f"  Driver: {d['name']}")
                print(f"  Contract type: Fixed race deal")
                print(f"  Races remaining on contract: {state.driver_contract_races}")
                print(f"  Pay per race: £{state.driver_pay}")
                print("  Notes:")
                print("    • Contract automatically ends when the race count hits zero.")
                print("    • Future versions may allow buyouts or handshake deals.")
            else:
                print("  No driver currently under contract.")

            input("\nPress Enter to return to the Business menu...")

        elif choice == "2":
            handle_pr_trip(state, time)

        elif choice == "3":
            break

        else:
            print("Invalid choice.")

def can_do_pr_trip(state, time):
    """
    You can only really 'work the room' with sponsors every few months.
    """
    if state.last_pr_abs_week == 0:
        return True
    return (time.absolute_week - state.last_pr_abs_week) >= 12  # ~3 months


def handle_pr_trip(state, time):
    """
    Spend money and time to go charm potential sponsors.
    Small prestige bump, stronger if you've been scoring points.
    """
    print("\n=== Sponsor Courtship & PR ===")

    if not can_do_pr_trip(state, time):
        print("You've already spent time courting sponsors recently.")
        print("It'll be a while before another trip feels worthwhile.")
        input("\nPress Enter to return to the Business menu...")
        return

    PR_COST = 80

    print("You spend a few days writing letters, visiting factories and")
    print("buying lunches for anyone who might back a racing team.")
    print(f"It'll cost about £{PR_COST} in travel, hotels and lost workshop time.")
    print("\nProceed with this PR push? (y/n)")

    choice = input("> ").strip().lower()
    if choice != "y":
        print("You decide to stay in the workshop instead.")
        input("\nPress Enter to return to the Business menu...")
        return

    if state.money < PR_COST:
        print("\nYou simply can't afford to wine and dine anyone right now.")
        input("\nPress Enter to return to the Business menu...")
        return

    # Pay and log
    state.money -= PR_COST
    state.last_week_purchases += PR_COST
    state.last_pr_abs_week = time.absolute_week

    # Prestige boost with some swing
    base_boost = random.uniform(0.6, 1.4)

    # Slightly better returns if you've been scoring points
    points_total = sum(state.points.values())
    if points_total > 0:
        base_boost *= 1.0 + min(points_total, 10) * 0.03

    before = state.prestige
    state.prestige = max(0.0, min(100.0, state.prestige + base_boost))

    team_name = state.player_constructor or "Your team"
    state.news.append(
        f"{team_name} conduct a round of sponsor meetings and PR work "
        f"(prestige {before:.1f} → {state.prestige:.1f})."
    )

    input("\nPress Enter to return to the Business menu...")

