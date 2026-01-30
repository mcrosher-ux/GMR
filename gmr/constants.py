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
    """
    Reliability improves over the decades as engineering matures.
    Lower = more reliable.
    """
    year = time.year
    if year < 1955:
        return 2.5  # Early era: very unreliable
    elif year < 1965:
        return 2.0  # 1950s-60s: improving
    elif year < 1980:
        return 1.5  # 1970s: better engineering
    elif year < 2000:
        return 1.2  # 1980s-90s: modern reliability
    elif year < 2020:
        return 1.0  # 2000s-2010s: highly reliable
    else:
        return 0.8  # 2020s: cutting-edge reliability


def get_crash_mult(time):
    """
    Crash rates decline as safety improves, but later eras push limits again.
    """
    year = time.year
    if year < 1955:
        return 1.5  # Early era: dangerous
    elif year < 1970:
        return 1.3  # 1960s: still risky
    elif year < 1985:
        return 1.1  # 1970s-80s: safety improvements
    elif year < 2000:
        return 1.0  # 1990s: modern safety
    elif year < 2020:
        return 0.9  # 2000s-2010s: very safe
    else:
        return 1.0  # 2020s: pushing limits again with speed


def get_era_name(year):
    """Get the name of the current racing era."""
    if year < 1950:
        return "Post-War Revival"
    elif year < 1960:
        return "Golden Age"
    elif year < 1970:
        return "Sponsorship Era"
    elif year < 1980:
        return "Ground Effect Era"
    elif year < 1990:
        return "Turbo Era"
    elif year < 2000:
        return "High-Tech Era"
    elif year < 2010:
        return "Aero Dominance"
    elif year < 2020:
        return "Hybrid Era"
    elif year < 2025:
        return "Sustainable Era"
    else:
        return "Future Racing"


def get_era_description(year):
    """Get a description of the current era's characteristics."""
    if year < 1950:
        return "Grids rebuilt from pre-war remnants. Passion over technology."
    elif year < 1960:
        return "Front-engined roadsters rule. Privateers thrive alongside works teams."
    elif year < 1970:
        return "Rear engines revolutionize racing. Commercial sponsorship arrives."
    elif year < 1980:
        return "Aerodynamic ground effect changes everything. Danger peaks then regulations tighten."
    elif year < 1990:
        return "Turbochargers deliver incredible power. Electronics begin to influence racing."
    elif year < 2000:
        return "Active suspension and traction control emerge. Costs spiral upward."
    elif year < 2010:
        return "Aerodynamics dominate car design. Overtaking becomes difficult."
    elif year < 2020:
        return "Hybrid power units arrive. Efficiency matters alongside speed."
    elif year < 2025:
        return "Sustainable fuels and reduced emissions. Racing adapts to a changing world."
    else:
        return "Autonomous assistance systems and electric hybrids. The future of racing."


def get_era_speed_factor(year):
    """
    Speed factor increases over time as cars get faster.
    Affects lap times, pursuit gaps, etc.
    """
    if year < 1950:
        return 1.0
    elif year < 1960:
        return 1.1
    elif year < 1970:
        return 1.25
    elif year < 1980:
        return 1.4
    elif year < 1990:
        return 1.6
    elif year < 2000:
        return 1.8
    elif year < 2010:
        return 2.0
    elif year < 2020:
        return 2.1
    else:
        return 2.3  # Futuristic speed


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
