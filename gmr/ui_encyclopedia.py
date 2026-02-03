# gmr/ui_encyclopedia.py
# UI for viewing constructors, tracks, and championship information

from gmr.data import constructors, tracks, drivers
from gmr.constants import is_championship_year, POINTS_TABLE
from gmr.calendar import is_championship_race, BIG_RACES, MEDIUM_RACES, get_world_championship_races


def show_encyclopedia(state, time):
    """Main encyclopedia menu - view constructors, tracks, and championship."""
    while True:
        print("\n" + "=" * 60)
        print("  📚 ENCYCLOPEDIA")
        print("=" * 60)
        print("\nExplore the world of Grand Prix racing:")
        print()
        print("1. Constructors")
        print("2. Circuits")
        if is_championship_year(time.year):
            print("3. 🏆 World Championship Standings")
            print("4. Back to Main Menu")
        else:
            print("3. Back to Main Menu")
        
        choice = input("> ").strip()
        
        if choice == "1":
            show_constructors_menu(state, time)
        elif choice == "2":
            show_tracks_menu(state, time)
        elif choice == "3":
            if is_championship_year(time.year):
                show_championship_standings(state, time)
            else:
                break
        elif choice == "4" and is_championship_year(time.year):
            break
        else:
            print("Invalid choice.")


# =============================================================================
# WORLD CHAMPIONSHIP STANDINGS
# =============================================================================

def show_championship_standings(state, time):
    """Display current World Championship standings."""
    print("\n" + "=" * 60)
    print(f"  🏆 {time.year} FIA WORLD CHAMPIONSHIP OF DRIVERS")
    print("=" * 60)
    
    # Get championship calendar
    champ_races = get_world_championship_races(time.year)
    
    # Show calendar with completed status
    print("\n  CHAMPIONSHIP CALENDAR:")
    completed_count = 0
    for race_name, week, is_transatlantic in champ_races:
        # Check if race is completed
        if hasattr(state, 'completed_races') and week in state.completed_races:
            status = "✅"
            completed_count += 1
        elif hasattr(state, 'pending_race_week') and state.pending_race_week == week:
            status = "🏁"  # Current race
        else:
            status = "⬜"
        
        transatlantic_mark = " 🚢" if is_transatlantic else ""
        print(f"    {status} Week {week}: {race_name}{transatlantic_mark}")
    
    print(f"\n  Races completed: {completed_count}/{len(champ_races)}")
    
    # Show driver standings
    print("\n  ─── DRIVER STANDINGS ───")
    
    if hasattr(state, 'points') and state.points:
        # Sort by points descending
        standings = sorted(state.points.items(), key=lambda x: -x[1])
        
        # Only show drivers with points or top 15
        shown = 0
        for pos, (driver_name, points) in enumerate(standings, 1):
            if points == 0 and shown >= 15:
                continue
            
            # Find driver's constructor
            ctor = "Independent"
            for d in drivers:
                if d.get("name") == driver_name:
                    ctor = d.get("constructor", "Independent")
                    break
            
            # Format position
            if pos == 1:
                medal = "🥇"
            elif pos == 2:
                medal = "🥈"
            elif pos == 3:
                medal = "🥉"
            else:
                medal = f"{pos:2d}."
            
            print(f"    {medal} {driver_name} ({ctor}) - {points} pts")
            shown += 1
            
            if shown >= 20:
                remaining = len([p for _, p in standings if p > 0]) - shown
                if remaining > 0:
                    print(f"    ... and {remaining} more with points")
                break
    else:
        print("    No points scored yet.")
    
    # Show points system
    print("\n  ─── POINTS SYSTEM ───")
    print(f"    1st: {POINTS_TABLE[0]} pts  |  2nd: {POINTS_TABLE[1]} pts  |  3rd: {POINTS_TABLE[2]} pts")
    print(f"    4th: {POINTS_TABLE[3]} pts  |  5th: {POINTS_TABLE[4]} pts  |  6th: {POINTS_TABLE[5]} pts")
    
    input("\n  Press Enter to continue...")


# =============================================================================
# CONSTRUCTORS
# =============================================================================

def get_constructor_stats(state, time, ctor_name):
    """Calculate live stats for a constructor from constructor_stats tracking."""
    # Get current drivers
    current_drivers = [d for d in drivers if d.get("constructor") == ctor_name]
    
    # Get constructor stats if available
    if hasattr(state, 'constructor_stats') and ctor_name in state.constructor_stats:
        stats = state.constructor_stats[ctor_name].copy()
        stats["drivers"] = current_drivers
        return stats
    
    # Fallback: return empty stats
    return {
        "wins": 0,
        "podiums": 0,
        "dnfs": 0,
        "starts": 0,
        "points": 0,
        "drivers": current_drivers,
        "best_finish": None,
        "prize_money": 0,
    }


def show_constructors_menu(state, time):
    """Show list of all constructors."""
    while True:
        print("\n" + "=" * 60)
        print("  🏎️ CONSTRUCTORS")
        print("=" * 60)
        
        # Separate into categories
        works_teams = []
        privateer_teams = []
        
        for name, data in constructors.items():
            if name in ("Independent", "Test"):
                continue
            # Don't show Scuderia Valdieri until they've debuted
            if name == "Scuderia Valdieri" and not getattr(state, "valdieri_active", False):
                continue
            # Don't show Silberkern-Stahl until they've debuted (1952)
            if name == "Silberkern-Stahl" and not getattr(state, "silberkern_active", False):
                continue
            if data.get("is_privateer"):
                privateer_teams.append((name, data))
            else:
                works_teams.append((name, data))
        
        # Sort by prestige
        works_teams.sort(key=lambda x: x[1].get("prestige", 0), reverse=True)
        privateer_teams.sort(key=lambda x: x[1].get("prestige", 0), reverse=True)
        
        ctor_list = []
        
        if works_teams:
            print("\n  WORKS TEAMS:")
            for name, data in works_teams:
                ctor_list.append(name)
                idx = len(ctor_list)
                prestige = data.get("prestige", 0)
                country = data.get("country", "?")
                
                # Count drivers
                driver_count = sum(1 for d in drivers if d.get("constructor") == name)
                
                # Prestige stars
                stars = "★" * int(prestige / 3) + "☆" * (5 - int(prestige / 3))
                
                print(f"    {idx}. {name} ({country}) - {driver_count} driver(s)")
                print(f"       Prestige: {stars}")
        
        if privateer_teams:
            print("\n  PRIVATEER ENTRIES:")
            for name, data in privateer_teams:
                ctor_list.append(name)
                idx = len(ctor_list)
                prestige = data.get("prestige", 0)
                country = data.get("country", "?")
                
                driver_count = sum(1 for d in drivers if d.get("constructor") == name)
                stars = "★" * int(prestige / 3) + "☆" * (5 - int(prestige / 3))
                
                print(f"    {idx}. {name} ({country}) - {driver_count} driver(s)")
                print(f"       Prestige: {stars}")
        
        # Player team
        if state.player_constructor and state.player_constructor not in [n for n, _ in works_teams + privateer_teams]:
            ctor_list.append(state.player_constructor)
            idx = len(ctor_list)
            prestige = state.prestige
            print(f"\n  YOUR TEAM:")
            print(f"    {idx}. {state.player_constructor} - {1 if state.player_driver else 0} driver(s)")
            print(f"       Prestige: {'★' * int(prestige / 2)}{'☆' * (5 - int(prestige / 2))}")
        
        print(f"\n    {len(ctor_list) + 1}. Back")
        
        try:
            choice = int(input("> ").strip())
            if 1 <= choice <= len(ctor_list):
                show_constructor_detail(state, time, ctor_list[choice - 1])
            elif choice == len(ctor_list) + 1:
                break
        except ValueError:
            pass


def show_constructor_detail(state, time, ctor_name):
    """Show detailed view of a single constructor."""
    # Check if it's player team
    is_player = ctor_name == state.player_constructor
    
    if is_player:
        ctor_data = {
            "country": "UK",  # Default for player
            "prestige": state.prestige,
        }
    else:
        ctor_data = constructors.get(ctor_name, {})
    
    print("\n" + "=" * 60)
    print(f"  🏁 {ctor_name.upper()}")
    print("=" * 60)
    
    # Basic info
    country = ctor_data.get("country", "Unknown")
    prestige = ctor_data.get("prestige", state.prestige if is_player else 0)
    
    print(f"\n  Country: {country}")
    print(f"  Prestige: {prestige:.1f} / 15.0")
    print(f"  {'★' * int(prestige)}{'☆' * (15 - int(prestige))}")
    
    # Team type
    if ctor_data.get("is_privateer"):
        print(f"  Type: Privateer Entry")
    elif ctor_name == "Independent":
        print(f"  Type: Independent (no factory backing)")
    elif is_player:
        print(f"  Type: Player Team")
    else:
        print(f"  Type: Works Team")
    
    # Technical info
    engine_id = ctor_data.get("engine_id")
    chassis_id = ctor_data.get("chassis_id")
    if engine_id:
        print(f"\n  Factory Engine: {engine_id}")
    if chassis_id:
        print(f"  Factory Chassis: {chassis_id}")
    
    dev_bonus = ctor_data.get("dev_bonus", 0)
    if dev_bonus > 0:
        print(f"  Development Bonus: +{dev_bonus*100:.0f}%")
    
    # Current drivers
    print("\n  ─── CURRENT DRIVERS ───")
    team_drivers = [d for d in drivers if d.get("constructor") == ctor_name]
    
    if team_drivers:
        for d in sorted(team_drivers, key=lambda x: x.get("fame", 0), reverse=True):
            name = d.get("name", "Unknown")
            fame = d.get("fame", 0)
            age = d.get("age", "?")
            country = d.get("country", "?")
            pace = d.get("pace", 5)
            consistency = d.get("consistency", 5)
            
            fame_int = int(fame)
            fame_stars = "★" * fame_int + "☆" * (4 - fame_int)
            print(f"    • {name} ({country}, age {age})")
            print(f"      Fame: {fame_stars}  Pace: {pace}  Consistency: {consistency}")
    else:
        print("    No drivers currently signed.")
    
    # Season stats
    stats = get_constructor_stats(state, time, ctor_name)
    
    print("\n  ─── SEASON STATS ───")
    print(f"    Races Entered: {stats.get('starts', 0)}")
    print(f"    Wins: {stats.get('wins', 0)}")
    print(f"    Podiums: {stats.get('podiums', 0)}")
    print(f"    DNFs: {stats.get('dnfs', 0)}")
    if stats.get('best_finish'):
        print(f"    Best Result: P{stats['best_finish']}")
    
    if is_championship_year(time.year):
        print(f"    Championship Points: {stats.get('points', 0)}")
    
    # Historical note for famous teams
    if ctor_name == "Enzoni":
        print("\n  ─── HISTORY ───")
        print("    The dominant force of Italian motorsport. Founded")
        print("    by the legendary Enzo Enzoni, this works team has")
        print("    the resources, the drivers, and the prestige that")
        print("    others can only dream of. Their blood-red machines")
        print("    are feared on every circuit.")
    elif ctor_name == "Scuderia Valdieri":
        print("\n  ─── HISTORY ───")
        print("    A proud Italian racing stable, Valdieri represents")
        print("    the elegant side of motorsport. Their royal backing")
        print("    provides resources to challenge even Enzoni, though")
        print("    they prefer grace over brute force.")
    
    input("\n  Press Enter to continue...")


# =============================================================================
# TRACKS / CIRCUITS
# =============================================================================

def get_track_tier(track_name):
    """Get track tier as a readable string."""
    if track_name in BIG_RACES:
        return "Grade A (International Grand Prix)"
    elif track_name in MEDIUM_RACES:
        return "Grade B (International)"
    else:
        return "Grade C (Club/Regional)"


def show_tracks_menu(state, time):
    """Show list of all tracks."""
    while True:
        print("\n" + "=" * 60)
        print("  🏁 CIRCUITS")
        print("=" * 60)
        
        # Group by region
        europe_gp = []
        europe_club = []
        americas = []
        other = []
        
        for name, data in tracks.items():
            country = data.get("country", "Unknown")
            
            # Categorize by country/region
            if country in ("USA", "Argentina", "Brazil"):
                americas.append((name, data))
            elif data.get("allowed_nationalities") and country in ("UK", "France", "Italy", "Germany", "Belgium", 
                           "Switzerland", "Monaco", "Spain", "Netherlands"):
                # European club circuits with nationality restrictions
                europe_club.append((name, data))
            elif country in ("UK", "France", "Italy", "Germany", "Belgium", 
                           "Switzerland", "Monaco", "Spain", "Netherlands"):
                europe_gp.append((name, data))
            else:
                other.append((name, data))
        
        # Sort by prestige
        europe_gp.sort(key=lambda x: x[1].get("prestige_rating", 0), reverse=True)
        europe_club.sort(key=lambda x: x[1].get("prestige_rating", 0), reverse=True)
        americas.sort(key=lambda x: x[1].get("prestige_rating", 0), reverse=True)
        
        track_list = []
        
        print("\n  EUROPEAN GRAND PRIX CIRCUITS:")
        for name, data in europe_gp:
            track_list.append(name)
            idx = len(track_list)
            country = data.get("country", "?")
            prestige = data.get("prestige_rating", 5)
            
            # Championship indicator
            champ = "🏆 " if is_championship_race(name, time.year) else ""
            stars = "★" * prestige + "☆" * (10 - prestige)
            
            print(f"    {idx}. {champ}{name} ({country})")
            print(f"       {stars}")
        
        if europe_club:
            print("\n  EUROPEAN CLUB CIRCUITS:")
            for name, data in europe_club:
                track_list.append(name)
                idx = len(track_list)
                country = data.get("country", "?")
                prestige = data.get("prestige_rating", 5)
                stars = "★" * prestige + "☆" * (10 - prestige)
                
                print(f"    {idx}. {name} ({country})")
                print(f"       {stars}")
        
        if americas:
            print("\n  AMERICAS:")
            for name, data in americas:
                track_list.append(name)
                idx = len(track_list)
                country = data.get("country", "?")
                prestige = data.get("prestige_rating", 5)
                champ = "🏆 " if is_championship_race(name, time.year) else ""
                stars = "★" * prestige + "☆" * (10 - prestige)
                
                print(f"    {idx}. {champ}{name} ({country})")
                print(f"       {stars}")
        
        print(f"\n    {len(track_list) + 1}. Back")
        
        try:
            choice = int(input("> ").strip())
            if 1 <= choice <= len(track_list):
                show_track_detail(state, time, track_list[choice - 1])
            elif choice == len(track_list) + 1:
                break
        except ValueError:
            pass


def show_track_detail(state, time, track_name):
    """Show detailed view of a single track."""
    track_data = tracks.get(track_name, {})
    
    print("\n" + "=" * 60)
    print(f"  🏁 {track_name.upper()}")
    print("=" * 60)
    
    # Basic info
    country = track_data.get("country", "Unknown")
    length = track_data.get("length_km", 0)
    distance = track_data.get("race_distance_km", 0)
    grid_size = track_data.get("grid_size", 20)
    
    print(f"\n  Country: {country}")
    print(f"  Circuit Length: {length:.1f} km")
    print(f"  Race Distance: {distance:.0f} km")
    print(f"  Grid Capacity: {grid_size} cars")
    
    # Tier and championship status
    tier = get_track_tier(track_name)
    print(f"\n  Grade: {tier}")
    if is_championship_race(track_name, time.year):
        print("  🏆 WORLD CHAMPIONSHIP ROUND")
    
    # Flavor text
    flavor = track_data.get("flavor", "")
    if flavor:
        print(f"\n  \"{flavor}\"")
    
    # Track characteristics
    print("\n  ─── TRACK CHARACTERISTICS ───")
    
    # Danger ratings
    engine_danger = track_data.get("engine_danger", 1.0)
    crash_danger = track_data.get("crash_danger", 1.0)
    
    engine_risk = "Low" if engine_danger < 1.0 else "Medium" if engine_danger < 1.1 else "High" if engine_danger < 1.2 else "Extreme"
    crash_risk = "Low" if crash_danger < 1.0 else "Medium" if crash_danger < 1.1 else "High" if crash_danger < 1.2 else "Extreme"
    
    print(f"    Engine Stress: {engine_risk} ({engine_danger:.2f}x)")
    print(f"    Crash Risk: {crash_risk} ({crash_danger:.2f}x)")
    
    # Weather
    wet_chance = track_data.get("wet_chance", 0.3)
    hot_chance = track_data.get("base_hot_chance", 0.2)
    heat_intensity = track_data.get("heat_intensity", 1.0)
    
    print(f"\n    Rain Likelihood: {wet_chance*100:.0f}%")
    print(f"    Hot Weather Likelihood: {hot_chance*100:.0f}%")
    if heat_intensity > 1.05:
        print(f"    Heat Intensity: Severe ({heat_intensity:.2f}x)")
    
    # Car setup importance
    print("\n  ─── CAR SETUP PRIORITIES ───")
    
    pace_weight = track_data.get("pace_weight", 1.0)
    cons_weight = track_data.get("consistency_weight", 1.0)
    susp_importance = track_data.get("suspension_importance", 1.0)
    weight_importance = track_data.get("weight_pace_importance", 1.0)
    
    if pace_weight > 1.05:
        print("    • Raw speed is crucial here")
    elif pace_weight < 0.95:
        print("    • Less about outright pace")
    
    if cons_weight > 1.05:
        print("    • Consistency and precision matter")
    
    if susp_importance > 1.1:
        print("    • Suspension setup is critical")
    
    if weight_importance > 1.1:
        print("    • Lightweight cars have a major advantage")
    
    # Facility ratings
    print("\n  ─── FACILITY RATINGS ───")
    
    safety = track_data.get("safety_rating", 3)
    facilities = track_data.get("facilities_rating", 3)
    prestige = track_data.get("prestige_rating", 5)
    
    print(f"    Safety: {'█' * safety}{'░' * (10 - safety)} ({safety}/10)")
    print(f"    Facilities: {'█' * facilities}{'░' * (10 - facilities)} ({facilities}/10)")
    print(f"    Prestige: {'█' * prestige}{'░' * (10 - prestige)} ({prestige}/10)")
    
    # Prize money info
    fame_mult = track_data.get("fame_mult", 1.0)
    xp_mult = track_data.get("xp_mult", 1.0)
    appearance = track_data.get("appearance_base", 30)
    
    print("\n  ─── REWARDS ───")
    print(f"    Fame Multiplier: {fame_mult:.1f}x")
    print(f"    Experience Multiplier: {xp_mult:.1f}x")
    print(f"    Base Appearance Fee: £{appearance}")
    
    # Nationality restrictions
    allowed = track_data.get("allowed_nationalities")
    if allowed:
        print(f"\n  ⚠️ Regional event: {', '.join(allowed)} drivers only")
    
    # Track history from race_history
    if hasattr(state, 'race_history'):
        track_races = [r for r in state.race_history if r.get("race_name") == track_name]
        if track_races:
            print("\n  ─── RACE HISTORY ───")
            for race in track_races[-3:]:  # Last 3 races at this track
                year = race.get("year", "?")
                finishers = race.get("finishers", [])
                if finishers:
                    winner = finishers[0]
                    print(f"    {year}: {winner.get('name', 'Unknown')} ({winner.get('constructor', '?')})")
    
    input("\n  Press Enter to continue...")
