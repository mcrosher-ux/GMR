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


# Garage upgrade system
GARAGE_UPGRADES = {
    "basic_workshop": {
        "name": "Basic Workshop",
        "description": "Convert your home shed into a proper workshop with better tools and workspace.",
        "cost": 500,
        "year_available": 1947,
        "benefits": {
            "repair_discount": 0.1,  # 10% cheaper repairs
            "mechanic_skill_bonus": 1,  # +1 mechanic skill
        },
        "requirements": [],
    },
    "repair_specialization": {
        "name": "Repair Specialization",
        "description": "Train your mechanics in efficient repair techniques.",
        "cost": 800,
        "year_available": 1948,
        "benefits": {
            "repair_speed_bonus": 0.2,  # 20% faster repairs (lower costs for same work)
        },
        "requirements": ["basic_workshop"],
    },
    "advanced_tools": {
        "name": "Advanced Tools",
        "description": "Invest in precision measuring equipment and specialized tools.",
        "cost": 1200,
        "year_available": 1949,
        "benefits": {
            "repair_discount": 0.15,  # Additional 15% discount (stacks)
            "mechanic_skill_bonus": 1,  # Additional +1 mechanic skill
        },
        "requirements": ["basic_workshop"],
    },
    "research_facility": {
        "name": "Research Facility",
        "description": "Add a dedicated research area for studying chassis development.",
        "cost": 2000,
        "year_available": 1955,  # Research becomes more important in 1950s
        "benefits": {
            "r_and_d_enabled": True,  # Unlocks R&D features
        },
        "requirements": ["advanced_tools"],
    },
    "professional_garage": {
        "name": "Professional Garage",
        "description": "Expand to a full professional racing garage with multiple bays.",
        "cost": 3000,
        "year_available": 1952,
        "benefits": {
            "repair_discount": 0.2,  # Additional 20% discount
            "repair_speed_bonus": 0.3,  # Additional 30% faster repairs
            "mechanic_skill_bonus": 2,  # Additional +2 mechanic skill
        },
    },
}


def calculate_garage_benefits(garage):
    """
    Calculate effective garage benefits based on purchased upgrades.
    Returns a dict with total benefits.
    """
    benefits = {
        "repair_discount": 0.0,
        "repair_speed_bonus": 0.0,
        "mechanic_skill_bonus": 0,
        "r_and_d_enabled": False,
    }

    for upgrade_id in garage.upgrades:
        if upgrade_id in GARAGE_UPGRADES:
            upgrade = GARAGE_UPGRADES[upgrade_id]
            for benefit_key, benefit_value in upgrade["benefits"].items():
                if benefit_key in benefits:
                    if isinstance(benefits[benefit_key], bool):
                        benefits[benefit_key] = benefits[benefit_key] or benefit_value
                    else:
                        benefits[benefit_key] += benefit_value

    return benefits


def get_available_garage_upgrades(garage, current_year):
    """
    Get list of upgrade IDs that are available for purchase.
    """
    available = []

    for upgrade_id, upgrade in GARAGE_UPGRADES.items():
        # Check if already purchased
        if upgrade_id in garage.upgrades:
            continue

        # Check year requirement
        if current_year < upgrade["year_available"]:
            continue

        # Check prerequisites
        requirements_met = True
        for req in upgrade["requirements"]:
            if req not in garage.upgrades:
                requirements_met = False
                break

        if requirements_met:
            available.append(upgrade_id)

    return available
