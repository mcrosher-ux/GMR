# gmr/calendar.py

from gmr.core_time import get_season_week, GameTime
from gmr.constants import MONTHS

import random

def generate_calendar_for_year(year):
    """
    Build the season calendar for a given year.

    1947–1951 demo:
    - Keep anchor events stable (Vallone week 20, Ardennes finale)
    - Randomise the other race weeks within Mar–Oct with spacing rules
    """
    rng = random.Random(year)  # deterministic per year

    # Allowed race weeks (Mar–Oct)
    allowed_weeks = list(range(9, 41))  # 9..40 inclusive

    cal = {}

    # ---- Anchors (fixed) ----
    cal[20] = "Vallone GP"              # sponsor trigger week
    cal[40] = "Ardennes Endurance GP"   # season finale

    # Second Vallone stays late summer-ish but not fixed
    # pick from Aug/Sep window: weeks 29–36 excluding 20/40
    vallone2_pool = [w for w in range(29, 37) if w not in cal]
    cal[rng.choice(vallone2_pool)] = "Vallone GP"

    # ---- Fillers (randomised with spacing) ----
    # Event list: same total as your current fixed calendar (9 races)
    fillers = [
        "Bradley Fields", "Bradley Fields", "Bradley Fields",
        "Little Autodromo", "Little Autodromo", "Little Autodromo",
        "Marblethorpe GP",
        "Château-des-Prés GP",
    ]

    # Candidate weeks exclude anchors
    candidates = [w for w in allowed_weeks if w not in cal]

    def take_week(min_week, max_week, min_gap=2):
        pool = [w for w in candidates if min_week <= w <= max_week]
        rng.shuffle(pool)
        for w in pool:
            # enforce gap from existing races
            if all(abs(w - ew) >= min_gap for ew in cal.keys()):
                candidates.remove(w)
                return w
        # fallback: if we can't satisfy gap, just take any free week in range
        for w in pool:
            if w in candidates:
                candidates.remove(w)
                return w
        return None

    # Rough seasonal placement buckets to keep the “shape” of the season
    placement_windows = [
        (9, 12),    # early spring
        (13, 16),   # spring
        (17, 19),   # pre-Vallone
        (21, 24),   # early summer
        (25, 28),   # mid summer
        (29, 32),   # late summer
        (33, 36),   # early autumn
        (37, 39),   # pre-finale
    ]

    # Assign fillers to windows
    rng.shuffle(fillers)
    for event, window in zip(fillers, placement_windows):
        w = take_week(window[0], window[1], min_gap=2)
        if w is None:
            # absolute fallback: any candidate week
            w = candidates.pop(0)
        cal[w] = event

    return dict(sorted(cal.items()))


def format_week_date(time, season_week):
    """
    Convert a season-week number into the month/week display
    using the time object.
    """
    # Clone temp time so we don't mutate the real one
    temp = GameTime(time.year)
    temp.month = 0
    temp.week = 1
    temp.absolute_week = 1

    # Advance until we reach the target week
    for _ in range(season_week - 1):
        temp.advance_week()

    return f"Week {temp.week}, {MONTHS[temp.month]}"



def show_calendar(state, time, race_calendar):
    """
    Show the full season calendar with race weeks and simple status flags.
    race_calendar must be the actual calendar used by the game loop.
    """
    current_season_week = get_season_week(time)


    print("\n=== Season Calendar ===")
    print(f"Year: {time.year}")
    print("------------------------")

    for week in sorted(race_calendar.keys()):
        race_name = race_calendar[week]

        # Work out a simple status label
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

        date_label = format_week_date(time, week)
        print(f"{date_label}: {race_name}  [{status}]")

    print("------------------------")
    print("Non-race weeks are not shown.")
