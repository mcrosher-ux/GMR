# gmr/ui_world.py
# UI for viewing world economy, country reports, and global events

from gmr.world_economy import COUNTRIES, REGIONAL_EVENTS, WorldEconomy
from gmr.data import tracks


def show_world_economy(state, time):
    """Main world economy menu."""
    while True:
        print("\n" + "=" * 60)
        print("  🌍 WORLD NEWS & ECONOMY")
        print("=" * 60)
        
        # Show active events summary
        if hasattr(state, 'world_economy'):
            economy = state.world_economy
            
            if economy.active_events:
                print("\n📰 ACTIVE WORLD EVENTS:")
                for event_data in economy.active_events[:5]:
                    event = event_data["event"]
                    scope = event_data["scope"]
                    weeks = event_data["weeks_remaining"]
                    
                    # Indicator for positive/negative
                    if event.get("economy_modifier", 1.0) > 1.0 or event.get("attendance_modifier", 1.0) > 1.0:
                        indicator = "📈"
                    elif event.get("economy_modifier", 1.0) < 1.0 or event.get("attendance_modifier", 1.0) < 1.0:
                        indicator = "📉"
                    else:
                        indicator = "📊"
                    
                    print(f"  {indicator} {event['name']} ({scope})")
                    print(f"      {event['description']}")
                    print(f"      ⏱️ {weeks} weeks remaining")
            else:
                print("\n📰 No major world events affecting the racing calendar.")
        
        print("\n" + "-" * 40)
        print("1. View Country Reports")
        print("2. View Track Economies")
        print("3. Attendance History")
        print("4. Back to Main Menu")
        
        choice = input("> ").strip()
        
        if choice == "1":
            show_country_selector(state)
        elif choice == "2":
            show_track_economies(state)
        elif choice == "3":
            show_attendance_history(state)
        elif choice == "4":
            break
        else:
            print("Invalid choice.")


def show_country_selector(state):
    """Show list of countries to get detailed reports."""
    print("\n" + "=" * 60)
    print("  🗺️ COUNTRY REPORTS")
    print("=" * 60)
    
    # Group countries by region
    regions = {}
    for name, data in COUNTRIES.items():
        region = data.get("region", "Other")
        if region not in regions:
            regions[region] = []
        regions[region].append(name)
    
    # Build numbered list
    country_list = []
    for region in sorted(regions.keys()):
        print(f"\n  {region}:")
        for country in sorted(regions[region]):
            country_list.append(country)
            idx = len(country_list)
            
            # Get current economy if available
            econ_str = ""
            if hasattr(state, 'world_economy'):
                econ = state.world_economy.get_current_economy(country)
                econ_str = f" [Economy: {'★' * int(econ)}]"
            
            print(f"    {idx}. {country}{econ_str}")
    
    print(f"\n    {len(country_list) + 1}. Back")
    
    try:
        choice = int(input("> ").strip())
        if 1 <= choice <= len(country_list):
            show_country_detail(state, country_list[choice - 1])
    except ValueError:
        pass


def show_country_detail(state, country_name):
    """Show detailed report for a specific country."""
    country = COUNTRIES.get(country_name)
    if not country:
        print(f"Unknown country: {country_name}")
        return
    
    print("\n" + "=" * 60)
    print(f"  🏴 {country['name'].upper()}")
    print("=" * 60)
    
    print(f"\n  Region: {country['region']}")
    print(f"  Population: {country['population_millions']}M")
    
    # Economy stats
    base_econ = country['base_economy']
    if hasattr(state, 'world_economy'):
        current_econ = state.world_economy.get_current_economy(country_name)
        attendance_mod = state.world_economy.get_attendance_modifier(country_name)
    else:
        current_econ = base_econ
        attendance_mod = 1.0
    
    print(f"\n  📊 ECONOMIC INDICATORS:")
    print(f"     Base Economy:        {'★' * base_econ}{'☆' * (10 - base_econ)} ({base_econ}/10)")
    print(f"     Current Economy:     {'★' * int(current_econ)}{'☆' * (10 - int(current_econ))} ({current_econ:.1f}/10)")
    print(f"     Political Stability: {'★' * country['political_stability']}{'☆' * (10 - country['political_stability'])} ({country['political_stability']}/10)")
    print(f"     Industrial Strength: {'★' * country['industrial_strength']}{'☆' * (10 - country['industrial_strength'])} ({country['industrial_strength']}/10)")
    
    print(f"\n  🏎️ MOTORSPORT FACTORS:")
    print(f"     Racing Culture:      {'★' * country['motorsport_culture']}{'☆' * (10 - country['motorsport_culture'])} ({country['motorsport_culture']}/10)")
    print(f"     Wealth Distribution: {country['wealth_distribution']:.0%} can afford tickets")
    print(f"     Current Attendance:  {attendance_mod:.0%} of normal")
    
    # Tracks in this country
    country_tracks = [name for name, data in tracks.items() if data.get("country") == country_name]
    if country_tracks:
        print(f"\n  🏁 RACING CIRCUITS:")
        for track_name in country_tracks:
            track = tracks[track_name]
            fame_mult = track.get("fame_mult", 1.0)
            prestige_label = "★★★" if fame_mult >= 1.5 else "★★" if fame_mult >= 1.0 else "★"
            print(f"     • {track_name} {prestige_label}")
    
    # Active events affecting this country
    if hasattr(state, 'world_economy'):
        region = country["region"]
        affecting = [
            e for e in state.world_economy.active_events
            if e["scope"] == "global" or e["scope"] == region or e["scope"] == country_name
        ]
        if affecting:
            print(f"\n  📰 ACTIVE EVENTS:")
            for e in affecting:
                effect = ""
                if e["event"].get("economy_modifier", 1.0) != 1.0:
                    effect += f" Econ: {e['event']['economy_modifier']:.0%}"
                if e["event"].get("attendance_modifier", 1.0) != 1.0:
                    effect += f" Attend: {e['event']['attendance_modifier']:.0%}"
                print(f"     • {e['event']['name']} ({e['weeks_remaining']}w){effect}")
    
    # Flavor text
    print(f"\n  \"{country['flavor']}\"")
    
    input("\n  Press Enter to continue...")


def show_track_economies(state):
    """Show economic overview for all tracks."""
    print("\n" + "=" * 60)
    print("  🏁 TRACK ECONOMIC OVERVIEW")
    print("=" * 60)
    
    print(f"\n  {'Track':<30} {'Country':<15} {'Economy':<10} {'Attendance':<10}")
    print("  " + "-" * 65)
    
    for track_name, track_data in tracks.items():
        country_name = track_data.get("country", "Unknown")
        
        if hasattr(state, 'world_economy'):
            econ = state.world_economy.get_current_economy(country_name)
            attend = state.world_economy.get_attendance_modifier(country_name)
            econ_str = f"{'★' * int(econ)}"
            attend_str = f"{attend:.0%}"
        else:
            econ_str = "N/A"
            attend_str = "N/A"
        
        print(f"  {track_name:<30} {country_name:<15} {econ_str:<10} {attend_str:<10}")
    
    input("\n  Press Enter to continue...")


def show_attendance_history(state):
    """Show historical attendance at races."""
    print("\n" + "=" * 60)
    print("  📊 RACE ATTENDANCE HISTORY")
    print("=" * 60)
    
    if not hasattr(state, 'world_economy') or not state.world_economy.attendance_history:
        print("\n  No race attendance data recorded yet.")
        input("\n  Press Enter to continue...")
        return
    
    history = state.world_economy.attendance_history
    
    print(f"\n  {'Track':<30} {'Races':<8} {'Average':<12} {'Best':<12}")
    print("  " + "-" * 62)
    
    for track_name, attendances in history.items():
        if attendances:
            avg = sum(attendances) / len(attendances)
            best = max(attendances)
            print(f"  {track_name:<30} {len(attendances):<8} {avg:>10,.0f}  {best:>10,.0f}")
    
    # Total stats
    all_attendances = [a for attendances in history.values() for a in attendances]
    if all_attendances:
        print("\n  " + "-" * 62)
        total_avg = sum(all_attendances) / len(all_attendances)
        total_best = max(all_attendances)
        print(f"  {'OVERALL':<30} {len(all_attendances):<8} {total_avg:>10,.0f}  {total_best:>10,.0f}")
    
    input("\n  Press Enter to continue...")


def format_economy_indicator(value, max_val=10):
    """Format an economy value as a star rating."""
    filled = int(value)
    empty = max_val - filled
    return '★' * filled + '☆' * empty
