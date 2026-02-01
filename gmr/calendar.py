# gmr/calendar.py

from gmr.core_time import get_season_week, GameTime
from gmr.constants import MONTHS

import random

# Track tiers for clash rules and championship eligibility
# Grade A: World Championship caliber - cannot clash with anything
# Grade B: International - can clash with small races only  
# Grade C/D: Regional/Club - can clash with other small races

# Big races that anchor the calendar (always Grade A)
BIG_RACES = [
    "Vallone GP", 
    "Ardennes Endurance GP", 
    "Autódromo General San Martín", 
    "Union Speedway",
    "Schwarzwald Ring",
]

# Medium races (Grade B international events)
MEDIUM_RACES = [
    "Marblethorpe GP", 
    "Château-des-Prés GP", 
    "Rougemont GP", 
    "Copper State Circuit",
    "Circuito de las Palmas",
    "Kingsport Coastal Circuit",
    "Circuit de Sable d'Or",
    "Fuji Kogen Circuit",
]

# Small races (Grade C/D club circuits)
SMALL_RACES = [
    "Bradley Fields", 
    "Little Autodromo", 
    "Circuito da Estrada Velha",
]


def get_race_tier(race_name):
    """Get the tier of a race for clash calculations."""
    if race_name in BIG_RACES:
        return "big"
    elif race_name in MEDIUM_RACES:
        return "medium"
    else:
        return "small"


def generate_calendar_for_year(year):
    """
    Build the season calendar for a given year.

    Track availability by year:
    - 1947: European season only (UK, France, Italy, Switzerland, Belgium)
    - 1948: Americas circuits added (Argentina, Brazil, USA regional)
    - 1949: Germany (Nürburgring) joins
    - 1950: USA (Union Speedway), Spain (Pedralbes) join
    - 1951: South Africa (East London) joins  
    - 1952: Morocco (Aïn-Diab), Japan (Suzuka) join
    
    Clash rules:
    - Big races: Never clash
    - Medium races: Can clash with small races only
    - Small races: Can clash with each other
    - At least one race in a clash must be small
    
    Returns: dict mapping week -> race_name (for single races)
             Also stores clashes in a separate structure accessed via get_clashes_for_year()
    """
    rng = random.Random(year)  # deterministic per year

    # Allowed race weeks (Mar–Oct)
    allowed_weeks = list(range(9, 41))  # 9..40 inclusive

    cal = {}
    clashes = {}  # week -> [race1, race2]

    # ---- Anchors (fixed major events) ----
    cal[20] = "Vallone GP"              # sponsor trigger week
    cal[40] = "Ardennes Endurance GP"   # season finale

    # Union Speedway from 1950
    if year >= 1950:
        cal[25] = "Union Speedway"
    
    # Nürburgring equivalent from 1949 - mid-season epic
    if year >= 1949:
        schwarzwald_pool = [w for w in range(22, 28) if w not in cal]
        if schwarzwald_pool:
            cal[rng.choice(schwarzwald_pool)] = "Schwarzwald Ring"

    # Autódromo General San Martín from 1948 (Southern hemisphere = early year)
    if year >= 1948:
        buenos_aires_pool = [w for w in range(10, 15) if w not in cal]
        if buenos_aires_pool:
            cal[rng.choice(buenos_aires_pool)] = "Autódromo General San Martín"

    # Second Vallone in late summer (Italian GP tradition)
    vallone2_pool = [w for w in range(29, 37) if w not in cal]
    if vallone2_pool:
        cal[rng.choice(vallone2_pool)] = "Vallone GP"
    
    # Spanish GP from 1950
    if year >= 1950:
        spain_pool = [w for w in range(16, 22) if w not in cal]
        if spain_pool:
            cal[rng.choice(spain_pool)] = "Circuito de las Palmas"
    
    # South African GP from 1951 (early year due to Southern hemisphere)
    if year >= 1951:
        south_africa_pool = [w for w in range(9, 14) if w not in cal]
        if south_africa_pool:
            cal[rng.choice(south_africa_pool)] = "Kingsport Coastal Circuit"
    
    # Moroccan GP from 1952
    if year >= 1952:
        morocco_pool = [w for w in range(36, 40) if w not in cal]
        if morocco_pool:
            cal[rng.choice(morocco_pool)] = "Circuit de Sable d'Or"
    
    # Japanese GP from 1952 (autumn race)
    if year >= 1952:
        japan_pool = [w for w in range(32, 38) if w not in cal]
        if japan_pool:
            cal[rng.choice(japan_pool)] = "Fuji Kogen Circuit"

    # ---- Fillers (club and regional races) ----
    fillers = [
        "Bradley Fields", "Bradley Fields", "Bradley Fields",
        "Little Autodromo", "Little Autodromo", "Little Autodromo",
        "Marblethorpe GP",
        "Château-des-Prés GP",
        "Rougemont GP",
    ]
    
    # Add Americas races from 1948
    if year >= 1948:
        fillers.extend([
            "Circuito da Estrada Velha", "Circuito da Estrada Velha",
            "Copper State Circuit",
        ])

    candidates = [w for w in allowed_weeks if w not in cal]

    def can_clash(existing_race, new_race):
        """Check if two races can share a week."""
        tier1 = get_race_tier(existing_race)
        tier2 = get_race_tier(new_race)
        
        # Big races never clash
        if tier1 == "big" or tier2 == "big":
            return False
        
        # At least one must be small
        if tier1 == "small" or tier2 == "small":
            return True
        
        # Two medium = no clash
        return False

    def take_week(min_week, max_week, event, min_gap=2):
        """Find a week for an event, possibly creating a clash."""
        # First: try to find a clean week with proper spacing
        pool = [w for w in candidates if min_week <= w <= max_week]
        rng.shuffle(pool)
        
        for w in pool:
            if all(abs(w - ew) >= min_gap for ew in cal.keys()):
                candidates.remove(w)
                return w, False
        
        # Second: try to create a valid clash with an existing race
        clash_candidates = [w for w in range(min_week, max_week + 1) 
                          if w in cal and w not in clashes and can_clash(cal[w], event)]
        rng.shuffle(clash_candidates)
        
        if clash_candidates:
            return clash_candidates[0], True
        
        # Fallback: any free week
        for w in pool:
            if w in candidates:
                candidates.remove(w)
                return w, False
        
        return None, False

    # Placement windows
    placement_windows = [
        (9, 12), (13, 16), (17, 19), (21, 24),
        (26, 28), (29, 32), (33, 36), (37, 39),
    ]
    
    if year >= 1948:
        placement_windows.extend([(14, 18), (22, 26), (30, 34)])

    rng.shuffle(fillers)
    
    for i, event in enumerate(fillers):
        window = placement_windows[i % len(placement_windows)]
        w, is_clash = take_week(window[0], window[1], event)
        
        if w is None and candidates:
            w = candidates.pop(0)
            is_clash = False
        
        if w is not None:
            if is_clash and w in cal:
                existing = cal[w]
                clashes[w] = [existing, event]
                # Keep the "primary" race in cal for backwards compatibility
            else:
                cal[w] = event

    # Store clashes globally for this year (hacky but simple)
    _year_clashes[year] = clashes

    return dict(sorted(cal.items()))


# Global storage for clashes by year
_year_clashes = {}


def get_clashes_for_year(year):
    """Get the clash schedule for a year (must call generate_calendar_for_year first)."""
    return _year_clashes.get(year, {})


def format_week_date(time, season_week):
    """
    Convert a season-week number into the month/week display
    using the time object.
    """
    temp = GameTime(time.year)
    temp.month = 0
    temp.week = 1
    temp.absolute_week = 1

    for _ in range(season_week - 1):
        temp.advance_week()

    return f"Week {temp.week}, {MONTHS[temp.month]}"


def show_calendar(state, time, race_calendar):
    """
    Show the full season calendar with race weeks and simple status flags.
    """
    current_season_week = get_season_week(time)
    clashes = get_clashes_for_year(time.year)

    print("\n=== Season Calendar ===")
    print(f"Year: {time.year}")
    print("------------------------")

    # Collect all race weeks (including clash weeks)
    all_weeks = set(race_calendar.keys()) | set(clashes.keys())

    for week in sorted(all_weeks):
        # Check if this week has a clash
        if week in clashes:
            clash_races = clashes[week]
            race_display = f"{clash_races[0]} OR {clash_races[1]}"
            is_clash = True
        else:
            race_display = race_calendar.get(week, "Unknown")
            is_clash = False

        # Status
        if week in state.completed_races:
            podium = state.podiums.get(week)
            if podium:
                labels = []
                for idx, (name, ctor) in enumerate(podium, start=1):
                    labels.append(f"P{idx} {name} ({ctor})")
                status = ", ".join(labels)
            else:
                status = "Completed"
        elif state.pending_race_week == week and week == current_season_week:
            status = "Race this week"
        else:
            status = "Upcoming"
            if is_clash:
                status = "CHOOSE ONE"

        date_label = format_week_date(time, week)
        
        if is_clash:
            print(f"{date_label}: ⚔️ {race_display}  [{status}]")
        else:
            print(f"{date_label}: {race_display}  [{status}]")

    print("------------------------")
    print("Non-race weeks are not shown.")
    if any(clashes):
        print("⚔️ = Schedule clash — you must choose one race")
