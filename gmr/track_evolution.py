# gmr/track_evolution.py
"""
Track Evolution System

Tracks are living entities that can:
- Improve safety after fatal accidents or FIA mandates
- Add grandstands when profitable
- Receive FIA upgrades or demotions based on thresholds
- Host different tier championships based on their ratings

Track Ratings:
- safety_rating: 1-10 (1=death trap, 10=ultra-modern)
- facilities_rating: 1-10 (grandstands, pits, medical)  
- prestige: 1-10 (history, crowd, importance)
- grade: "A" (World Championship), "B" (International), "C" (Regional), "D" (Club)

FIA Thresholds (evolve over time):
- 1947-1955: Grade A needs safety 3+, facilities 4+
- 1956-1965: Grade A needs safety 5+, facilities 5+
- 1966-1975: Grade A needs safety 6+, facilities 6+
- 1976+: Grade A needs safety 7+, facilities 7+
"""

import random


# Track state storage (runtime modifications to base track data)
_track_upgrades = {}  # track_name -> {safety_added: int, facilities_added: int, ...}
_track_history = {}   # track_name -> list of events


def get_fia_thresholds(year):
    """
    Get the FIA's minimum requirements for each track grade in a given year.
    Standards increase over time as safety becomes more important.
    """
    if year <= 1955:
        return {
            "A": {"safety": 3, "facilities": 4, "prestige": 5},  # World Championship
            "B": {"safety": 2, "facilities": 3, "prestige": 3},  # International
            "C": {"safety": 1, "facilities": 2, "prestige": 1},  # Regional
            "D": {"safety": 0, "facilities": 0, "prestige": 0},  # Club (anything goes)
        }
    elif year <= 1965:
        return {
            "A": {"safety": 5, "facilities": 5, "prestige": 5},
            "B": {"safety": 3, "facilities": 4, "prestige": 3},
            "C": {"safety": 2, "facilities": 2, "prestige": 1},
            "D": {"safety": 0, "facilities": 0, "prestige": 0},
        }
    elif year <= 1975:
        return {
            "A": {"safety": 6, "facilities": 6, "prestige": 5},
            "B": {"safety": 4, "facilities": 5, "prestige": 3},
            "C": {"safety": 3, "facilities": 3, "prestige": 1},
            "D": {"safety": 1, "facilities": 1, "prestige": 0},
        }
    else:
        return {
            "A": {"safety": 7, "facilities": 7, "prestige": 5},
            "B": {"safety": 5, "facilities": 6, "prestige": 3},
            "C": {"safety": 4, "facilities": 4, "prestige": 1},
            "D": {"safety": 2, "facilities": 2, "prestige": 0},
        }


def get_track_rating(track_name, rating_type):
    """
    Get a track's current rating including any upgrades.
    rating_type: 'safety', 'facilities', 'prestige'
    """
    from gmr.data import tracks
    
    base_data = tracks.get(track_name, {})
    base_value = base_data.get(f"{rating_type}_rating", 3)  # default 3
    
    upgrades = _track_upgrades.get(track_name, {})
    added = upgrades.get(f"{rating_type}_added", 0)
    
    return min(10, base_value + added)  # cap at 10


def get_track_grade(track_name, year):
    """
    Determine what grade a track currently qualifies for.
    Returns: "A", "B", "C", or "D"
    """
    safety = get_track_rating(track_name, "safety")
    facilities = get_track_rating(track_name, "facilities")
    prestige = get_track_rating(track_name, "prestige")
    
    thresholds = get_fia_thresholds(year)
    
    for grade in ["A", "B", "C", "D"]:
        reqs = thresholds[grade]
        if (safety >= reqs["safety"] and 
            facilities >= reqs["facilities"] and 
            prestige >= reqs["prestige"]):
            return grade
    
    return "D"  # fallback


def get_tracks_by_grade(year, target_grade):
    """
    Get all tracks that qualify for a specific grade in a given year.
    """
    from gmr.data import tracks
    
    result = []
    for track_name in tracks.keys():
        if get_track_grade(track_name, year) == target_grade:
            result.append(track_name)
    return result


def get_championship_eligible_tracks(year):
    """
    Get tracks eligible for World Championship (Grade A) in a given year.
    """
    return get_tracks_by_grade(year, "A")


def upgrade_track_safety(track_name, amount=1, reason="general improvements"):
    """
    Increase a track's safety rating.
    """
    if track_name not in _track_upgrades:
        _track_upgrades[track_name] = {}
    
    _track_upgrades[track_name]["safety_added"] = (
        _track_upgrades[track_name].get("safety_added", 0) + amount
    )
    
    if track_name not in _track_history:
        _track_history[track_name] = []
    _track_history[track_name].append(f"Safety upgrade: {reason}")


def upgrade_track_facilities(track_name, amount=1, reason="expansion"):
    """
    Increase a track's facilities rating (grandstands, pits, etc).
    """
    if track_name not in _track_upgrades:
        _track_upgrades[track_name] = {}
    
    _track_upgrades[track_name]["facilities_added"] = (
        _track_upgrades[track_name].get("facilities_added", 0) + amount
    )
    
    if track_name not in _track_history:
        _track_history[track_name] = []
    _track_history[track_name].append(f"Facilities upgrade: {reason}")


def maybe_track_upgrades_after_fatality(state, track_name, year):
    """
    After a fatal accident, there's a chance the track will improve safety.
    Higher chance in later years as public pressure increases.
    """
    # Base 30% chance, increases with year
    base_chance = 0.30 + (year - 1947) * 0.02  # +2% per year
    base_chance = min(0.80, base_chance)  # cap at 80%
    
    if random.random() < base_chance:
        upgrade_track_safety(track_name, amount=1, reason="safety improvements after fatal accident")
        state.news.append(
            f"📋 {track_name} announces safety improvements following the recent tragedy. "
            f"New barriers and run-off areas to be installed before next season."
        )
        return True
    return False


def maybe_track_upgrades_after_serious_crash(state, track_name, year):
    """
    After serious (non-fatal) crashes, smaller chance of safety upgrade.
    """
    chance = 0.10 + (year - 1947) * 0.01  # 10% base, +1% per year
    
    if random.random() < chance:
        upgrade_track_safety(track_name, amount=1, reason="crash investigation recommendations")
        state.news.append(
            f"📋 Following crash investigations, {track_name} will install improved barriers."
        )
        return True
    return False


def maybe_track_expansion(state, track_name, year):
    """
    Tracks may expand facilities if they're doing well (profitable seasons).
    Called during offseason. Higher prestige tracks more likely to expand.
    """
    from gmr.data import tracks
    
    track_data = tracks.get(track_name, {})
    prestige = get_track_rating(track_name, "prestige")
    facilities = get_track_rating(track_name, "facilities")
    
    # Don't expand if already maxed
    if facilities >= 10:
        return False
    
    # Higher prestige = more likely to have money for expansion
    base_chance = 0.05 + prestige * 0.02  # 5% + 2% per prestige point
    
    if random.random() < base_chance:
        upgrade_track_facilities(track_name, amount=1, reason="grandstand expansion")
        state.news.append(
            f"📋 {track_name} announces new grandstand construction for next season. "
            f"Increased capacity expected to boost attendance."
        )
        return True
    return False


def check_fia_grade_changes(state, year):
    """
    Check all tracks against current FIA thresholds.
    Generate news for promotions/demotions.
    Called at start of each season.
    """
    from gmr.data import tracks
    
    news_items = []
    
    for track_name in tracks.keys():
        current_grade = get_track_grade(track_name, year)
        previous_grade = get_track_grade(track_name, year - 1) if year > 1947 else current_grade
        
        # Check for threshold changes (new year means new requirements)
        threshold_years = [1956, 1966, 1976]
        if year in threshold_years:
            if current_grade != previous_grade:
                if current_grade > previous_grade:  # A < B < C < D alphabetically, so > means demotion
                    news_items.append(
                        f"📋 FIA announces stricter {year} regulations. {track_name} no longer meets "
                        f"Grade {previous_grade} standards and is demoted to Grade {current_grade}. "
                        f"The circuit must upgrade to host World Championship events."
                    )
                else:
                    news_items.append(
                        f"📋 {track_name} promoted to Grade {current_grade} status! "
                        f"Recent improvements meet FIA's new standards."
                    )
    
    for item in news_items:
        state.news.append(item)
    
    return news_items


def maybe_fia_pressure_upgrade(state, track_name, year):
    """
    If a track is just below Grade A threshold, FIA may pressure them to upgrade.
    Track might comply (upgrade) or refuse (and lose championship status).
    """
    current_grade = get_track_grade(track_name, year)
    
    if current_grade != "B":
        return  # Only pressure Grade B tracks that could be A
    
    thresholds = get_fia_thresholds(year)
    safety = get_track_rating(track_name, "safety")
    facilities = get_track_rating(track_name, "facilities")
    prestige = get_track_rating(track_name, "prestige")
    
    # Check what's missing
    a_reqs = thresholds["A"]
    safety_gap = max(0, a_reqs["safety"] - safety)
    facilities_gap = max(0, a_reqs["facilities"] - facilities)
    
    if safety_gap == 0 and facilities_gap == 0:
        return  # Already qualifies (must be prestige issue)
    
    # 30% chance FIA pressures them
    if random.random() > 0.30:
        return
    
    # 50% chance track complies with upgrade
    if random.random() < 0.50:
        if safety_gap > 0:
            upgrade_track_safety(track_name, safety_gap, "FIA mandate compliance")
        if facilities_gap > 0:
            upgrade_track_facilities(track_name, facilities_gap, "FIA mandate compliance")
        
        state.news.append(
            f"📋 {track_name} completes FIA-mandated upgrades to retain World Championship status."
        )
    else:
        state.news.append(
            f"📋 {track_name} refuses FIA upgrade demands citing costs. "
            f"The circuit may lose its World Championship date."
        )


def run_offseason_track_evolution(state, year):
    """
    Run all offseason track evolution events.
    Called at the end of each season.
    """
    from gmr.data import tracks
    
    for track_name in tracks.keys():
        # Random expansion chance
        maybe_track_expansion(state, track_name, year)
        
        # FIA pressure on borderline tracks
        maybe_fia_pressure_upgrade(state, track_name, year)
    
    # Check for grade changes at threshold years
    check_fia_grade_changes(state, year + 1)


def get_track_info_string(track_name, year):
    """
    Get a formatted string describing a track's current state.
    """
    safety = get_track_rating(track_name, "safety")
    facilities = get_track_rating(track_name, "facilities")
    prestige = get_track_rating(track_name, "prestige")
    grade = get_track_grade(track_name, year)
    
    safety_desc = ["death trap", "dangerous", "basic", "adequate", "improved", 
                   "good", "modern", "excellent", "world-class", "state-of-art"][min(9, max(0, safety - 1))]
    
    return (
        f"Grade {grade} | Safety: {safety}/10 ({safety_desc}) | "
        f"Facilities: {facilities}/10 | Prestige: {prestige}/10"
    )


def reset_track_evolution():
    """Reset all track upgrades (for new game)."""
    global _track_upgrades, _track_history
    _track_upgrades = {}
    _track_history = {}
