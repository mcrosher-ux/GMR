#gmr/core_state.py
import random

from gmr.data import drivers

class GarageState:
    def __init__(self):
        self.level = 0  # 0 = home shed
        self.base_cost = 25  # weekly running cost
        self.staff_count = 1
        self.staff_salary = 10

        self.customer_parts_only = True
        self.r_and_d_enabled = False
        self.factory_team = False
        self.mechanic_skill = 3  # 1–10: how good your crew is for now

class GameState:
    def __init__(self):
        self.country = None
        self.money = 5000
        self.points = {}
        self.player_constructor = None
        self.player_driver = None
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
        self.chassis_insight = 0.0      # how well you "understand" the current chassis
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

        # Has a bankruptcy rescue already been offered this week?
        self.bankruptcy_offered = False

        # Story / demo flags
        self.seen_prologue = False           # have we shown the opening story?
        self.demo_driver_death_done = False  # has the final fatal event fired yet?

    def reset_championship(self):
        self.points = {d["name"]: 0 for d in drivers}

def ensure_state_fields(state) -> None:
    """
    Defensive: ensure common per-week / per-race trackers exist.
    Safe to call at boot and at start of each week.
    """
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
