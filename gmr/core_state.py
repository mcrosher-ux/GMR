# gmr/core_state.py

from gmr.data import drivers
from gmr.world_economy import WorldEconomy


class PlayerCharacter:
    """
    The player as a PERSON - separate from any company they might own/run.
    Born in 1930, dies at 100 (year 2030).
    
    SKILLS (grow with experience, start low):
    - technical_knowledge: R&D success, spotting good equipment, era adaptation
    - business: Sponsor deals, purchase prices, detecting bad deals
    - leadership: Driver/mechanic morale, team cohesion
    
    PERSONALITY TRAITS (determined at creation, shape behavior):
    - risk_tolerance: Conservative (1) to Aggressive (10)
    - ambition: Content (1) to Driven (10) 
    - integrity: Pragmatic (1) to Principled (10)
    - patience: Impatient (1) to Long-term planner (10)
    
    REPUTATION: Mirrors prestige/success, not a skill you train
    """
    def __init__(self):
        self.name = "Anonymous Owner"
        self.birth_year = 1930
        self.home_country = "UK"
        
        # Personal wealth (separate from company money)
        self.personal_savings = 500  # Start with some personal savings
        
        # === SKILLS (1-10, start as novice ~2-3) ===
        self.technical_knowledge = 2  # R&D efficiency, equipment insight
        self.business = 2             # Sponsor negotiations, purchase prices
        self.leadership = 2           # Driver/mechanic morale, team cohesion
        
        # === SKILL EXPERIENCE (progress toward next level) ===
        self.technical_xp = 0  # XP toward next technical level
        self.business_xp = 0   # XP toward next business level
        self.leadership_xp = 0 # XP toward next leadership level
        
        # === TECHNICAL EXPERIENCE BY CATEGORY ===
        # Tracks how many times you've built each type (affects learning penalty)
        self.component_experience = {
            "engines": 0,   # How many engines you've developed
            "chassis": 0,   # How many chassis you've developed  
            "aero": 0,      # How many aero packages you've developed
        }
        
        # === ERA FAMILIARITY ===
        # When eras change, your technical knowledge takes a hit until you adapt
        self.current_era = "Post-War Revival"
        self.era_adaptation = 1.0  # 1.0 = fully adapted, lower = still learning
        
        # === PERSONALITY TRAITS (1-10, determined at creation) ===
        self.risk_tolerance = 5  # Conservative (1) to Aggressive (10)
        self.ambition = 5        # Content (1) to Driven (10)
        self.integrity = 5       # Pragmatic (1) to Principled (10)
        self.patience = 5        # Impatient (1) to Long-term planner (10)
        
        # === REPUTATION (mirrors success, not trained) ===
        self.reputation = 1      # Personal fame in the paddock (grows with prestige)
        
        # Health (affects late-game survival)
        self.health = 10
        
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
    
    # === SKILL GROWTH ===
    def gain_technical_xp(self, amount, reason=""):
        """Gain technical experience. Level up when hitting threshold."""
        self.technical_xp += amount
        xp_needed = self._xp_for_next_level(self.technical_knowledge)
        if self.technical_xp >= xp_needed and self.technical_knowledge < 10:
            self.technical_xp -= xp_needed
            self.technical_knowledge += 1
            return f"Technical knowledge improved to {self.technical_knowledge}!"
        return None
    
    def gain_business_xp(self, amount, reason=""):
        """Gain business experience. Level up when hitting threshold."""
        self.business_xp += amount
        xp_needed = self._xp_for_next_level(self.business)
        if self.business_xp >= xp_needed and self.business < 10:
            self.business_xp -= xp_needed
            self.business += 1
            return f"Business skill improved to {self.business}!"
        return None
    
    def gain_leadership_xp(self, amount, reason=""):
        """Gain leadership experience. Level up when hitting threshold."""
        self.leadership_xp += amount
        xp_needed = self._xp_for_next_level(self.leadership)
        if self.leadership_xp >= xp_needed and self.leadership < 10:
            self.leadership_xp -= xp_needed
            self.leadership += 1
            return f"Leadership skill improved to {self.leadership}!"
        return None
    
    def _xp_for_next_level(self, current_level):
        """XP required to reach next level. Higher levels need more XP."""
        # Level 2->3: 100 XP, Level 9->10: 800 XP
        return current_level * 100
    
    # === COMPONENT EXPERIENCE ===
    def record_component_build(self, category):
        """Record that you built a component. Reduces future learning penalty."""
        if category in self.component_experience:
            self.component_experience[category] += 1
    
    def get_component_penalty(self, category):
        """
        Get the learning penalty for building this type of component.
        First time: -30% success rate
        Second time: -15%
        Third+: no penalty
        """
        exp = self.component_experience.get(category, 0)
        if exp == 0:
            return 0.30  # 30% penalty for first attempt
        elif exp == 1:
            return 0.15  # 15% penalty for second attempt
        else:
            return 0.0   # No penalty once experienced
    
    # === ERA ADAPTATION ===
    def check_era_change(self, current_year):
        """Check if era changed and apply adaptation penalty if so."""
        from gmr.constants import get_era_name
        new_era = get_era_name(current_year)
        
        if new_era != self.current_era:
            old_era = self.current_era
            self.current_era = new_era
            # Take a hit to effectiveness until you adapt
            self.era_adaptation = 0.70  # Start at 70% effectiveness in new era
            return f"The {new_era} begins! Your technical knowledge needs updating."
        return None
    
    def adapt_to_era(self):
        """Gradually adapt to new era (call each season or after R&D)."""
        if self.era_adaptation < 1.0:
            # Gain 10% adaptation per season/major activity
            self.era_adaptation = min(1.0, self.era_adaptation + 0.10)
            if self.era_adaptation >= 1.0:
                return "You've fully adapted to the new era!"
        return None
    
    def get_effective_technical(self):
        """Get technical knowledge adjusted for era adaptation."""
        return self.technical_knowledge * self.era_adaptation
    
    # === REPUTATION (mirrors prestige) ===
    def update_reputation(self, company_prestige):
        """Update reputation based on company prestige. Called periodically."""
        # Reputation trends toward company prestige but slower
        target = max(1, company_prestige)
        if self.reputation < target:
            # Gain reputation slowly
            self.reputation = min(target, self.reputation + 0.5)
        elif self.reputation > target + 2:
            # Lose reputation if company is doing worse (but keep some personal rep)
            self.reputation = max(target, self.reputation - 0.25)
    
    # === BUSINESS SKILL EFFECTS ===
    def get_sponsor_deal_multiplier(self):
        """Higher business skill = better sponsor deals."""
        # Skill 2: 0.85x, Skill 5: 1.0x, Skill 10: 1.25x
        return 0.7 + (self.business * 0.055)
    
    def get_purchase_discount(self):
        """Higher business skill = better prices when buying equipment."""
        # Skill 2: 0%, Skill 5: 6%, Skill 10: 16%
        return (self.business - 2) * 0.02
    
    # === LEADERSHIP SKILL EFFECTS ===
    def get_morale_bonus(self):
        """Higher leadership = better driver/mechanic morale."""
        # Skill 2: 0, Skill 5: +3%, Skill 10: +8%
        return (self.leadership - 2) * 0.01
    
    def get_mechanic_bonus(self):
        """Higher leadership = more effective mechanics."""
        # Skill 2: 0, Skill 5: +0.3, Skill 10: +0.8
        return (self.leadership - 2) * 0.1

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


class DriverCareerHistory:
    """
    Detailed career history for a driver.
    Tracks every race result, team affiliations, championships, awards.
    """
    def __init__(self, driver_name, country="Unknown"):
        self.driver_name = driver_name
        self.country = country
        
        # Career totals
        self.total_starts = 0
        self.total_wins = 0
        self.total_podiums = 0
        self.total_poles = 0  # for future qualifying
        self.total_dnfs = 0
        self.total_points = 0
        self.total_prize_money = 0
        self.best_finish = None
        
        # Detailed race results: list of dicts
        # Each: {year, week, race, position, constructor, points, prize, dnf, dnf_reason, wet, hot}
        self.race_results = []
        
        # Team history: list of {constructor, start_year, end_year, wins, races}
        self.team_history = []
        self.current_team = None
        self.current_team_start_year = None
        
        # Season summaries: year -> {starts, wins, podiums, points, position, constructor}
        self.seasons = {}
        
        # Championships and awards
        self.championships = []  # list of {year, position, points, constructor}
        self.awards = []  # list of {year, award_type, details}
        
        # Streaks and records
        self.current_win_streak = 0
        self.best_win_streak = 0
        self.current_podium_streak = 0
        self.best_podium_streak = 0
        self.current_points_streak = 0
        self.best_points_streak = 0
        self.consecutive_finishes = 0
        self.best_consecutive_finishes = 0
        
        # Career start/end
        self.debut_year = None
        self.debut_race = None
        self.retirement_year = None
        self.is_active = True
    
    def record_race(self, year, week, race_name, position, constructor, points, prize, 
                    dnf=False, dnf_reason=None, wet=False, hot=False):
        """Record a single race result."""
        
        # Update debut
        if self.debut_year is None:
            self.debut_year = year
            self.debut_race = race_name
        
        # Track team changes
        if constructor != self.current_team:
            if self.current_team is not None:
                # Close out previous team stint
                for stint in self.team_history:
                    if stint["constructor"] == self.current_team and stint["end_year"] is None:
                        stint["end_year"] = year
            
            # Start new team stint
            self.team_history.append({
                "constructor": constructor,
                "start_year": year,
                "end_year": None,
                "wins": 0,
                "races": 0,
                "points": 0
            })
            self.current_team = constructor
            self.current_team_start_year = year
        
        # Update current team stats
        for stint in self.team_history:
            if stint["constructor"] == constructor and stint["end_year"] is None:
                stint["races"] += 1
                stint["points"] += points
                if position == 1:
                    stint["wins"] += 1
        
        # Record the race result
        result = {
            "year": year,
            "week": week,
            "race": race_name,
            "position": position,  # None if DNF
            "constructor": constructor,
            "points": points,
            "prize": prize,
            "dnf": dnf,
            "dnf_reason": dnf_reason,
            "wet": wet,
            "hot": hot
        }
        self.race_results.append(result)
        
        # Update totals
        self.total_starts += 1
        self.total_points += points
        self.total_prize_money += prize
        
        if dnf:
            self.total_dnfs += 1
            # Reset finish streaks
            if self.consecutive_finishes > self.best_consecutive_finishes:
                self.best_consecutive_finishes = self.consecutive_finishes
            self.consecutive_finishes = 0
            # Reset points streak if DNF with no points
            if points == 0:
                if self.current_points_streak > self.best_points_streak:
                    self.best_points_streak = self.current_points_streak
                self.current_points_streak = 0
            # Reset podium and win streaks
            if self.current_win_streak > self.best_win_streak:
                self.best_win_streak = self.current_win_streak
            if self.current_podium_streak > self.best_podium_streak:
                self.best_podium_streak = self.current_podium_streak
            self.current_win_streak = 0
            self.current_podium_streak = 0
        else:
            self.consecutive_finishes += 1
            
            # Best finish
            if self.best_finish is None or position < self.best_finish:
                self.best_finish = position
            
            # Wins
            if position == 1:
                self.total_wins += 1
                self.total_podiums += 1
                self.current_win_streak += 1
                self.current_podium_streak += 1
            elif position <= 3:
                self.total_podiums += 1
                self.current_podium_streak += 1
                # Reset win streak on non-win
                if self.current_win_streak > self.best_win_streak:
                    self.best_win_streak = self.current_win_streak
                self.current_win_streak = 0
            else:
                # Reset streaks on non-podium
                if self.current_win_streak > self.best_win_streak:
                    self.best_win_streak = self.current_win_streak
                if self.current_podium_streak > self.best_podium_streak:
                    self.best_podium_streak = self.current_podium_streak
                self.current_win_streak = 0
                self.current_podium_streak = 0
            
            # Points streak
            if points > 0:
                self.current_points_streak += 1
            else:
                if self.current_points_streak > self.best_points_streak:
                    self.best_points_streak = self.current_points_streak
                self.current_points_streak = 0
        
        # Update season summary
        if year not in self.seasons:
            self.seasons[year] = {
                "starts": 0,
                "wins": 0,
                "podiums": 0,
                "points": 0,
                "dnfs": 0,
                "constructor": constructor,
                "best_finish": None
            }
        
        season = self.seasons[year]
        season["starts"] += 1
        season["points"] += points
        season["constructor"] = constructor  # Update to current (in case of mid-season change)
        
        if dnf:
            season["dnfs"] += 1
        else:
            if season["best_finish"] is None or position < season["best_finish"]:
                season["best_finish"] = position
            if position == 1:
                season["wins"] += 1
                season["podiums"] += 1
            elif position <= 3:
                season["podiums"] += 1
    
    def record_championship_result(self, year, position, points, constructor):
        """Record end-of-season championship standing."""
        self.championships.append({
            "year": year,
            "position": position,
            "points": points,
            "constructor": constructor
        })
        
        if year in self.seasons:
            self.seasons[year]["championship_position"] = position
        
        # Award for championship win
        if position == 1:
            self.awards.append({
                "year": year,
                "award_type": "Champion",
                "details": f"World Champion with {constructor}"
            })
    
    def add_award(self, year, award_type, details):
        """Add a special award or achievement."""
        self.awards.append({
            "year": year,
            "award_type": award_type,
            "details": details
        })
    
    def retire(self, year):
        """Mark driver as retired."""
        self.retirement_year = year
        self.is_active = False
        
        # Close out current team stint
        if self.current_team is not None:
            for stint in self.team_history:
                if stint["constructor"] == self.current_team and stint["end_year"] is None:
                    stint["end_year"] = year
    
    def get_results_for_year(self, year):
        """Get all race results for a specific year."""
        return [r for r in self.race_results if r["year"] == year]
    
    def get_results_for_team(self, constructor):
        """Get all race results for a specific team."""
        return [r for r in self.race_results if r["constructor"] == constructor]
    
    def get_career_summary(self):
        """Get a summary dict of career stats."""
        years_active = len(self.seasons) if self.seasons else 0
        
        return {
            "name": self.driver_name,
            "country": self.country,
            "years_active": years_active,
            "debut_year": self.debut_year,
            "retirement_year": self.retirement_year,
            "is_active": self.is_active,
            "starts": self.total_starts,
            "wins": self.total_wins,
            "podiums": self.total_podiums,
            "poles": self.total_poles,
            "dnfs": self.total_dnfs,
            "points": self.total_points,
            "prize_money": self.total_prize_money,
            "best_finish": self.best_finish,
            "championships": len([c for c in self.championships if c["position"] == 1]),
            "best_championship": min([c["position"] for c in self.championships]) if self.championships else None,
            "teams": len(self.team_history),
            "best_win_streak": max(self.best_win_streak, self.current_win_streak),
            "best_podium_streak": max(self.best_podium_streak, self.current_podium_streak),
        }


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
        self.driver_career = {}      # driver_name -> totals/stats (legacy, still updated)
        
        # Detailed driver career histories
        # driver_name -> DriverCareerHistory object
        self.driver_histories = {}

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


def record_season_championship_standings(state, year):
    """
    Record end-of-season championship standings to all driver histories.
    Call this BEFORE reset_championship().
    """
    if not hasattr(state, 'points') or not state.points:
        return
    
    if not hasattr(state, 'driver_histories'):
        state.driver_histories = {}
    
    # Sort drivers by points to get championship positions
    standings = sorted(state.points.items(), key=lambda x: -x[1])
    
    for position, (driver_name, points) in enumerate(standings, start=1):
        if points == 0:
            continue  # Skip drivers with no points
        
        # Find driver's constructor
        constructor = "Unknown"
        for d in drivers:
            if d.get("name") == driver_name:
                constructor = d.get("constructor", "Independent")
                break
        
        # Record to driver history if it exists
        if driver_name in state.driver_histories:
            history = state.driver_histories[driver_name]
            history.record_championship_result(year, position, points, constructor)


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
        ("driver_histories", {}),  # Detailed driver career histories
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

