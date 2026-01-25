# gmr/constants.py



MONTHS = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

POINTS_TABLE = [8, 6, 4, 3, 2, 1]

CONSTRUCTOR_SHARE = 0.3
WEEKLY_RUNNING_COST = 80
ERA_RELIABILITY_MULTIPLIER = 2.5
ERA_CRASH_MULTIPLIER = 1.5
WEATHER_WET_CHANCE = 0.35
WEEKS_PER_YEAR = 48
SPONSOR_TRIGGER_RACE_WEEK = 20  # Vallone GP
ENZONI_PRESTIGE_REQUIREMENT = 5.0  # minimum team prestige to unlock Enzoni customer engines
CHAMPIONSHIP_ACTIVE = False
TEST_DRIVERS_ENABLED = False  # Patch F: keep Test archetypes out of real seasons
# --- Debug / dev toggles ---
DEBUG_MODE = True          # set False for "release-like" behaviour
PAUSE_ON_CRASH = True      # when DEBUG_MODE, pause so console doesn't vanish
# ------------------------------
# Prize money by race (player cut still uses CONSTRUCTOR_SHARE elsewhere)
# ------------------------------

DEFAULT_PRIZE_TOP3 = [300, 200, 100]  # fallback if a race isn't listed

PRIZE_RULES = {
    # Keep these as-is (whatever your current defaults are)
    "Bradley Fields": {"top3": [300, 200, 100], "finisher_bonus": 0},
    "Little Autodromo": {"top3": [300, 200, 100], "finisher_bonus": 0},
    "Rogemont": {"top3": [300, 200, 100], "finisher_bonus": 0},

    # Your new structure
    "Marblethorpe GP": {"top3": [400, 250, 150], "finisher_bonus": 0},
    "Château-des-Prés GP": {"top3": [500, 250, 100], "finisher_bonus": 50},
    "Vallone GP": {"top3": [500, 250, 100], "finisher_bonus": 50},
    "Ardennes Endurance GP": {"top3": [800, 500, 300], "finisher_bonus": 100},
}

def get_prize_for_race_and_pos(race_name: str, pos_index: int) -> int:
    """
    pos_index is 0-based (0=winner, 1=P2, 2=P3, 3=P4, etc).
    Returns the organiser prize for that finishing position.
    """
    rule = PRIZE_RULES.get(race_name)
    if not rule:
        # fallback to old behavior
        return DEFAULT_PRIZE_TOP3[pos_index] if pos_index < len(DEFAULT_PRIZE_TOP3) else 0

    top3 = rule.get("top3", DEFAULT_PRIZE_TOP3)
    finisher_bonus = int(rule.get("finisher_bonus", 0))

    if pos_index < len(top3):
        return int(top3[pos_index])

    # 4th+ get finisher bonus (if any)
    return finisher_bonus


def get_reliability_mult(time):
    return ERA_RELIABILITY_MULTIPLIER


def get_crash_mult(time):
    return ERA_CRASH_MULTIPLIER
