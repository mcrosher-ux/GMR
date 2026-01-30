# gmr/core_state.py

from gmr.data import drivers
from gmr.world_economy import WorldEconomy


class PlayerCharacter:
    """
    The player as a PERSON - separate from any company they might own/run.
    Born in 1930, dies at 100 (year 2030).
    """
    def __init__(self):
        self.name = "Anonymous Owner"
        self.birth_year = 1930
        self.home_country = "UK"
        
        # Personal wealth (separate from company money)
        self.personal_savings = 500  # Start with some personal savings
        
        # Personal stats (1-10 scale)
        self.business_acumen = 5     # Affects sponsor negotiations, costs
        self.technical_knowledge = 5  # Affects R&D efficiency, car insight
        self.reputation = 5          # Personal fame in the paddock
        self.health = 10             # Affects late-game survival
        
        # Career history
        self.companies_founded = []   # List of company names founded
        self.companies_managed = []   # List of company names worked at
        self.career_wins = 0         # Total wins across all companies
        self.career_podiums = 0      # Total podiums across all companies
        self.career_races = 0        # Total races managed
        
        # Current employment status
        self.current_role = "owner"  # "owner", "manager", "unemployed"
        self.years_in_current_role = 0
        
        # Death flag
        self.is_alive = True
        self.death_year = None
        self.death_reason = None
    
    def get_age(self, current_year):
        """Calculate player's current age."""
        return current_year - self.birth_year
    
    def check_death(self, current_year):
        """Check if player should die this year. Returns True if newly dead."""
        if not self.is_alive:
            return False
        
        age = self.get_age(current_year)
        
        # Guaranteed death at 100
        if age >= 100:
            self.is_alive = False
            self.death_year = current_year
            self.death_reason = "old_age"
            return True
        
        # Health-based chance of death after 80
        if age >= 80:
            import random
            # Lower health = higher death chance
            # At age 80 with health 10: ~5% chance
            # At age 95 with health 1: ~50% chance
            death_chance = ((age - 75) * 0.02) * (1.1 - self.health * 0.1)
            if random.random() < death_chance:
                self.is_alive = False
                self.death_year = current_year
                self.death_reason = "health"
                return True
        
        return False
    
    def get_title(self, current_year):
        """Get appropriate title based on age."""
        age = self.get_age(current_year)
        if age < 25:
            return "Young"
        elif age < 40:
            return ""
        elif age < 55:
            return "Experienced"
        elif age < 70:
            return "Veteran"
        else:
            return "Legendary"


class GarageState:
    def __init__(self):
        self.level = 0  # 0 = home shed, 1+ = upgraded facilities
        self.base_cost = 25  # weekly running cost
        self.staff_count = 1
        self.staff_salary = 10

        self.customer_parts_only = True
        self.r_and_d_enabled = False
        self.factory_team = False
        self.mechanic_skill = 3  # 1–10: how good your crew is for now

        # Garage upgrade system
        self.upgrade_level = 0  # 0 = basic shed, 1 = workshop, 2 = professional garage, etc.
        self.upgrades = []  # list of purchased upgrades
        self.repair_discount = 0.0  # percentage discount on repair costs (0.0-1.0)
        self.repair_speed_bonus = 0.0  # percentage faster repairs (0.0-1.0)
        self.mechanic_skill_bonus = 0  # additional mechanic skill from upgrades

    def get_effective_mechanic_skill(self, state=None):
        """Get total mechanic skill including upgrade bonuses and temporary bonuses."""
        from gmr.constants import calculate_garage_benefits
        benefits = calculate_garage_benefits(self)
        skill = self.mechanic_skill + benefits["mechanic_skill_bonus"]

        # Add temporary bonuses from weekly events
        if state:
            if hasattr(state, 'temp_mechanic_bonus') and state.temp_mechanic_bonus != 0:
                skill += state.temp_mechanic_bonus
                # Clear the bonus after use
                state.temp_mechanic_bonus = 0
            if hasattr(state, 'temp_morale_bonus') and state.temp_morale_bonus != 0:
                skill += state.temp_morale_bonus
                # Clear the bonus after use
                state.temp_morale_bonus = 0

        return skill

    def get_repair_cost_multiplier(self):
        """Get multiplier for repair costs (lower = cheaper)."""
        from gmr.constants import calculate_garage_benefits
        benefits = calculate_garage_benefits(self)
        discount = benefits["repair_discount"]
        return max(0.1, 1.0 - discount)  # Minimum 10% of original cost

    def get_repair_speed_multiplier(self):
        """Get multiplier for repair effectiveness (lower = faster/more effective)."""
        from gmr.constants import calculate_garage_benefits
        benefits = calculate_garage_benefits(self)
        speed_bonus = benefits["repair_speed_bonus"]
        return max(0.1, 1.0 - speed_bonus)  # Minimum 10% of original work needed

class GameState:
    def __init__(self):
        # =====================================================================
        # PLAYER CHARACTER - The person playing the game
        # =====================================================================
        self.player_character = PlayerCharacter()
        
        # =====================================================================
        # COMPANY/TEAM - The business entity (can change!)
        # =====================================================================
        self.country = None
        self.money = 5000  # Company money, not personal
        self.points = {}
        self.player_constructor = None  # Company name
        self.player_driver = None       # Driver hired by the company
        
        # Company identity
        self.company_founded_year = 1947  # When the company was founded
        self.company_founder = None       # Who founded it (player or AI name)
        self.is_player_owned = True       # Does the player own this company?
        
        # Company stats
        self.car_speed = 0
        self.car_reliability = 0
        self.constructor_earnings = 0
        self.last_week_income = 0
        self.last_week_outgoings = 0

        # Outgoings buckets
        self.last_week_purchases = 0
        self.last_week_driver_pay = 0
        self.last_week_rnd = 0  # chassis development / R&D spend
        self.last_week_travel_cost = 0  # NEW: race logistics / travel

        # Income buckets
        self.last_week_prize_income = 0
        self.last_week_sponsor_income = 0
        self.last_week_appearance_income = 0  # NEW: organiser appearance money
        self.travel_paid_week = None  # NEW: stops travel being charged twice in same week

        # Patch D: post-race breakdown + XP tracking
        self.last_race_xp_gained = 0.0
        self.last_race_prize_gained = 0
        self.last_race_sponsor_gained = 0
        self.last_race_driver_pay = 0
        self.gallant_driver_promo_done = False

        self.news = []
        self.garage = GarageState()
        self.driver_contract_races = 0
        self.driver_pay = 0
        # Injury system
        self.player_driver_injured = False
        self.player_driver_injury_weeks_remaining = 0
        self.player_driver_injury_severity = 0  # 0=none, 1=minor, 2=serious, 3=career-ending
        self.podiums = {}   # season_week -> list of (driver_name, constructor)
        self.podiums_year = 1947  # tracks which season the stored podiums belong to
        self.race_history = []       # list of race records
        self.driver_career = {}      # driver_name -> totals/stats

        # Career stats for your current lead driver with YOUR team
        self.races_entered_with_team = 0
        self.wins_with_team = 0
        self.podiums_with_team = 0
        self.points_with_team = 0


        self.current_engine = None
        self.current_chassis = None
        self.car_name = None  # e.g. "Harper X1"
        # Long-term mechanical condition (0–100, higher = healthier)
        self.engine_wear = 100.0        # current engine condition
        self.chassis_wear = 100.0       # current chassis condition
        self.engine_max_condition = 100.0   # can be rebuilt to this, then degrades over time
        self.chassis_max_condition = 90.0   # you already conceptually had this for the dad chassis


        # Testing & knowledge
        self.chassis_insight = 0.0      # understanding of current chassis (0-12), gained via test days, resets on chassis change
        self.engine_insight = 0.0       # reserved for later engine work
        self.last_test_abs_week = 0     # absolute_week of last test day

        # PR / sponsor courtship
        self.last_pr_abs_week = 0       # last time you did a PR/networking push


        # NEW: race strategy for the current event
        self.race_strategy = "normal"

        # For repeating calendar & demo cutoff
        self.completed_races = set()
        # Sponsorship fields
        self.sponsor_active = False
        self.sponsor_name = None
        self.sponsor_start_year = None
        self.sponsor_end_year = None
        self.sponsor_races_started = 0
        self.sponsor_podiums = 0
        self.sponsor_points = 0
        self.sponsor_seen_offer = False
        # Sponsor tuning
        self.sponsor_rate_multiplier = 1.0   # lets us sweeten the deal later
        self.sponsor_bonus_event_done = False  # have we had the prestige 5 advert chat yet?
        # Goal tracking for sponsor contracts
        self.sponsor_goals_races_started = False  # completed 3 races started
        self.sponsor_goals_podium = False  # completed 1 podium

      
        self.demo_complete = False

        # NEW: track if we went bust
        self.bankrupt = False       

        # NEW: race is available this week but not started yet
        self.pending_race_week = None

        # Long-term chassis development project
        self.chassis_project_active = False
        self.chassis_progress = 0.0
        self.chassis_project_chassis_id = None  # which chassis this project is for

        # NEW: long-term car condition
        self.engine_health = 100.0  # 0–100, how “fresh” the engine is
        self.chassis_health = 70.0  # start dad’s chassis at ~70% as you asked

        # NEW: remembers how hard you ran the car last race
        self.risk_mode = "neutral"         # "attack", "neutral", "nurse"
        self.risk_multiplier = 1.0         # numeric version, for wear + failure

        # NEW: team reputation in the paddock
        self.prestige = 0.0   # 0–100-ish scale for now

        # Track once we've ever completed Vallone GP (for sponsor triggers)
        self.ever_completed_vallone = False

        # NEW: loan / debt system
        self.loan_balance = 0
        self.loan_interest_rate = 0.0   # weekly rate, e.g. 0.07 for 7%
        self.loan_due_year = None       # year when the loan must be settled
        self.loan_lender_name = None
        self.last_week_loan_interest = 0

        # Tyres (sets in garage)
        self.tyre_sets = 1

        # Has a bankruptcy rescue already been offered this week?
        self.bankruptcy_offered = False

        # Story / demo flags
        self.seen_prologue = False           # have we shown the opening story?
        self.demo_driver_death_done = False  # has the final fatal event fired yet?

        # World economy system
        self.world_economy = WorldEconomy()
        
        # Last race attendance tracking
        self.last_race_attendance = 0
        self.last_race_attendance_details = {}

    def reset_championship(self):
        self.points = {d["name"]: 0 for d in drivers}

def ensure_state_fields(state) -> None:
    """
    Defensive: ensure common per-week / per-race trackers exist.
    Safe to call at boot and at start of each week.
    """
    # Player character system (for old saves)
    if not hasattr(state, "player_character"):
        state.player_character = PlayerCharacter()
        # Try to migrate old data if available
        if hasattr(state, "player_constructor") and state.player_constructor:
            state.player_character.companies_founded.append(state.player_constructor)
            state.player_character.companies_managed.append(state.player_constructor)
    
    # Company identity fields (for old saves)
    if not hasattr(state, "company_founded_year"):
        state.company_founded_year = 1947
    if not hasattr(state, "company_founder"):
        state.company_founder = state.player_character.name if hasattr(state, "player_character") else "Unknown"
    if not hasattr(state, "is_player_owned"):
        state.is_player_owned = True
    
    if not hasattr(state, "valdieri_spawned"):
        state.valdieri_spawned = False

    # compatibility: old/new naming (prize/sponsor)
    if not hasattr(state, "last_week_prize_income"):
        state.last_week_prize_income = getattr(state, "last_week_prize_money", 0)
    if not hasattr(state, "last_week_sponsor_income"):
        state.last_week_sponsor_income = getattr(state, "last_week_sponsor_money", 0)

    # compatibility: R&D naming (YOU currently use last_week_rnd in __init__)
    if not hasattr(state, "last_week_rnd"):
        state.last_week_rnd = getattr(state, "last_week_rd_spend", 0)
    if not hasattr(state, "last_week_rd_spend"):
        state.last_week_rd_spend = getattr(state, "last_week_rnd", 0)

    if not hasattr(state, "last_week_travel_cost"):
        state.last_week_travel_cost = 0
    if not hasattr(state, "last_week_appearance_income"):
        state.last_week_appearance_income = 0
    if not hasattr(state, "travel_paid_week"):
        state.travel_paid_week = None

    if not hasattr(state, "tyre_sets"):
        state.tyre_sets = 1


    if not hasattr(state, "country"):
        state.country = "UK"   # optional: your team home base later

    # --- numeric weekly trackers ---
    for name, default in [
        ("last_week_prize_money", 0),
        ("last_week_sponsor_money", 0),

        ("last_week_driver_pay", 0),
        ("last_week_purchases", 0),
        ("last_week_rd_spend", 0),
        ("last_week_running_costs", 0),
        ("last_week_net", 0),

        # NEW buckets
        ("last_week_travel_cost", 0),
        ("last_week_appearance_income", 0),
    ]:

        if not hasattr(state, name):
            setattr(state, name, default)

    # --- dictionaries / history containers ---
    for name, default in [
        ("completed_races_by_year", {}),
        ("podiums_by_year", {}),
        ("race_history", []),
        ("driver_career", {}),
        ("season_points", {}),   # even if championship inactive
    ]:
        if not hasattr(state, name) or getattr(state, name) is None:
            setattr(state, name, default)

    # --- sponsor placeholders ---
    if not hasattr(state, "sponsor_contract"):
        state.sponsor_contract = None
    if not hasattr(state, "sponsor_paid_this_week"):
        state.sponsor_paid_this_week = False

    if not hasattr(state, "gallant_driver_promo_done"):
        state.gallant_driver_promo_done = False

    # Tyre sponsor fields
    if not hasattr(state, "tyre_sponsor_active"):
        state.tyre_sponsor_active = False
    if not hasattr(state, "tyre_sponsor_name"):
        state.tyre_sponsor_name = None
    if not hasattr(state, "tyre_sponsor_offer_seen_year"):
        state.tyre_sponsor_offer_seen_year = 0

