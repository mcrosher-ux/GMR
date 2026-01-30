# gmr/race_engine.py
# Core race engine helpers (stage flow, AI stage choices, pit decisions)

import random

from gmr.constants import (
    CHAMPIONSHIP_ACTIVE,
    CONSTRUCTOR_SHARE,
    POINTS_TABLE,
    WEATHER_WET_CHANCE,
    get_reliability_mult,
    get_crash_mult,
    TEST_DRIVERS_ENABLED,
    get_prize_for_race_and_pos,
)
from gmr.data import drivers, tracks, constructors, engines, chassis_list
from gmr.world_logic import driver_enters_event, get_car_speed_for_track, calculate_car_speed
from gmr.careers import (
    update_fame_after_race,
    update_driver_progress,
    grant_participation_xp_for_dnfs,
    tick_driver_contract_after_race_end,
)
from gmr.story import maybe_trigger_demo_finale
from gmr.world_economy import is_home_race, get_home_crowd_bonus

STAGE_LABELS = [
    "Stage 1/3 — Opening Phase",
    "Stage 2/3 — Mid-Race",
    "Stage 3/3 — Final Push",
]


# =============================================================================
# RACE SIMULATOR - Stateful stage-by-stage position tracking
# =============================================================================

class RaceSimulator:
    """
    Tracks the full state of a race through all stages.
    Simulates one stage at a time, maintaining accurate positions.
    """
    
    def __init__(self, event_grid, quali_results, track_profile, state, 
                 is_wet, is_hot, time, grid_risk_mult, race_length_factor):
        self.event_grid = event_grid
        self.quali_results = quali_results
        self.track_profile = track_profile
        self.game_state = state
        self.is_wet = is_wet
        self.is_hot = is_hot
        self.time = time
        self.grid_risk_mult = grid_risk_mult
        self.race_length_factor = race_length_factor
        
        # Initialize positions from qualifying
        if quali_results:
            self.current_positions = [d for d, _ in quali_results if d in event_grid]
        else:
            self.current_positions = list(event_grid)
        
        # Track race state
        self.dnf_drivers = []
        self.retire_reasons = {}  # name -> "engine" or "crash"
        self.active_drivers = set(d.get("name") for d in self.current_positions)
        
        # Track cumulative performance for each driver
        self.driver_performance = {}  # name -> cumulative performance score
        for d in self.current_positions:
            self.driver_performance[d.get("name")] = d["pace"] + d["consistency"] * 0.3
        
        # Player modifiers (cumulative across stages)
        self.player_perf_mult = 1.0
        self.player_engine_mult = 1.0
        self.player_crash_mult = 1.0
        
        # Track reported home race bonuses (only report once)
        self._reported_home_bonus = set()
        
        # Stage tracking
        self.current_stage_idx = 0
        self.stage_history = []  # List of stage results
        
        # Pre-calculate which drivers will have incidents (but don't reveal timing yet)
        self.planned_incidents = self._precompute_incidents()
    
    def _precompute_incidents(self):
        """Pre-determine which AI drivers will have incidents and in which stage."""
        incidents = {}
        reliability_mult = get_reliability_mult(self.time)
        crash_mult = get_crash_mult(self.time)
        
        for d in self.event_grid:
            if d == self.game_state.player_driver:
                continue
            
            car_speed, car_reliability = get_ai_car_stats(d.get("constructor"))
            mech = d.get("mechanical_sympathy", 5)
            aggression = d.get("aggression", 5)
            consistency = d.get("consistency", 5)
            wet_skill = d.get("wet_skill", 5)
            
            # Engine failure chance
            engine_fail_chance = (11 - car_reliability) * 0.02 * reliability_mult
            engine_fail_chance *= (1 + (5 - mech) * 0.05)
            engine_fail_chance *= self.track_profile.get("engine_danger", 1.0)
            engine_fail_chance *= self.race_length_factor
            
            if self.is_hot:
                heat_intensity = self.track_profile.get("heat_intensity", 1.0)
                engine_fail_chance *= heat_intensity
            
            # Crash chance
            base_crash_chance = (11 - consistency) * 0.012
            base_crash_chance *= (1 + (aggression - 5) * 0.05)
            base_crash_chance *= (1 + (5 - mech) * 0.03)
            crash_chance = base_crash_chance * crash_mult
            crash_chance *= self.track_profile.get("crash_danger", 1.0)
            
            if self.is_wet:
                wet_factor = wet_skill / 10.0
                rain_crash_mult = 1.40 - wet_factor * 0.30
                crash_chance *= rain_crash_mult
            
            crash_chance *= self.grid_risk_mult
            
            # Decide incidents
            if random.random() < engine_fail_chance:
                incidents[d.get("name")] = {
                    "type": "engine",
                    "stage_idx": random.randint(0, 2),
                }
            elif random.random() < crash_chance:
                incidents[d.get("name")] = {
                    "type": "crash", 
                    "stage_idx": random.randint(0, 2),
                }
        
        return incidents
    
    def get_current_standings(self):
        """Return current race positions as list of (position, driver, gap_info)."""
        standings = []
        leader_perf = None
        for pos, d in enumerate(self.current_positions, start=1):
            perf = self.driver_performance.get(d.get("name"), 0)
            if leader_perf is None:
                leader_perf = perf
                gap = "LEADER"
            else:
                gap_val = leader_perf - perf
                gap = f"+{gap_val:.1f}s" if gap_val > 0 else "LEADER"
            standings.append((pos, d, gap))
        return standings
    
    def simulate_stage(self, stage_idx, player_strategy_mult=1.0):
        """
        Simulate one stage of the race.
        Returns dict with: overtakes, incidents, new_standings, stage_label
        """
        if stage_idx >= len(STAGE_LABELS):
            return None
        
        stage_label = STAGE_LABELS[stage_idx]
        stage_result = {
            "stage_label": stage_label,
            "stage_idx": stage_idx,
            "overtakes": [],
            "incidents": [],
            "position_changes": [],
        }
        
        # Apply player strategy multiplier
        self.player_perf_mult *= player_strategy_mult
        
        # Process incidents for this stage
        drivers_to_remove = []
        for name, incident_info in self.planned_incidents.items():
            if incident_info["stage_idx"] == stage_idx and name in self.active_drivers:
                # Find the driver
                for d in self.current_positions:
                    if d.get("name") == name:
                        drivers_to_remove.append(d)
                        self.dnf_drivers.append(d)
                        self.retire_reasons[name] = incident_info["type"]
                        self.active_drivers.discard(name)
                        
                        # Record the incident with flavor
                        if incident_info["type"] == "engine":
                            flavors = [
                                f"{name}'s engine expires in a cloud of smoke",
                                f"Mechanical failure forces {name} to retire",
                                f"{name} pulls off with terminal engine damage",
                                f"A plume of oil smoke marks the end of {name}'s race",
                            ]
                        else:
                            flavors = [
                                f"{name} spins into the barriers and is out",
                                f"{name} loses control and crashes out",
                                f"A dramatic crash takes {name} out of the race",
                                f"{name} slides off into the gravel trap — race over",
                            ]
                        stage_result["incidents"].append(random.choice(flavors))
                        break
        
        # Remove DNF'd drivers (AI)
        for d in drivers_to_remove:
            if d in self.current_positions:
                self.current_positions.remove(d)
        
        # =========================================================================
        # PLAYER INCIDENT CHECK - Engine failures and crashes for the player car
        # =========================================================================
        player = self.game_state.player_driver
        if player and player in self.current_positions:
            player_name = player.get("name")
            
            # Get player car stats
            car_reliability = 5  # Default
            if self.game_state.current_engine:
                car_reliability = self.game_state.current_engine.get("reliability", 5)
            
            # Engine condition affects reliability
            engine_wear = getattr(self.game_state, 'engine_wear', 100)
            engine_health = getattr(self.game_state, 'engine_health', 100)
            condition_factor = (engine_wear / 100) * (engine_health / 100)
            
            # Driver mechanical sympathy
            mech = player.get("mechanical_sympathy", 5)
            
            # Base engine failure chance per stage (more punishing than AI for drama)
            reliability_mult = get_reliability_mult(self.time)
            base_engine_fail = (11 - car_reliability) * 0.025 * reliability_mult
            base_engine_fail *= (1 + (5 - mech) * 0.08)
            base_engine_fail *= self.track_profile.get("engine_danger", 1.0)
            base_engine_fail *= self.race_length_factor / 3.0  # Per stage
            
            # Poor condition massively increases risk
            base_engine_fail *= (2.5 - condition_factor * 1.5)  # Up to 2.5x at 0% condition
            
            # Player strategy affects risk
            base_engine_fail *= self.player_engine_mult
            
            # Hot conditions
            if self.is_hot:
                heat_intensity = self.track_profile.get("heat_intensity", 1.0)
                base_engine_fail *= (1.0 + heat_intensity * 0.6)
            
            # Crash chance
            consistency = player.get("consistency", 5)
            aggression = player.get("aggression", 5)
            wet_skill = player.get("wet_skill", 5)
            
            crash_mult = get_crash_mult(self.time)
            base_crash = (11 - consistency) * 0.012 * crash_mult
            base_crash *= (1 + (aggression - 5) * 0.08)
            base_crash *= self.track_profile.get("crash_danger", 1.0)
            base_crash *= self.race_length_factor / 3.0  # Per stage
            
            # Player strategy affects crash risk
            base_crash *= self.player_crash_mult
            
            # Wet conditions
            if self.is_wet:
                wet_factor = wet_skill / 10.0
                rain_crash_mult = 1.50 - wet_factor * 0.35
                base_crash *= rain_crash_mult
            
            base_crash *= self.grid_risk_mult
            
            # Roll for incidents
            player_incident = None
            if random.random() < base_engine_fail:
                player_incident = "engine"
            elif random.random() < base_crash:
                player_incident = "crash"
            
            if player_incident:
                # Player has an incident!
                self.current_positions.remove(player)
                self.dnf_drivers.append(player)
                self.retire_reasons[player_name] = player_incident
                self.active_drivers.discard(player_name)
                
                if player_incident == "engine":
                    flavors = [
                        f"💥 {player_name}'s engine lets go in a spectacular cloud of smoke!",
                        f"💥 Terminal mechanical failure! {player_name} coasts to a stop.",
                        f"💥 The engine gives up! {player_name}'s race is over.",
                        f"💥 Oil smoke billows from {player_name}'s car — engine failure!",
                    ]
                else:
                    flavors = [
                        f"💥 {player_name} loses control and slides into the barriers!",
                        f"💥 A mistake from {player_name}! The car spins off into the gravel!",
                        f"💥 {player_name} crashes out of the race!",
                        f"💥 Disaster! {player_name} hits the wall and is out!",
                    ]
                stage_result["incidents"].append(random.choice(flavors))
                stage_result["player_dnf"] = player_incident
        
        # Calculate new performance for each remaining driver
        old_positions = list(self.current_positions)
        old_order = [d.get("name") for d in old_positions]
        
        stage_performances = []
        for d in self.current_positions:
            name = d.get("name")
            
            # Base performance from stats
            base_pace = d["pace"]
            base_cons = d["consistency"] * 0.4
            
            # Track-specific weights
            track_pace_w = self.track_profile.get("pace_weight", 1.0)
            track_cons_w = self.track_profile.get("consistency_weight", 1.0)
            
            weighted_pace = base_pace * track_pace_w
            weighted_cons = base_cons * track_cons_w
            
            # Consistency affects variance - higher consistency = less swing
            consistency_factor = d["consistency"] / 10.0
            variance_range = (1 - consistency_factor) * weighted_pace * 0.3
            variance = random.uniform(-variance_range, variance_range)
            
            # Calculate stage performance
            stage_perf = weighted_pace + weighted_cons + variance
            
            # Apply aggression bonus (risky but faster)
            aggression = d.get("aggression", 5)
            aggression_bonus = (aggression - 5) * 0.02 * stage_perf
            stage_perf += aggression_bonus
            
            # Wet conditions favor wet skill
            if self.is_wet:
                wet_skill = d.get("wet_skill", 5)
                wet_factor = 0.85 + (wet_skill / 10.0) * 0.30
                stage_perf *= wet_factor
            
            # Hot conditions affect performance
            if self.is_hot:
                heat_tol = d.get("heat_tolerance", 5)
                heat_factor = 0.95 + (heat_tol / 10.0) * 0.10
                stage_perf *= heat_factor
            
            # Home race bonus - drivers perform better in front of home crowds
            if is_home_race(d, self.track_profile):
                home_bonus = get_home_crowd_bonus(d, self.track_profile)
                stage_perf *= home_bonus
                # Only report once at start of race
                if stage_idx == 0 and d.get("name") not in self._reported_home_bonus:
                    self._reported_home_bonus.add(d.get("name"))
            
            # Apply player multipliers
            if d == self.game_state.player_driver:
                stage_perf *= self.player_perf_mult
                
                # Car stats affect performance
                car_speed = get_car_speed_for_track(self.game_state, self.track_profile)
                car_bonus = (car_speed - 5) * 0.03
                stage_perf *= (1 + car_bonus)
            else:
                # AI car performance
                car_speed, _ = get_ai_car_stats(d.get("constructor"))
                car_bonus = (car_speed - 5) * 0.025
                stage_perf *= (1 + car_bonus)
            
            # Update cumulative performance
            self.driver_performance[name] = self.driver_performance.get(name, 0) + stage_perf
            stage_performances.append((d, self.driver_performance[name]))
        
        # Sort by cumulative performance (higher = better position)
        stage_performances.sort(key=lambda x: x[1], reverse=True)
        self.current_positions = [d for d, _ in stage_performances]
        
        # Detect overtakes
        new_order = [d.get("name") for d in self.current_positions]
        
        for new_pos_idx, driver_name in enumerate(new_order):
            if driver_name not in old_order:
                continue
            old_pos_idx = old_order.index(driver_name)
            
            # If driver moved up (lower index = higher position)
            if new_pos_idx < old_pos_idx:
                positions_gained = old_pos_idx - new_pos_idx
                # Record overtakes on drivers they passed
                for i in range(new_pos_idx, old_pos_idx):
                    if i < len(old_order):
                        overtaken_name = old_order[i]
                        if overtaken_name != driver_name:
                            new_pos = new_pos_idx + 1  # 1-indexed
                            stage_result["overtakes"].append({
                                "overtaker": driver_name,
                                "overtaken": overtaken_name,
                                "new_position": new_pos,
                            })
        
        # Record position changes
        for d in self.current_positions:
            name = d.get("name")
            new_pos = new_order.index(name) + 1
            if name in old_order:
                old_pos = old_order.index(name) + 1
                change = old_pos - new_pos
                if change != 0:
                    stage_result["position_changes"].append({
                        "driver": name,
                        "old_pos": old_pos,
                        "new_pos": new_pos,
                        "change": change,
                    })
        
        # Store in history
        self.stage_history.append(stage_result)
        self.current_stage_idx = stage_idx + 1
        
        return stage_result
    
    def get_final_results(self):
        """Return final race results."""
        finishers = []
        for pos, d in enumerate(self.current_positions, start=1):
            score = self.driver_performance.get(d.get("name"), 0)
            finishers.append((d, score))
        return finishers, self.dnf_drivers, self.retire_reasons


def format_overtake_text(overtaker, overtaken, new_pos):
    """Generate flavorful overtake announcement."""
    flavors = [
        f"{overtaker} slips past {overtaken} to grab P{new_pos}",
        f"{overtaker} outbrakes {overtaken} into P{new_pos}",
        f"{overtaker} powers past {overtaken} to take P{new_pos}",
        f"{overtaker} dives inside {overtaken} for P{new_pos}",
        f"{overtaker} overtakes {overtaken} — now P{new_pos}",
        f"{overtaker} sweeps past {overtaken} to claim P{new_pos}",
        f"Brilliant move! {overtaker} takes P{new_pos} from {overtaken}",
        f"{overtaker} makes it stick on {overtaken} — P{new_pos}!",
    ]
    return random.choice(flavors)


def display_stage_results(state, race_name, stage_result, simulator):
    """Display the results of a simulated stage to the player."""
    
    def highlight_player(text):
        player = getattr(state, "player_driver", None)
        if not player:
            return text
        name = player.get("name")
        if not name:
            return text
        green = "\x1b[32m"
        reset = "\x1b[0m"
        return text.replace(name, f"{green}{name}{reset}")
    
    stage_label = stage_result["stage_label"]
    print(f"\n{'='*60}")
    print(f"  {stage_label}")
    print(f"{'='*60}")
    
    # Show incidents first
    if stage_result["incidents"]:
        print("\n⚠️  INCIDENTS:")
        for incident in stage_result["incidents"]:
            print(f"    {highlight_player(incident)}")
            state.news.append(f"INCIDENT ({race_name}): {incident}")
    
    # Show overtakes
    if stage_result["overtakes"]:
        print("\n🏎️  POSITION CHANGES:")
        for ot in stage_result["overtakes"]:
            text = format_overtake_text(ot["overtaker"], ot["overtaken"], ot["new_position"])
            print(f"    {highlight_player(text)}")
            # Overtakes not added to news - too spammy for post-race summary
    
    # Show current standings
    standings = simulator.get_current_standings()
    print(f"\n📊  CURRENT STANDINGS:")
    
    # Find player position for highlighting
    player_name = state.player_driver.get("name") if state.player_driver else None
    
    for pos, d, gap in standings[:10]:  # Top 10
        name = d.get("name")
        if name == player_name:
            print(f"    \x1b[32mP{pos}. {name} ({gap})\x1b[0m")
        else:
            print(f"    P{pos}. {name} ({gap})")
    
    if len(standings) > 10:
        # Check if player is outside top 10
        player_pos = None
        for pos, d, gap in standings:
            if d.get("name") == player_name:
                player_pos = pos
                break
        if player_pos and player_pos > 10:
            print(f"    ...")
            print(f"    \x1b[32mP{player_pos}. {player_name}\x1b[0m")


def get_player_stage_decision(stage_idx, is_wet, is_hot):
    """Get player's strategy decision for the upcoming stage."""
    
    stage_label = STAGE_LABELS[stage_idx] if stage_idx < len(STAGE_LABELS) else "Final Stage"
    
    print(f"\n{'─'*60}")
    print(f"  STRATEGY DECISION — {stage_label}")
    print(f"{'─'*60}")
    
    # Context-aware options
    if is_wet:
        print("\n  Conditions: WET — grip is unpredictable")
    elif is_hot:
        print("\n  Conditions: HOT — engine and tyres under stress")
    else:
        print("\n  Conditions: DRY — standard racing conditions")
    
    print("\n  Choose your approach:")
    print("  1) PUSH — Attack hard, risk more (+5% pace, +15% incident risk)")
    print("  2) BALANCED — Steady pace, normal risk")
    print("  3) CONSERVE — Protect car, sacrifice pace (-5% pace, -20% incident risk)")
    
    while True:
        choice = input("\n  Your choice (1/2/3): ").strip()
        if choice == "1":
            return {
                "label": "PUSH",
                "performance_mult": 1.05,
                "engine_fail_mult": 1.15,
                "crash_mult": 1.15,
            }
        elif choice == "2":
            return {
                "label": "BALANCED", 
                "performance_mult": 1.0,
                "engine_fail_mult": 1.0,
                "crash_mult": 1.0,
            }
        elif choice == "3":
            return {
                "label": "CONSERVE",
                "performance_mult": 0.95,
                "engine_fail_mult": 0.85,
                "crash_mult": 0.80,
            }
        else:
            print("  Please enter 1, 2, or 3.")


def run_interactive_race_stages(simulator, state, race_name, is_wet, is_hot):
    """
    Run the race interactively: simulate each stage, show results, get decision.
    Returns final stage_mods dict with cumulative multipliers.
    """
    cumulative_mods = {
        "performance_mult": 1.0,
        "engine_fail_mult": 1.0,
        "crash_mult": 1.0,
    }
    
    for stage_idx in range(len(STAGE_LABELS)):
        # Get player decision BEFORE simulating this stage
        decision = get_player_stage_decision(stage_idx, is_wet, is_hot)
        
        print(f"\n  → Strategy set to: {decision['label']}")
        
        # Apply decision to cumulative mods
        cumulative_mods["performance_mult"] *= decision["performance_mult"]
        cumulative_mods["engine_fail_mult"] *= decision["engine_fail_mult"]
        cumulative_mods["crash_mult"] *= decision["crash_mult"]
        
        # Update simulator's risk multipliers for this stage
        simulator.player_engine_mult = decision["engine_fail_mult"]
        simulator.player_crash_mult = decision["crash_mult"]
        
        # Simulate the stage with player's chosen multiplier
        stage_result = simulator.simulate_stage(stage_idx, decision["performance_mult"])
        
        if stage_result:
            # Display what happened
            display_stage_results(state, race_name, stage_result, simulator)
            
            # Check if player DNF'd
            if stage_result.get("player_dnf"):
                print(f"\n  💀 YOUR RACE IS OVER!")
                input("\n  Press Enter to continue...")
                break
        
        # Pause between stages (except after last)
        if stage_idx < len(STAGE_LABELS) - 1:
            input("\n  Press Enter to continue to next stage...")
    
    return cumulative_mods


# =============================================================================
# END RACE SIMULATOR
# =============================================================================


def per_stage_chance(total_chance, stages=3):
    """
    Convert a total event probability into an approximate per-stage chance.
    Ensures the overall probability stays similar across multiple rolls.
    """
    total_chance = max(0.0, min(total_chance, 0.99))
    if stages <= 1:
        return total_chance
    return 1.0 - (1.0 - total_chance) ** (1.0 / stages)


def estimate_stage_wear(stage_index, race_length_factor, is_hot):
    """
    Rough UI-only estimates for tyre wear and engine temp by stage.
    Returns (tyre_pct, engine_temp_pct) as 0–100.
    """
    base_tyre = 25 + (race_length_factor - 1.0) * 15
    base_engine = 30 + (race_length_factor - 1.0) * 10

    if is_hot:
        base_engine += 15
        base_tyre += 5

    tyre = min(98, max(5, base_tyre * (stage_index + 1)))
    engine = min(98, max(5, base_engine * (stage_index + 1)))
    return int(tyre), int(engine)


def generate_stage_blurb(stage_label, is_hot, is_wet, long_race, pace_note=None, incidents=None):
    """
    Procedural stage blurb including other-driver incidents and position changes.
    """
    segments = []

    weather_openers = [
        "Heat haze shimmers over the circuit.",
        "The sun bakes the tarmac into a shimmering ribbon.",
        "The crowd waves handkerchiefs in the glare of the afternoon heat.",
        "Spray hangs in the air as grip comes and goes.",
        "The rain eases, leaving a slippery sheen and scattered puddles.",
        "The wind carries a fine mist across the braking zones.",
        "The field settles into a steady rhythm.",
        "Engines roar in unison as the pack strings out.",
        "Marshals watch intently as the race finds its pace.",
    ]

    if is_hot:
        segments.append(random.choice(weather_openers[:3]))
    elif is_wet:
        segments.append(random.choice(weather_openers[3:6]))
    else:
        segments.append(random.choice(weather_openers[6:]))

    trackside = [
        "A thin line of rubber darkens the racing groove.",
        "Dust from the infield drifts onto the edge of the circuit.",
        "Pit boards flash along the pit wall as crews take notes.",
        "A brief lull lets drivers find a smoother line.",
        "Spectators rise as two cars dispute the same corner.",
        "The grandstands ripple with cheers as someone attacks into the braking zone.",
    ]
    if random.random() < 0.65:
        segments.append(random.choice(trackside))

    # Other-driver failures (named incidents)
    if incidents:
        for incident in incidents[:2]:
            segments.append(incident)

    # Other-driver failures (generic flavour)
    failure_lines = [
        "A plume of smoke signals trouble for a mid-pack runner.",
        "A car crawls into the pits with a faltering engine.",
        "Marshals wave yellow flags after a car stops off-line.",
        "A privateer limps back with a misfire.",
        "The crowd spots a stricken car at the far hairpin.",
    ]
    if random.random() < 0.60 and not incidents:
        count = random.choice([1, 1, 2])
        segments.append(
            f"Around the circuit, {count} car{'s' if count != 1 else ''} slow or retire with trouble."
        )
        if random.random() < 0.55:
            segments.append(random.choice(failure_lines))

    # Overtake flavour
    overtake_lines = [
        "Your driver gets a better exit and draws alongside.",
        "A brave move into the corner pays off.",
        "A rival hesitates on the brakes and loses momentum.",
        "A lapped car forces a momentary hesitation.",
        "The slipstream tug proves decisive down the straight.",
        "Your driver holds firm through the chicane.",
    ]
    if pace_note:
        segments.append(pace_note)
    elif random.random() < 0.75:
        delta = random.choice([-3, -2, -1, 1, 2, 3])
        if delta > 0:
            segments.append(random.choice(overtake_lines))
            segments.append(f"Your driver picks off {delta} rival{'s' if delta != 1 else ''} in traffic.")
        else:
            segments.append(random.choice(overtake_lines))
            segments.append(f"A rival slips past — you drop {abs(delta)} place{'s' if abs(delta) != 1 else ''}.")

    long_race_lines = [
        "In this long race, pacing is already proving decisive.",
        "The long distance begins to expose the fragile cars.",
        "A steady hand seems more valuable with every passing kilometre.",
    ]
    if long_race and random.random() < 0.8:
        segments.append(random.choice(long_race_lines))

    tactical_lines = [
        "The crew signals to keep it tidy through the rough section.",
        "The pit wall urges patience as gaps fluctuate.",
        "A brief lull lets your driver reset their rhythm.",
        "Radio silence means the pit board is the only guide.",
    ]
    if random.random() < 0.6:
        segments.append(random.choice(tactical_lines))

    # Ensure multiple sentences for richer flavour
    random.shuffle(segments)
    return " ".join(segments[:min(len(segments), 5)])


def choose_stage_strategy(stage_label, is_wet, is_hot, state=None):
    """
    Player choice for a race stage. Returns multipliers for performance, engine risk, crash risk.
    Also accumulates wear on state if provided.
    """
    print(f"\n=== Race Update: {stage_label} ===")
    if is_wet:
        print("Conditions are still tricky in the damp.")
    elif is_hot:
        print("Engines are running hot in the heat.")
    else:
        print("Track conditions are steady.")

    print("Choose your approach for this phase:")
    print("1) Push hard (faster, +40% wear)")
    print("2) Balanced (steady pace)")
    print("3) Conserve (safer, -30% wear)")

    choice = input("> ").strip()

    # Track cumulative wear from stage choices
    if state is not None:
        if not hasattr(state, 'stage_wear_accumulator'):
            state.stage_wear_accumulator = 0.0
        if not hasattr(state, 'stage_count'):
            state.stage_count = 0
        state.stage_count += 1

    if choice == "1":
        if state is not None:
            state.stage_wear_accumulator += 1.4  # Push = 40% more wear
        return {
            "label": "Push hard",
            "performance_mult": 1.04,
            "engine_fail_mult": 1.25,
            "crash_mult": 1.20,
        }
    if choice == "3":
        if state is not None:
            state.stage_wear_accumulator += 0.7  # Conserve = 30% less wear
        return {
            "label": "Conserve",
            "performance_mult": 0.97,
            "engine_fail_mult": 0.80,
            "crash_mult": 0.85,
        }

    # Default: balanced
    if state is not None:
        state.stage_wear_accumulator += 1.0
    return {
        "label": "Balanced",
        "performance_mult": 1.00,
        "engine_fail_mult": 1.00,
        "crash_mult": 1.00,
    }


def maybe_stage_event(stage_label, is_wet, is_hot):
    """
    Random race-stage events that may affect the player's race.
    Returns None or a dict with multipliers.
    """
    if random.random() > 0.35:
        return None

    events = [
        {
            "text": "Clear track ahead lets you build rhythm.",
            "performance_mult": 1.02,
            "engine_fail_mult": 1.00,
            "crash_mult": 1.00,
        },
        {
            "text": "Traffic slows your pace through the twisty section.",
            "performance_mult": 0.98,
            "engine_fail_mult": 1.00,
            "crash_mult": 1.00,
        },
        {
            "text": "A brake pedal goes long for a moment.",
            "performance_mult": 0.99,
            "engine_fail_mult": 1.00,
            "crash_mult": 1.10,
        },
        {
            "text": "The engine starts to run a little rough.",
            "performance_mult": 0.98,
            "engine_fail_mult": 1.12,
            "crash_mult": 1.00,
        },
        {
            "text": "A light shower begins, making the braking zones uncertain.",
            "performance_mult": 0.99,
            "engine_fail_mult": 1.00,
            "crash_mult": 1.15,
            "requires_wet": True,
        },
        {
            "text": "Trackside dust drifts onto the racing line.",
            "performance_mult": 0.99,
            "engine_fail_mult": 1.00,
            "crash_mult": 1.08,
        },
        {
            "text": "A tailwind on the main straight boosts top speed.",
            "performance_mult": 1.02,
            "engine_fail_mult": 1.02,
            "crash_mult": 1.00,
        },
        {
            "text": "A vibration hints at a tire issue.",
            "performance_mult": 1.00,
            "engine_fail_mult": 1.00,
            "crash_mult": 1.00,
            "pit_issue": True,
            "no_pit_performance_mult": 0.96,
            "no_pit_crash_mult": 1.25,
        },
        {
            "text": "A sudden tyre failure sends the driver scrambling to keep control.",
            "performance_mult": 0.96,
            "engine_fail_mult": 1.00,
            "crash_mult": 1.20,
            "forced_tyre_change": True,
        },
        {
            "text": "Fuel delivery feels uneven under load.",
            "performance_mult": 1.00,
            "engine_fail_mult": 1.10,
            "crash_mult": 1.00,
            "pit_issue": True,
            "no_pit_engine_mult": 1.20,
            "no_pit_performance_mult": 0.97,
        },
        {
            "text": "The car settles into a smooth rhythm.",
            "performance_mult": 1.01,
            "engine_fail_mult": 0.98,
            "crash_mult": 0.98,
        },
        {
            "text": "Oil temperature spikes briefly.",
            "performance_mult": 0.99,
            "engine_fail_mult": 1.12,
            "crash_mult": 1.00,
            "requires_hot": True,
        },
        {
            "text": "A light drizzle makes the racing line tricky.",
            "performance_mult": 0.99,
            "engine_fail_mult": 1.00,
            "crash_mult": 1.12,
            "requires_wet": True,
        },
        {
            "text": "A drying line appears and grip improves.",
            "performance_mult": 1.02,
            "engine_fail_mult": 1.00,
            "crash_mult": 0.98,
            "requires_wet": True,
        },
    ]

    eligible = []
    for ev in events:
        if ev.get("requires_wet") and not is_wet:
            continue
        if ev.get("requires_hot") and not is_hot:
            continue
        eligible.append(ev)

    if not eligible:
        return None

    event = random.choice(eligible)
    return {
        "text": event["text"],
        "performance_mult": event.get("performance_mult", 1.0),
        "engine_fail_mult": event.get("engine_fail_mult", 1.0),
        "crash_mult": event.get("crash_mult", 1.0),
        "pit_issue": event.get("pit_issue", False),
        "forced_tyre_change": event.get("forced_tyre_change", False),
        "no_pit_performance_mult": event.get("no_pit_performance_mult", 1.0),
        "no_pit_engine_mult": event.get("no_pit_engine_mult", 1.0),
        "no_pit_crash_mult": event.get("no_pit_crash_mult", 1.0),
    }


def maybe_stage_decision(stage_label, is_wet, is_hot):
    """
    Random decision prompts during a stage.
    Returns None or a dict with two choices and multipliers.
    """
    if random.random() > 0.25:
        return None

    decisions = [
        {
            "prompt": "The driver reports fading brakes at the end of the straight.",
            "choice_a": "Tell them to nurse the brakes",
            "choice_b": "Tell them to keep pushing",
            "a": {"performance_mult": 0.98, "engine_fail_mult": 0.98, "crash_mult": 0.90},
            "b": {"performance_mult": 1.01, "engine_fail_mult": 1.02, "crash_mult": 1.15},
        },
        {
            "prompt": "The pit board suggests conserving fuel. Do you comply?",
            "choice_a": "Conserve fuel",
            "choice_b": "Ignore and maintain pace",
            "a": {"performance_mult": 0.98, "engine_fail_mult": 0.92, "crash_mult": 0.98},
            "b": {"performance_mult": 1.01, "engine_fail_mult": 1.08, "crash_mult": 1.00},
        },
    ]

    eligible = []
    for dec in decisions:
        if dec.get("requires_wet") and not is_wet:
            continue
        if dec.get("requires_hot") and not is_hot:
            continue
        eligible.append(dec)

    if not eligible:
        return None

    return random.choice(eligible)


def prompt_pit_decision(reason, prompt_text):
    """
    Ask player about a pit decision (1940s style: no radio).
    """
    print("\nPit decision:")
    print(reason)
    choice = input(prompt_text).strip().lower()
    return choice == "y"


def precompute_ai_stage_incidents(event_grid, state, track_profile, time, is_wet, is_hot, grid_risk_mult, race_length_factor):
    """
    Decide AI DNFs up front so stage updates can name actual incidents.
    Returns dict: driver_name -> {"type": "engine"|"crash", "stage": label}.
    """
    incidents = {}

    reliability_mult = get_reliability_mult(time)
    crash_mult = get_crash_mult(time)

    for d in event_grid:
        if d == state.player_driver:
            continue

        car_speed, car_reliability = get_ai_car_stats(d.get("constructor"))
        _ = car_speed  # unused here but kept for parity

        mech = d.get("mechanical_sympathy", 5)
        aggression = d.get("aggression", 5)
        consistency = d.get("consistency", 5)
        wet_skill = d.get("wet_skill", 5)

        engine_fail_chance = (11 - car_reliability) * 0.02 * reliability_mult
        engine_fail_chance *= (1 + (5 - mech) * 0.05)
        engine_fail_chance *= track_profile.get("engine_danger", 1.0)
        engine_fail_chance *= race_length_factor

        if is_hot:
            heat_intensity = track_profile.get("heat_intensity", 1.0)
            engine_fail_chance *= heat_intensity

        base_crash_chance = (11 - consistency) * 0.012
        base_crash_chance *= (1 + (aggression - 5) * 0.05)
        base_crash_chance *= (1 + (5 - mech) * 0.03)

        crash_chance = base_crash_chance * crash_mult
        crash_chance *= track_profile.get("crash_danger", 1.0)

        if is_wet:
            wet_factor = wet_skill / 10.0
            rain_crash_mult = 1.40 - wet_factor * 0.30
            crash_chance *= rain_crash_mult

        sus = get_suspension_value_for_driver(state, d)
        sus_importance = suspension_track_factor(track_profile)
        crash_sus_mult = 1.08 - (sus - 5) * 0.02
        crash_sus_mult = clamp(crash_sus_mult, 0.88, 1.15)
        crash_sus_mult = 1.0 + (crash_sus_mult - 1.0) * sus_importance
        crash_chance *= crash_sus_mult
        crash_chance *= grid_risk_mult

        ai_stage_mods = run_ai_race_stages(d, is_wet, is_hot, race_length_factor, car_reliability)
        engine_fail_chance *= ai_stage_mods["engine_fail_mult"]
        crash_chance *= ai_stage_mods["crash_mult"]

        if random.random() < engine_fail_chance:
            incidents[d.get("name")] = {
                "type": "engine",
                "stage": random.choice(STAGE_LABELS),
            }
            continue

        if random.random() < crash_chance:
            incidents[d.get("name")] = {
                "type": "crash",
                "stage": random.choice(STAGE_LABELS),
            }

    return incidents


def precompute_ai_stage_overtakes(event_grid, quali_results):
    """
    Compare qualifying positions to predicted race finishing order.
    Distribute position changes across stages as overtake announcements.
    Returns dict: stage_label -> [("Smith", "Jones", 3)] meaning "Smith overtakes Jones for 3rd".
    """
    if not quali_results:
        return {label: [] for label in STAGE_LABELS}

    # Map driver names to their qualifying positions (1-indexed)
    quali_positions = {}
    for pos, (d, _) in enumerate(quali_results, start=1):
        quali_positions[d.get("name")] = pos

    # Predict race order using simple performance scoring (matches run_race logic)
    predicted_race_order = []
    for d in event_grid:
        # Simple performance score (rough approximation)
        score = d["pace"] * 1.2 + d["consistency"] * 0.4
        predicted_race_order.append((d, score))

    predicted_race_order.sort(key=lambda x: x[1], reverse=True)

    # Map driver names to predicted race positions (1-indexed)
    race_positions = {}
    for pos, (d, _) in enumerate(predicted_race_order, start=1):
        race_positions[d.get("name")] = pos

    # Build reverse map: quali position -> driver name
    quali_pos_to_name = {pos: name for name, pos in quali_positions.items()}
    race_pos_to_name = {pos: name for name, pos in race_positions.items()}

    # Distribute overtakes across stages (more in early/mid stages)
    stage_overtakes = {label: [] for label in STAGE_LABELS}
    stage_weights = [0.40, 0.40, 0.20]

    # For each final race position, work backwards to see who was overtaken
    all_overtakes = []
    
    for race_pos in sorted(race_positions.values()):
        overtaker = race_pos_to_name.get(race_pos)
        if not overtaker:
            continue
            
        quali_pos_overtaker = quali_positions.get(overtaker)
        if quali_pos_overtaker is None:
            continue
        
        # If they gained positions (moved up)
        if quali_pos_overtaker > race_pos:
            # They overtook everyone between their quali pos and race pos
            for pos_between in range(race_pos, quali_pos_overtaker):
                # Who was in this position in quali?
                overtaken = quali_pos_to_name.get(pos_between)
                if overtaken and overtaken in race_positions:
                    # Only record if the overtaken driver also finished
                    all_overtakes.append({
                        "overtaker": overtaker,
                        "overtaken": overtaken,
                        "new_position": race_pos
                    })

    # Assign each overtake to a stage
    for overtake in all_overtakes:
        # Pick a stage probabilistically
        rand = random.random()
        cumulative = 0.0
        assigned_stage = STAGE_LABELS[-1]  # default to final stage

        for idx, weight in enumerate(stage_weights):
            cumulative += weight
            if rand < cumulative:
                assigned_stage = STAGE_LABELS[idx]
                break

        stage_overtakes[assigned_stage].append(
            (overtake["overtaker"], overtake["overtaken"], overtake["new_position"])
        )

    return stage_overtakes


def compute_stage_overtakes_from_results(quali_results, finishers):
    """
    Compute overtakes based on actual final results.
    Uses a swap-based transform from quali order to final order.
    Returns dict: stage_label -> [(overtaker, overtaken, new_pos), ...]
    """
    stage_overtakes = {label: [] for label in STAGE_LABELS}

    if not quali_results or not finishers:
        return stage_overtakes

    finishers_names = [d.get("name") for d, _ in finishers]
    quali_order = [d.get("name") for d, _ in quali_results if d.get("name") in finishers_names]
    final_order = finishers_names[:]

    if not quali_order or not final_order:
        return stage_overtakes

    current = quali_order[:]
    swap_events = []

    for target_index, target_name in enumerate(final_order):
        if target_name not in current:
            continue
        current_index = current.index(target_name)
        while current_index > target_index:
            overtaker = current[current_index]
            overtaken = current[current_index - 1]
            current[current_index - 1], current[current_index] = current[current_index], current[current_index - 1]
            current_index -= 1
            new_pos = current_index + 1
            swap_events.append((overtaker, overtaken, new_pos))

    total = len(swap_events)
    if total == 0:
        return stage_overtakes

    stage_weights = [0.40, 0.40, 0.20]
    counts = [int(total * w) for w in stage_weights]
    while sum(counts) < total:
        for i in range(len(counts)):
            if sum(counts) < total:
                counts[i] += 1

    idx = 0
    for stage_idx, stage_label in enumerate(STAGE_LABELS):
        take = counts[stage_idx]
        for _ in range(take):
            if idx >= total:
                break
            stage_overtakes[stage_label].append(swap_events[idx])
            idx += 1

    return stage_overtakes


def simulate_race_positions(event_grid, quali_results, stage_incidents, stage_mods, 
                           track_profile, is_wet, is_hot, time, state, grid_risk_mult, race_length_factor):
    """
    Simulate race positions through all 3 stages, tracking overtakes as they happen.
    Returns: (finishers, dnf_drivers, retire_reasons, stage_overtakes)
    
    stage_overtakes is a dict: stage_label -> [(overtaker, overtaken, new_pos), ...]
    """
    stage_overtakes = {label: [] for label in STAGE_LABELS}
    dnf_drivers = []
    retire_reasons = {}
    
    # Build starting positions from quali results
    if quali_results:
        current_positions = [d for d, _ in quali_results if d in event_grid]
    else:
        current_positions = list(event_grid)
    
    # Track who has DNF'd
    active_drivers = set(d.get("name") for d in current_positions)
    
    # Process each stage
    for stage_label in STAGE_LABELS:
        # Remove drivers who crashed/failed in this stage
        stage_dnfs = []
        if stage_incidents:
            for name, info in stage_incidents.items():
                if info["stage"] == stage_label and name in active_drivers:
                    # Find and remove the driver
                    for d in current_positions:
                        if d.get("name") == name:
                            stage_dnfs.append(d)
                            dnf_drivers.append(d)
                            retire_reasons[name] = info["type"]
                            active_drivers.discard(name)
                            break
        
        # Remove DNFs from current positions
        for d in stage_dnfs:
            if d in current_positions:
                current_positions.remove(d)
        
        # Calculate performance for remaining drivers this stage
        stage_performances = []
        for d in current_positions:
            # Base performance calculation
            base_pace = d["pace"]
            base_cons = d["consistency"] * 0.4
            
            # Random variance based on consistency
            consistency_factor = d["consistency"] / 10.0
            variance = random.uniform(-1, 1) * (1 - consistency_factor) * base_pace * 0.25
            
            performance = base_pace + base_cons + variance
            
            # Apply stage mods for player
            if d == state.player_driver:
                performance *= stage_mods.get("performance_mult", 1.0)
            
            # Wet conditions favor wet skill
            if is_wet:
                wet_skill = d.get("wet_skill", 5)
                wet_factor = 0.85 + (wet_skill / 10.0) * 0.30
                performance *= wet_factor
            
            stage_performances.append((d, performance))
        
        # Sort by performance (higher is better)
        stage_performances.sort(key=lambda x: x[1], reverse=True)
        new_positions = [d for d, _ in stage_performances]
        
        # Detect overtakes: compare old order to new order
        old_order = [d.get("name") for d in current_positions]
        new_order = [d.get("name") for d in new_positions]
        
        for new_pos_idx, driver_name in enumerate(new_order):
            if driver_name not in old_order:
                continue
            old_pos_idx = old_order.index(driver_name)
            
            # If driver moved up (lower index = higher position)
            if new_pos_idx < old_pos_idx:
                # They overtook everyone between their old and new position
                for pos_between in range(new_pos_idx, old_pos_idx):
                    overtaken_name = old_order[pos_between]
                    if overtaken_name != driver_name:
                        stage_overtakes[stage_label].append(
                            (driver_name, overtaken_name, new_pos_idx + 1)  # 1-indexed position
                        )
        
        # Update positions for next stage
        current_positions = new_positions
    
    # Build final finishers list with scores
    finishers = []
    for pos, d in enumerate(current_positions):
        # Calculate a final score for tie-breaking
        score = d["pace"] + d["consistency"] * 0.4
        finishers.append((d, score))
    
    return finishers, dnf_drivers, retire_reasons, stage_overtakes


def consume_tyre_set(state, race_name, reason):
    """
    Consume one tyre set if available. Returns True if consumed.
    """
    if getattr(state, "tyre_sets", 0) <= 0:
        state.news.append(
            f"TYRES ({race_name}): No spare sets available — {reason} postponed."
        )
        return False

    state.tyre_sets -= 1
    state.news.append(
        f"TYRES ({race_name}): Used 1 set ({reason}). Remaining: {state.tyre_sets}."
    )
    return True


def run_player_race_stages(state, race_name, is_wet, is_hot, track_profile, stage_incidents=None, stage_overtakes=None, defer_output=False):
    """
    Run a simple 3-part race flow with player decisions and events.
    Returns cumulative multipliers for performance and risks.
    """
    stage_defs = STAGE_LABELS
    stage_output = []

    perf_mult = 1.0
    engine_mult = 1.0
    crash_mult = 1.0

    race_distance_km = track_profile.get("race_distance_km", 250.0)
    long_race = race_distance_km >= 350.0

    for idx, stage_label in enumerate(stage_defs):
        tyre_pct, engine_temp_pct = estimate_stage_wear(idx, race_distance_km / 250.0, is_hot)
        stage_events = []
        stage_news = []
        stage_blurb = None

        # Collect ALL incidents for this stage
        incidents = []
        if stage_incidents:
            for name, info in stage_incidents.items():
                if info["stage"] == stage_label:
                    if info["type"] == "engine":
                        incidents.append(f"{name} slows with engine trouble")
                    else:
                        incidents.append(f"{name} spins into the barriers")

        for incident in incidents:
            stage_events.append(f"Incident: {incident}")

        # Collect ALL overtakes for this stage
        overtakes = []
        if stage_overtakes and stage_label in stage_overtakes:
            for overtaker, overtaken, new_pos in stage_overtakes[stage_label]:
                # Add flavor to the overtake announcement
                flavors = [
                    f"{overtaker} slips past {overtaken} to grab P{new_pos}",
                    f"{overtaker} outbrakes {overtaken} into P{new_pos}",
                    f"{overtaker} powers past {overtaken} to take P{new_pos}",
                    f"{overtaker} dives inside {overtaken} for P{new_pos}",
                    f"{overtaker} overtakes {overtaken} to move into P{new_pos}",
                    f"{overtaker} sweeps past {overtaken} to claim P{new_pos}",
                ]
                overtakes.append(random.choice(flavors))

        choice = choose_stage_strategy(stage_label, is_wet, is_hot, state)
        perf_mult *= choice["performance_mult"]
        engine_mult *= choice["engine_fail_mult"]
        crash_mult *= choice["crash_mult"]

        stage_news.append(
            f"RACE STRATEGY ({race_name}): {stage_label} — {choice['label']}."
        )

        event = maybe_stage_event(stage_label, is_wet, is_hot)
        if event:
            perf_mult *= event["performance_mult"]
            engine_mult *= event["engine_fail_mult"]
            crash_mult *= event["crash_mult"]
            stage_events.append(event["text"])
            stage_news.append(f"RACE EVENT ({race_name}): {event['text']}")

            if event.get("forced_tyre_change"):
                stage_events.append("The driver dives into the pits for a tyre change.")
                if consume_tyre_set(state, race_name, "emergency tyre change"):
                    perf_mult *= 0.96
                    crash_mult *= 0.95
                else:
                    perf_mult *= 0.95
                    crash_mult *= 1.15

            if event.get("pit_issue"):
                stage_events.append("The driver brings the car in to report the issue (no radio in this era).")
                if prompt_pit_decision(
                    "You can attempt a quick fix/tyre change, or send them straight back out.",
                    "Attempt a quick fix? (y/n): "
                ):
                    if consume_tyre_set(state, race_name, "repair stop"):
                        perf_mult *= 0.97
                        engine_mult *= 0.90
                        crash_mult *= 0.90
                        perf_mult *= 1.01
                        stage_news.append(f"PIT STOP ({race_name}): Team makes a quick repair stop.")
                    else:
                        perf_mult *= 0.985
                        engine_mult *= event.get("no_pit_engine_mult", 1.0)
                        crash_mult *= event.get("no_pit_crash_mult", 1.0)
                        stage_news.append(f"PIT STOP ({race_name}): No tyres available; driver waved back out.")
                else:
                    perf_mult *= 0.985
                    perf_mult *= event.get("no_pit_performance_mult", 1.0)
                    engine_mult *= event.get("no_pit_engine_mult", 1.0)
                    crash_mult *= event.get("no_pit_crash_mult", 1.0)
                    stage_news.append(f"PIT STOP ({race_name}): Driver waved back out without repairs.")

        if long_race and stage_label != stage_defs[0]:
            if prompt_pit_decision(
                "Long race. You can hang a pit board and call them in for fuel/tyres.",
                "Signal for a stop? (y/n): "
            ):
                if consume_tyre_set(state, race_name, "fuel/tyre stop"):
                    perf_mult *= 0.97
                    perf_mult *= 1.01
                    engine_mult *= 0.92
                    crash_mult *= 0.92
                    stage_news.append(f"PIT STOP ({race_name}): Fuel/tyre stop taken in a long race.")
                else:
                    perf_mult *= 0.98
                    engine_mult *= 1.05
                    crash_mult *= 1.05
                    stage_news.append(f"PIT STOP ({race_name}): No tyres available; stop cancelled.")

        decision = maybe_stage_decision(stage_label, is_wet, is_hot)
        if decision:
            print(f"\nDecision: {decision['prompt']}")
            print(f"1) {decision['choice_a']}")
            print(f"2) {decision['choice_b']}")
            choice = input("> ").strip()
            if choice == "1":
                chosen = decision["a"]
                stage_news.append(f"DECISION ({race_name}): {decision['choice_a']}.")
            else:
                chosen = decision["b"]
                stage_news.append(f"DECISION ({race_name}): {decision['choice_b']}.")

            perf_mult *= chosen.get("performance_mult", 1.0)
            engine_mult *= chosen.get("engine_fail_mult", 1.0)
            crash_mult *= chosen.get("crash_mult", 1.0)

        # Stage pace note based on current multiplier
        if perf_mult >= 1.03:
            pace_note = "Your driver appears to be increasing the pace."
        elif perf_mult <= 0.98:
            pace_note = "Your driver looks to be losing ground."
        else:
            pace_note = "The pace looks steady for now."

        stage_blurb = generate_stage_blurb(stage_label, is_hot, is_wet, long_race, pace_note=pace_note, incidents=[])

        stage_output.append({
            "label": stage_label,
            "tyre_pct": tyre_pct,
            "engine_temp_pct": engine_temp_pct,
            "events": stage_events,
            "blurb": stage_blurb,
            "incidents": incidents,
            "overtakes": overtakes,
            "news": stage_news,
        })

        if not defer_output:
            render_player_stage_output(state, race_name, [stage_output[-1]], stage_overtakes)

    stage_mods = {
        "performance_mult": perf_mult,
        "engine_fail_mult": engine_mult,
        "crash_mult": crash_mult,
    }

    return stage_mods, stage_output


def render_player_stage_output(state, race_name, stage_output, stage_overtakes=None):
    def highlight_player(text: str) -> str:
        player = getattr(state, "player_driver", None)
        if not player:
            return text
        name = player.get("name")
        if not name:
            return text
        green = "\x1b[32m"
        reset = "\x1b[0m"
        return text.replace(name, f"{green}{name}{reset}")

    for stage in stage_output:
        stage_label = stage["label"]
        tyre_pct = stage["tyre_pct"]
        engine_temp_pct = stage["engine_temp_pct"]

        print(f"\n[{stage_label}] Tyre wear estimate: {tyre_pct}% | Engine temp: {engine_temp_pct}%")

        for entry in stage.get("news", []):
            state.news.append(entry)

        for event_text in stage.get("events", []):
            print(event_text)

        blurb = stage.get("blurb")
        if blurb:
            state.news.append(f"STAGE UPDATE ({race_name}): {blurb}")
            print(highlight_player(blurb))

        incidents = stage.get("incidents", [])
        if incidents:
            print(f"\nIncidents in {stage_label}:")
            for incident in incidents:
                print(f"  • {highlight_player(incident)}")
                state.news.append(f"INCIDENT ({race_name}, {stage_label}): {incident}")

        overtakes = stage.get("overtakes", [])
        if stage_overtakes and stage_label in stage_overtakes:
            overtakes = []
            for overtaker, overtaken, new_pos in stage_overtakes[stage_label]:
                flavors = [
                    f"{overtaker} slips past {overtaken} to grab P{new_pos}",
                    f"{overtaker} outbrakes {overtaken} into P{new_pos}",
                    f"{overtaker} powers past {overtaken} to take P{new_pos}",
                    f"{overtaker} dives inside {overtaken} for P{new_pos}",
                    f"{overtaker} overtakes {overtaken} to move into P{new_pos}",
                    f"{overtaker} sweeps past {overtaken} to claim P{new_pos}",
                ]
                overtakes.append(random.choice(flavors))

        if overtakes:
            print(f"\nPosition changes in {stage_label}:")
            for overtake in overtakes:
                print(f"  • {highlight_player(overtake)}")
                # Overtakes not added to news - too spammy for post-race summary


def render_stage_overtakes_only(state, race_name, stage_overtakes):
    def highlight_player(text: str) -> str:
        player = getattr(state, "player_driver", None)
        if not player:
            return text
        name = player.get("name")
        if not name:
            return text
        green = "\x1b[32m"
        reset = "\x1b[0m"
        return text.replace(name, f"{green}{name}{reset}")

    if not stage_overtakes:
        return

    for stage_label in STAGE_LABELS:
        overtakes = stage_overtakes.get(stage_label, [])
        if not overtakes:
            continue

        print(f"\nPosition changes in {stage_label}:")
        for overtaker, overtaken, new_pos in overtakes:
            flavors = [
                f"{overtaker} slips past {overtaken} to grab P{new_pos}",
                f"{overtaker} outbrakes {overtaken} into P{new_pos}",
                f"{overtaker} powers past {overtaken} to take P{new_pos}",
                f"{overtaker} dives inside {overtaken} for P{new_pos}",
                f"{overtaker} overtakes {overtaken} to move into P{new_pos}",
                f"{overtaker} sweeps past {overtaken} to claim P{new_pos}",
            ]
            line = random.choice(flavors)
            print(f"  • {highlight_player(line)}")
            # Overtakes not added to news - too spammy for post-race summary


def choose_ai_stage_strategy(stage_label, driver, is_wet, is_hot, race_length_factor, car_reliability):
    """
    AI stage choice for a race segment.
    """
    aggression = driver.get("aggression", 5)
    consistency = driver.get("consistency", 5)
    mech = driver.get("mechanical_sympathy", 5)

    # Baseline tendency
    push_bias = 0
    conserve_bias = 0

    if aggression >= 7:
        push_bias += 1
    if consistency >= 7:
        push_bias += 1
    if mech >= 7:
        conserve_bias += 1
    if car_reliability < 5:
        conserve_bias += 2

    if is_hot and mech <= 4:
        conserve_bias += 1
    if is_wet and consistency <= 4:
        conserve_bias += 1

    if race_length_factor >= 1.2 and stage_label != "Stage 3/3 — Final Push":
        conserve_bias += 1

    # Small randomness so AI isn't deterministic
    roll = random.random()

    if push_bias - conserve_bias >= 2 or (roll < 0.2 and push_bias > conserve_bias):
        return "push"
    if conserve_bias - push_bias >= 2 or (roll < 0.2 and conserve_bias > push_bias):
        return "conserve"

    return "balanced"


def run_ai_race_stages(driver, is_wet, is_hot, race_length_factor, car_reliability):
    """
    Run 3-stage AI race flow and return combined multipliers.
    """
    stage_defs = STAGE_LABELS

    perf_mult = 1.0
    engine_mult = 1.0
    crash_mult = 1.0

    for stage_label in stage_defs:
        choice = choose_ai_stage_strategy(
            stage_label,
            driver,
            is_wet,
            is_hot,
            race_length_factor,
            car_reliability,
        )

        if choice == "push":
            perf_mult *= 1.03
            engine_mult *= 1.15
            crash_mult *= 1.12
        elif choice == "conserve":
            perf_mult *= 0.98
            engine_mult *= 0.88
            crash_mult *= 0.90

    return {
        "performance_mult": perf_mult,
        "engine_fail_mult": engine_mult,
        "crash_mult": crash_mult,
    }


def choose_ai_race_strategy(driver, constructor):
    """
    AI drivers choose strategy based on aggression and constructor.
    Returns risk_mode string.
    """
    aggression = driver.get("aggression", 5)

    # Base chance from aggression
    if aggression >= 7:
        attack_chance = 0.6
        nurse_chance = 0.1
    elif aggression <= 3:
        attack_chance = 0.1
        nurse_chance = 0.6
    else:
        attack_chance = 0.3
        nurse_chance = 0.3

    # Constructor influence
    if constructor == "Enzoni":
        attack_chance += 0.2  # More aggressive
    elif constructor == "Independent":
        nurse_chance += 0.1  # More conservative

    # Normalize
    attack_chance = min(attack_chance, 1.0)
    nurse_chance = min(nurse_chance, 1.0)
    neutral_chance = 1.0 - attack_chance - nurse_chance
    neutral_chance = max(neutral_chance, 0.0)

    rand = random.random()
    if rand < attack_chance:
        return "attack"
    if rand < attack_chance + neutral_chance:
        return "neutral"
    return "nurse"


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def pay_appearance_money(state, race_name):
    t = tracks.get(race_name, {})
    base = int(t.get("appearance_base", 0))
    mult = float(t.get("appearance_prestige_mult", 0.0))

    if base <= 0 and mult <= 0:
        return 0

    payout = int(base + state.prestige * mult)
    payout = max(0, payout)

    # Cap appearance money based on track prestige
    if race_name in ["Bradley Fields", "Little Autodromo"]:
        payout = min(payout, 50)
    elif race_name in ["Ardennes Endurance GP", "Union Speedway"]:
        payout = min(payout, 150)
    else:
        payout = min(payout, 100)

    # Track appearance money separately from prize money
    if not hasattr(state, "last_week_appearance_income"):
        state.last_week_appearance_income = 0

    state.money += payout
    state.last_week_income += payout
    state.last_week_appearance_income += payout

    team_name = state.player_constructor or "Your team"
    state.news.append(
        f"Appearance money: {team_name} receive £{payout} from {race_name}'s organisers for taking the start."
    )
    return payout


def get_suspension_value_for_driver(state, d):
    """
    Returns suspension score (1–10) for this driver's current car.
    Player uses current_chassis. AI uses constructor chassis if available.
    """
    if d == state.player_driver and state.current_chassis:
        return int(state.current_chassis.get("suspension", 5))

    # AI: try to read from their works chassis
    c = constructors.get(d.get("constructor", ""), {})
    ch_id = c.get("chassis_id")
    if ch_id:
        ch = next((x for x in chassis_list if x.get("id") == ch_id), None)
        if ch:
            return int(ch.get("suspension", 5))

    return 5


def suspension_track_factor(track_profile):
    return float(track_profile.get("suspension_importance", 1.0))


def get_ai_car_stats(constructor_name):
    c = constructors.get(constructor_name, {})

    # Parts-based path FIRST (only if ids are defined)
    eng_id = c.get("engine_id")
    ch_id = c.get("chassis_id")
    if eng_id and ch_id:
        eng = next((e for e in engines if e["id"] == eng_id), None)
        ch = next((x for x in chassis_list if x["id"] == ch_id), None)
        if eng and ch:
            speed = calculate_car_speed(eng, ch)
            reliability = eng.get("reliability", 5)
            return speed, reliability

    # Legacy fallback (Independents stay here)
    if "speed" in c and "reliability" in c:
        return c["speed"], c["reliability"]

    return 5, 5


def build_event_grid(state, time, race_name, track_profile):
    """
    Returns a list of drivers who will take part in THIS event,
    respecting per-team car limits.

    IMPORTANT:
    - "Independent" is NOT a real team; it's the open-entry pool.
      So it should NOT be capped to 2 cars.
    """

    # Optional: let tracks define grid size (fallback to something sane)
    grid_size = track_profile.get("grid_size", 12)

    # How many cars each WORKS team can enter this year
    def team_car_limit(team_name: str) -> int:
        if team_name == "Enzoni":
            return 3 if time.year >= 1950 else 2
        if team_name == "Scuderia Valdieri":
            return 2
        if state.player_constructor and team_name == state.player_constructor:
            return 1
        return 999  # any future "real" team won't be accidentally capped

    # Collect eligible drivers by "team"/pool
    by_team = {}
    for d in drivers:
        if not driver_enters_event(d, race_name, track_profile, state):
            continue

        # Block Test drivers if debug toggle is off
        if not TEST_DRIVERS_ENABLED and d.get("constructor") == "Test":
            continue

        # Player team: only the contracted player driver is allowed to represent it
        if state.player_constructor and d.get("constructor") == state.player_constructor:
            if d is not state.player_driver:
                continue

        team = d.get("constructor", "Independent")
        by_team.setdefault(team, []).append(d)

    final_grid = []

    # 1) Add works teams and player (capped)
    for team in ("Enzoni", "Scuderia Valdieri"):
        if team in by_team:
            team_drivers = by_team[team]

            # best drivers get the seats
            team_drivers.sort(
                key=lambda x: (x.get("pace", 0) * 1.0 + x.get("consistency", 0) * 0.5),
                reverse=True,
            )

            final_grid.extend(team_drivers[:team_car_limit(team)])

    # Player
    if state.player_constructor and state.player_constructor in by_team:
        final_grid.extend(by_team[state.player_constructor][:1])

    # 2) Fill the rest of the grid with Independents (open pool)
    independents = by_team.get("Independent", [])

    # IMPORTANT: don't always pick the same top guys
    # Shuffle first, then lightly sort by ability so it still feels “real”
    random.shuffle(independents)
    independents.sort(
        key=lambda x: (x.get("pace", 0) * 1.0 + x.get("consistency", 0) * 0.4),
        reverse=True,
    )

    # Fill remaining slots up to grid_size
    remaining = max(0, grid_size - len(final_grid))
    final_grid.extend(independents[:remaining])

    return final_grid


def roll_race_weather(track_profile):
    """
    Decide race-day weather once, so you can show a forecast before the player
    picks their risk level.
    Returns (is_wet, is_hot).
    """
    track_wet_chance = track_profile.get("wet_chance", WEATHER_WET_CHANCE)
    is_wet = random.random() < track_wet_chance

    base_hot_chance = track_profile.get("base_hot_chance", 0.2)
    is_hot = False
    if not is_wet:
        is_hot = random.random() < base_hot_chance

    return is_wet, is_hot


def record_race_result(state, time, season_week, race_name, is_wet, is_hot, finishers, retired):
    """
    Save one race to state.race_history and update state.driver_career totals.

    finishers: list of (driver_dict, performance)
    retired: list of (driver_dict, reason) where reason is "engine" or "crash" (or "unknown")
    """

    # Safety for old saves
    if not hasattr(state, "race_history") or state.race_history is None:
        state.race_history = []
    if not hasattr(state, "driver_career") or state.driver_career is None:
        state.driver_career = {}

    entry = {
        "year": time.year,
        "week": season_week,
        "race": race_name,
        "wet": bool(is_wet),
        "hot": bool(is_hot),
        "finishers": [],
        "dnfs": [],
    }

    # ---- finishers ----
    for pos, (d, _perf) in enumerate(finishers, start=1):
        pts = 0
        if CHAMPIONSHIP_ACTIVE and (pos - 1) < len(POINTS_TABLE):
            pts = POINTS_TABLE[pos - 1]

        prize = get_prize_for_race_and_pos(race_name, pos - 1)

        entry["finishers"].append({
            "pos": pos,
            "name": d.get("name"),
            "constructor": d.get("constructor"),
            "pts": pts,
            "prize": prize,
        })

        name = d.get("name")
        c = state.driver_career.get(name, {
            "starts": 0,
            "wins": 0,
            "podiums": 0,
            "dnfs": 0,
            "engine_dnfs": 0,
            "crash_dnfs": 0,
            "points": 0,
            "prize_money": 0,
            "best_finish": None,
        })

        c["starts"] += 1
        c["points"] += pts
        c["prize_money"] += prize

        # wins / podiums
        if pos == 1:
            c["wins"] += 1
            c["podiums"] += 1
        elif pos <= 3:
            c["podiums"] += 1

        # best finish
        if c["best_finish"] is None or pos < c["best_finish"]:
            c["best_finish"] = pos

        state.driver_career[name] = c

    # ---- DNFs ----
    for d, reason in retired:
        entry["dnfs"].append({
            "name": d.get("name"),
            "constructor": d.get("constructor"),
            "reason": reason,
        })

        name = d.get("name")
        c = state.driver_career.get(name, {
            "starts": 0,
            "wins": 0,
            "podiums": 0,
            "dnfs": 0,
            "engine_dnfs": 0,
            "crash_dnfs": 0,
            "points": 0,
            "prize_money": 0,
            "best_finish": None,
        })

        c["starts"] += 1
        c["dnfs"] += 1
        if reason == "engine":
            c["engine_dnfs"] += 1
        if reason == "crash":
            c["crash_dnfs"] += 1

        state.driver_career[name] = c

    state.race_history.append(entry)


def add_engine_failure_explanation(
    state,
    d,
    track_profile,
    is_hot,
    is_wet,
    perspective="neutral",
    breakdown=None,
):
    if breakdown is None:
        breakdown = [("a technical failure", 1.0)]

    top = breakdown[0][0] if breakdown else "a technical failure"

    if perspective == "player":
        state.news.append(
            f"Post-race inspection suggests {top} was the decisive factor in the failure."
        )
    else:
        state.news.append(
            f"Paddock analysis points to {top} as the likely cause."
        )


def add_crash_explanation(state, d, track_profile, is_hot, is_wet, perspective="neutral", breakdown=None):
    if breakdown is None:
        breakdown = [("a simple driving error", 1.0)]

    top = breakdown[0][0] if breakdown else "a simple driving error"

    if perspective == "player":
        state.news.append(
            f"Race control cite {top} as the key factor in the accident."
        )
    else:
        state.news.append(
            f"Observers suggest {top} played a major role in the crash."
        )


def run_ai_only_race(state, race_name, time, season_week, track_profile):
    """
    AI-only race simulation for weeks where the player does not/cannot compete.

    IMPORTANT:
    - This version includes engine failures + crashes (DNFs), using the same core logic
      style as run_race(), but without player wear/damage effects.
    - Fame/XP update is applied to FINISHERS only (DNFs don't gain post-race fame).
    """

    # Roll conditions for flavour + crash modifiers
    is_wet, is_hot = roll_race_weather(track_profile)

    finishers = []
    retired = []  # list of (driver, reason)

    track_pace_w = track_profile.get("pace_weight", 1.0)
    track_cons_w = track_profile.get("consistency_weight", 1.0)

    # Race length factor (endurance = more failures)
    race_distance_km = track_profile.get("race_distance_km", 250.0)
    race_length_factor = race_distance_km / 250.0

    reliability_mult = get_reliability_mult(time)
    crash_mult = get_crash_mult(time)

    event_grid = build_event_grid(state, time, race_name, track_profile)
    grid_size = len(event_grid)
    grid_risk_mult = 1.0 + max(0, grid_size - 12) * 0.01  # +1% per car above 12

    for d in event_grid:
        # Player shouldn't appear in AI-only race
        if state.player_driver is d:
            continue
        if state.player_constructor and d.get("constructor") == state.player_constructor:
            continue

        ctor_speed, ctor_reliability = get_ai_car_stats(d["constructor"])
        ctor_speed = max(1, ctor_speed)
        reliability = ctor_reliability

        # ---------- Performance roll (same vibe as your existing AI sim) ----------
        base = d["pace"] * track_pace_w + d["consistency"] * 0.4 * track_cons_w
        base += ctor_speed

        cons_factor = max(0.0, min(d["consistency"] / 10.0, 0.95))
        variance = (
            random.uniform(-1, 1)
            * (1 - cons_factor)
            * base
            * 0.25
        )
        performance = base + variance

        # Wet pace effect
        if is_wet:
            wet_factor = d.get("wet_skill", 5) / 10.0
            performance *= (0.9 + wet_factor * 0.3)

        # Heat pace effect (small)
        if is_hot:
            heat_handling = (d.get("mechanical_sympathy", 5) + d.get("consistency", 5)) / 20.0
            performance *= (0.97 + heat_handling * 0.06)

        # ---------- DNF logic (ported from run_race, simplified for AI) ----------
        mech = d.get("mechanical_sympathy", 5)
        aggression = d.get("aggression", 5)
        consistency = d.get("consistency", 5)
        wet_skill = d.get("wet_skill", 5)

        # Engine fail chance
        engine_fail_chance = (11 - reliability) * 0.02 * reliability_mult
        engine_fail_chance *= (1 + (5 - mech) * 0.05)
        engine_fail_chance *= track_profile.get("engine_danger", 1.0)
        engine_fail_chance *= race_length_factor

        # Hot-day engine stress (AI heat tolerance assumed average=5)
        if is_hot:
            heat_intensity = track_profile.get("heat_intensity", 1.0)
            engine_fail_chance *= heat_intensity

        # Crash chance
        base_crash_chance = (11 - consistency) * 0.012
        base_crash_chance *= (1 + (aggression - 5) * 0.05)
        base_crash_chance *= (1 + (5 - mech) * 0.03)

        crash_chance = base_crash_chance * crash_mult
        crash_chance *= track_profile.get("crash_danger", 1.0)

        # Wet -> more crashes, better wet_skill reduces it
        if is_wet:
            wet_factor = wet_skill / 10.0
            rain_crash_mult = 1.40 - wet_factor * 0.30
            crash_chance *= rain_crash_mult

        # Suspension affects crash risk (AI too)
        sus = get_suspension_value_for_driver(state, d)
        sus_importance = suspension_track_factor(track_profile)

        crash_sus_mult = 1.08 - (sus - 5) * 0.02
        crash_sus_mult = clamp(crash_sus_mult, 0.88, 1.15)
        crash_sus_mult = 1.0 + (crash_sus_mult - 1.0) * sus_importance

        crash_chance *= crash_sus_mult
        crash_chance *= grid_risk_mult

        # ---------- Resolve DNF ----------
        if random.random() < engine_fail_chance:
            retired.append((d, "engine"))
            state.news.append(f"{d['name']} ({d['constructor']}) retired with engine failure.")

            # --- simple breakdown so the news doesn't default to "general fatigue" ---
            breakdown = []

            reliability = max(1, ctor_reliability)
            mech = d.get("mechanical_sympathy", 5)

            reliability_mult = get_reliability_mult(time)
            race_distance_km = track_profile.get("race_distance_km", 250.0)
            race_length_factor = race_distance_km / 250.0

            # Start from baseline
            base_chance = (11 - reliability) * 0.02 * reliability_mult
            running = base_chance

            def add_factor(label, mult):
                nonlocal running
                extra = running * (mult - 1.0)
                if extra > 0:
                    breakdown.append((label, extra))
                running *= mult

            # Make reliability show up as a real contributor (lower reliability = more baseline risk)
            # Weight isn't perfect science — it's just to stop "generic fatigue" lines.
            reliability_weight = max(0.0, (11 - reliability) * 0.02 * reliability_mult)
            breakdown.append(("car reliability", reliability_weight))

            add_factor("driver mechanical sympathy", (1 + (5 - mech) * 0.05))
            add_factor("track engine strain", track_profile.get("engine_danger", 1.0))
            add_factor("race distance", race_length_factor)

            if is_hot:
                add_factor("heat intensity", track_profile.get("heat_intensity", 1.0))

            breakdown.sort(key=lambda x: x[1], reverse=True)
            if not breakdown:
                breakdown = [("a run of bad luck", 1.0)]

            add_engine_failure_explanation(
                state, d, track_profile, is_hot, is_wet,
                perspective="neutral",
                breakdown=breakdown
            )
            continue

        if random.random() < crash_chance:
            retired.append((d, "crash"))
            state.news.append(f"{d['name']} ({d['constructor']}) crashed out of the race.")
            add_crash_explanation(state, d, track_profile, is_hot, is_wet, perspective="neutral")

            # Check for injuries (player driver only)
            if state.player_driver and d['name'] == state.player_driver['name']:
                injury_roll = random.random()
                if injury_roll < 0.05:  # 5% chance of career-ending injury
                    state.player_driver_injury_severity = 3
                    state.player_driver_injury_weeks_remaining = 0  # Immediate retirement
                    state.news.append(f"TERRIBLE NEWS: {d['name']} has suffered a career-ending injury in the crash!")
                    state.news.append(f"{d['name']} will never race again. Your team must find a new driver.")
                    # Clear player driver
                    state.player_driver = None
                elif injury_roll < 0.20:  # 15% chance of serious injury (2-6 weeks)
                    state.player_driver_injury_severity = 2
                    weeks_out = random.randint(2, 6)
                    state.player_driver_injury_weeks_remaining = weeks_out
                    state.news.append(f"BAD NEWS: {d['name']} has suffered a serious injury in the crash!")
                    state.news.append(f"{d['name']} will be unable to drive for {weeks_out} weeks.")
                else:  # 80% chance of minor injury (1-2 weeks)
                    state.player_driver_injury_severity = 1
                    weeks_out = random.randint(1, 2)
                    state.player_driver_injury_weeks_remaining = weeks_out
                    state.news.append(f"{d['name']} has suffered a minor injury in the crash.")
                    state.news.append(f"{d['name']} will be unable to drive for {weeks_out} week{'s' if weeks_out > 1 else ''}.")

                state.player_driver_injured = state.player_driver_injury_weeks_remaining > 0

            continue

        # Survived -> classified finisher
        finishers.append((d, performance))

    if not finishers:
        state.news.append(f"{race_name}: chaotic scenes — no cars reach the finish.")
        record_race_result(state, time, season_week, race_name, is_wet, is_hot, finishers, retired)
        state.completed_races.add(season_week)
        return

    # Sort finishers fastest to slowest
    finishers.sort(key=lambda x: x[1], reverse=True)

    # ------------------------------
    # DEMO FINALE (AI-only): force fatal DNF so they cannot be classified
    # ------------------------------
    victim = maybe_trigger_demo_finale(state, time, race_name)
    if victim:
        vname = victim.get("name")

        # If they were a finisher, pull them out of classification
        before_n = len(finishers)
        finishers = [(drv, perf) for (drv, perf) in finishers if drv.get("name") != vname]

        # Ensure we log it as a retirement
        retired.append((victim, "crash"))

        if len(finishers) != before_n:
            state.news.append(f"Classification update: {vname} is not classified after the incident.")

        # Remove from global pool so future seasons are consistent
        from gmr.data import drivers as global_drivers
        if victim in global_drivers:
            global_drivers.remove(victim)

    # Fame/XP progression should apply to FINISHERS, not entrants
    fame_mult = track_profile.get("fame_mult", 1.0)
    xp_mult = track_profile.get("xp_mult", 1.0)

    update_fame_after_race(
        finishers,
        fame_mult=fame_mult,
        race_name=race_name,
        season_week=season_week,
        year=time.year
    )

    # Sponsor story event: driver promo at Fame 2+
    from gmr.sponsorship import maybe_gallant_driver_promo
    maybe_gallant_driver_promo(state, time)

    update_driver_progress(state, finishers, time, xp_mult=xp_mult)

    # Championship points (finishers only)
    if CHAMPIONSHIP_ACTIVE:
        for pos, (d, _) in enumerate(finishers):
            if pos < len(POINTS_TABLE):
                state.points[d["name"]] += POINTS_TABLE[pos]

    # Headline with enhanced media flavor
    winner = finishers[0][0]
    if len(finishers) > 1:
        runner_up = finishers[1][0]
        headline = (
            f"{race_name}: {winner['name']} wins for {winner['constructor']}, "
            f"ahead of {runner_up['name']}."
        )
    else:
        headline = f"{race_name}: {winner['name']} wins for {winner['constructor']}."
    state.news.append(headline)

    # Add atmospheric and media coverage based on race conditions
    weather_descriptions = []
    if is_wet:
        weather_descriptions.extend([
            "Dramatic wet-weather victory as rain made conditions treacherous.",
            "Spectacular driving in the pouring rain - a true test of skill.",
            "Rain-soaked triumph as drivers battled aquaplaning and poor visibility.",
        ])
    elif is_hot:
        weather_descriptions.extend([
            "Scorching conditions tested cars and drivers to their limits.",
            "Heat haze shimmered over the track as temperatures soared.",
            "Tires and engines pushed to the brink in the blazing heat.",
        ])
    else:
        weather_descriptions.extend([
            "Perfect racing conditions produced an exciting spectacle.",
            "Clear skies set the stage for a thrilling motor race.",
            "Sunshine and ideal weather delighted the crowd.",
        ])
    if weather_descriptions:
        state.news.append(random.choice(weather_descriptions))

    record_race_result(state, time, season_week, race_name, is_wet, is_hot, finishers, retired)


def get_qualifying_strategy_choice(state, track_profile, is_wet_quali):
    """
    Present the player with qualifying strategy options.
    Returns a dict with performance modifiers and risk factors.
    """
    if not state.player_driver:
        return None
    
    track_name = track_profile.get("name", "the circuit")
    weather = "Wet" if is_wet_quali else "Dry"
    
    print(f"\n{'='*60}")
    print(f"  🏁 QUALIFYING SESSION — {weather} Conditions")
    print(f"{'='*60}")
    
    driver_name = state.player_driver.get("name", "Your driver")
    aggression = state.player_driver.get("aggression", 5)
    consistency = state.player_driver.get("consistency", 5)
    
    print(f"\n  {driver_name} is ready to set a qualifying time.")
    print(f"  Driver traits: Aggression {aggression}/10, Consistency {consistency}/10")
    
    print(f"\n  Choose your qualifying approach:\n")
    
    print("  1. 🌅 GO OUT EARLY")
    print("     Beat the traffic, get clean laps. Lower risk but track may")
    print("     not be fully rubbered-in yet. Conservative but reliable.")
    print("")
    print("  2. ⏰ GO OUT LATE")
    print("     Wait for optimal track conditions. Higher risk of traffic")
    print("     or weather changes, but potentially faster lap times.")
    print("")
    print("  3. 🎯 BANKER LAP FIRST")
    print("     Set a safe time early, then push harder on second run.")
    print("     Balanced approach with two chances at a good time.")
    print("")
    print("  4. 💥 ALL-OUT ATTACK")
    print("     Maximum aggression from the start. Push to the absolute")
    print("     limit — could be pole or could be the barriers.")
    print("")
    print("  5. 🧘 CALCULATED PRECISION")
    print("     Focus on perfect execution over raw pace. Minimize mistakes")
    print("     but sacrifice some ultimate speed for consistency.")
    
    while True:
        choice = input("\n  Your choice (1-5): ").strip()
        if choice in ("1", "2", "3", "4", "5"):
            break
        print("  Please enter 1, 2, 3, 4, or 5.")
    
    # Define strategy effects
    strategies = {
        "1": {  # Go out early
            "name": "Go Out Early",
            "perf_bonus": -0.02,  # Slight pace disadvantage (track not optimal)
            "variance_low": 0.96,  # Less variance (clean track)
            "variance_high": 1.02,
            "risk_factor": 0.05,  # Low risk of disaster
            "upside_chance": 0.15,  # Low chance of exceptional lap
            "flavor_good": "found clean air and set a solid banker lap",
            "flavor_great": "nailed a perfect lap on the empty track — stunning!",
            "flavor_bad": "struggled on the green track surface",
            "flavor_disaster": "made an error on cold tyres and binned it",
        },
        "2": {  # Go out late
            "name": "Go Out Late",
            "perf_bonus": 0.03,  # Potential pace advantage (rubbered track)
            "variance_low": 0.92,  # High variance
            "variance_high": 1.08,
            "risk_factor": 0.18,  # Medium-high risk
            "upside_chance": 0.30,  # Good chance of special lap
            "flavor_good": "timed the run perfectly as the track reached peak grip",
            "flavor_great": "delivered a stunning final-minute lap on the rubbered circuit!",
            "flavor_bad": "got stuck in traffic and couldn't get a clean lap",
            "flavor_disaster": "ran out of time after traffic delays — disaster!",
        },
        "3": {  # Banker lap first
            "name": "Banker Lap First",
            "perf_bonus": 0.0,  # Neutral base performance
            "variance_low": 0.95,  # Moderate variance
            "variance_high": 1.05,
            "risk_factor": 0.08,  # Low-medium risk
            "upside_chance": 0.22,  # Decent chance of improvement
            "flavor_good": "set a safe time then improved on the second run",
            "flavor_great": "the banker lap was already quick, then the second run was even better!",
            "flavor_bad": "couldn't improve on the second run",
            "flavor_disaster": "spun on the improvement lap, left with the banker time",
        },
        "4": {  # All-out attack
            "name": "All-Out Attack",
            "perf_bonus": 0.05,  # Strong pace potential
            "variance_low": 0.88,  # Very high variance
            "variance_high": 1.12,
            "risk_factor": 0.25,  # High risk
            "upside_chance": 0.35,  # Good chance of brilliance
            "flavor_good": "pushed hard and extracted maximum performance",
            "flavor_great": "delivered an absolutely heroic lap on the ragged edge!",
            "flavor_bad": "overdrove the car and lost time with minor mistakes",
            "flavor_disaster": "pushed too hard and crashed into the barriers!",
        },
        "5": {  # Calculated precision
            "name": "Calculated Precision",
            "perf_bonus": -0.01,  # Slight pace sacrifice
            "variance_low": 0.98,  # Very low variance
            "variance_high": 1.02,
            "risk_factor": 0.03,  # Very low risk
            "upside_chance": 0.08,  # Rare to exceed expectations
            "flavor_good": "executed a clean, controlled qualifying lap",
            "flavor_great": "the perfectly judged lap was faster than expected!",
            "flavor_bad": "played it too safe and left time on the table",
            "flavor_disaster": "a moment of hesitation cost several tenths",
        },
    }
    
    strategy = strategies[choice]
    
    # Modify based on driver traits
    # High aggression helps attack strategies, hurts conservative ones
    aggression_effect = (aggression - 5) * 0.005
    if choice == "4":  # All-out attack
        strategy["perf_bonus"] += aggression_effect * 2
        strategy["risk_factor"] -= aggression_effect  # Aggressive drivers handle it better
    elif choice in ("1", "5"):  # Conservative strategies
        strategy["perf_bonus"] -= aggression_effect  # Aggressive drivers get frustrated
    
    # High consistency reduces risk and variance
    consistency_effect = (consistency - 5) * 0.01
    strategy["risk_factor"] -= consistency_effect
    strategy["variance_low"] += consistency_effect * 0.5
    strategy["variance_high"] -= consistency_effect * 0.5
    
    # Wet conditions amplify everything
    if is_wet_quali:
        strategy["risk_factor"] *= 1.5
        strategy["variance_low"] -= 0.02
        strategy["variance_high"] += 0.03
    
    return strategy


def simulate_qualifying(state, race_name, time, track_profile):
    """
    Simulate a single qualifying session for this race.
    Now includes player strategy choice mini-game.
    """
    results = []
    grid_bonus = {}

    is_wet_quali = random.random() < track_profile.get("wet_chance", WEATHER_WET_CHANCE)
    track_pace_w = track_profile.get("pace_weight", 1.0)
    track_cons_w = track_profile.get("consistency_weight", 1.0)

    event_grid = build_event_grid(state, time, race_name, track_profile)
    
    # Get player strategy if they're in the grid
    player_in_grid = state.player_driver and state.player_driver in event_grid
    player_strategy = None
    player_outcome = None
    
    if player_in_grid:
        player_strategy = get_qualifying_strategy_choice(state, track_profile, is_wet_quali)

    for d in event_grid:
        # Track-specific pace weighting
        base_pace = d["pace"] * track_pace_w
        base_cons = d["consistency"] * 0.4 * track_cons_w

        # Car performance for player vs AI
        if d == state.player_driver:
            car_speed = get_car_speed_for_track(state, track_profile)
        else:
            car_speed, _ = get_ai_car_stats(d["constructor"])

        perf = base_pace + base_cons + car_speed

        if is_wet_quali:
            wet_factor = d.get("wet_skill", 5) / 10.0
            perf *= (0.9 + wet_factor * 0.3)

        # Apply player strategy effects
        if d == state.player_driver and player_strategy:
            # Apply base performance modifier
            perf *= (1.0 + player_strategy["perf_bonus"])
            
            # Roll for outcome
            roll = random.random()
            
            if roll < player_strategy["risk_factor"]:
                # Disaster! Major time loss
                perf *= random.uniform(0.82, 0.90)
                player_outcome = "disaster"
            elif roll < player_strategy["risk_factor"] + (1 - player_strategy["risk_factor"]) * player_strategy["upside_chance"]:
                # Great lap! Exceeded expectations
                perf *= random.uniform(1.04, 1.08)
                player_outcome = "great"
            elif roll < player_strategy["risk_factor"] + 0.35:
                # Below expectations
                perf *= random.uniform(0.94, 0.98)
                player_outcome = "bad"
            else:
                # Good solid lap
                perf *= random.uniform(0.99, 1.03)
                player_outcome = "good"
            
            # Apply strategy-specific variance
            variance = random.uniform(player_strategy["variance_low"], player_strategy["variance_high"])
            perf *= variance
        else:
            # AI variance (same as before)
            perf *= random.uniform(0.94, 1.06)

        results.append((d, perf))

    # Sort by performance
    results.sort(key=lambda x: x[1], reverse=True)

    # Grid bonuses are a tiny advantage for qualifying position
    for i, (d, _perf) in enumerate(results):
        grid_bonus[d["name"]] = 1.00 - (i * 0.003)

    # Find player position for impact reporting
    player_pos = None
    if player_in_grid:
        for i, (d, _) in enumerate(results):
            if d == state.player_driver:
                player_pos = i + 1
                break
    
    # Report player strategy outcome
    if player_strategy and player_outcome:
        print(f"\n{'='*60}")
        print(f"  QUALIFYING RESULT")
        print(f"{'='*60}")
        
        flavor = player_strategy.get(f"flavor_{player_outcome}", "completed qualifying")
        driver_name = state.player_driver.get("name", "Your driver")
        
        outcome_emoji = {
            "disaster": "💥",
            "bad": "😓",
            "good": "✅",
            "great": "🌟",
        }
        
        print(f"\n  {outcome_emoji.get(player_outcome, '🏎️')} {driver_name} {flavor}")
        print(f"\n  Strategy: {player_strategy['name']}")
        print(f"  Grid Position: P{player_pos}")
        
        if player_outcome == "great":
            print(f"\n  💪 Excellent session! Your strategy paid off brilliantly.")
        elif player_outcome == "good":
            print(f"\n  👍 Solid qualifying. The strategy worked as planned.")
        elif player_outcome == "bad":
            print(f"\n  😤 Disappointing. The approach didn't quite work out.")
        else:  # disaster
            print(f"\n  😱 Nightmare qualifying! This will hurt in the race.")
        
        input("\n  Press Enter to continue...")
        
        # Store outcome for potential race effects
        state.last_quali_strategy = player_strategy["name"]
        state.last_quali_outcome = player_outcome

    # Qualifying summary for news
    if len(results) >= 2:
        p1 = results[0][0]
        p2 = results[1][0]
        if p1["constructor"] == p2["constructor"]:
            summary = (
                f"{p1['name']} takes pole for {p1['constructor']} with teammate {p2['name']} alongside."
            )
        else:
            summary = (
                f"{p1['name']} takes pole for {p1['constructor']}, "
                f"{p2['name']} joins on the front row."
            )
    elif len(results) == 1:
        p1 = results[0][0]
        summary = f"{p1['name']} takes pole for {p1['constructor']}"
    else:
        summary = "Qualifying completed."

    session_weather = "wet" if is_wet_quali else "dry"
    state.news.append(
        f"Qualifying for {race_name} ({session_weather} session): {summary}"
    )

    # Results (Q1/Q2/Q3...) into news
    state.news.append("Qualifying results:")
    for pos, (d, _) in enumerate(results, start=1):
        marker = " ⬅️ YOU" if d == state.player_driver else ""
        state.news.append(f"Q{pos}: {d['name']} ({d['constructor']}){marker}")

    # Store quali results in state for overtake calculation
    state.last_quali_results = results

    return results, grid_bonus, is_wet_quali


def run_race(state, race_name, time, season_week, grid_bonus, is_wet, is_hot):
    state.news.append(f"=== {race_name} ===")

    # How swingy race performance is (qualifying is higher)
    variance_scale = 0.25

    if state.player_driver:
        eid = state.current_engine.get("unit_id") if state.current_engine else None
        state.news.append(
            f"DEBUG ENGINE: unit_id={eid}, wear={state.engine_wear:.0f}%, health={state.engine_health:.0f}%")

    # PATCH : remember if we've ever completed Vallone GP
    if race_name == "Vallone GP":
        state.ever_completed_vallone = True

    finishers = []
    dnf_drivers = []

    # Track why drivers retired this race (engine vs crash etc.)
    retire_reasons = {}  # driver_name -> "engine" or "crash"

    track_profile = tracks.get(
        race_name,
        {
            "engine_danger": 1.0,
            "crash_danger": 1.0,
            "pace_weight": 1.0,
            "consistency_weight": 1.0,
            "wet_chance": WEATHER_WET_CHANCE,
            "base_hot_chance": 0.2,
            "heat_intensity": 1.0,
            "race_distance_km": 250.0,
        },
    )

    # Race length factor: how long this race is relative to a baseline 250 km
    race_distance_km = track_profile.get("race_distance_km", 250.0)
    race_length_factor = race_distance_km / 250.0

    # ------------------------------
    # ATTENDANCE CALCULATION (World Economy)
    # ------------------------------
    attendance = 50000  # default
    attendance_details = {}
    
    if hasattr(state, 'world_economy'):
        from gmr.world_economy import COUNTRIES
        track_country = track_profile.get("country", "Italy")
        event_prestige = track_profile.get("fame_mult", 1.0) * 2  # Track prestige estimate
        player_prestige = state.prestige if hasattr(state, 'prestige') else 0
        
        attendance, attendance_details = state.world_economy.calculate_attendance(
            race_name, 
            track_profile,
            player_prestige,
            event_prestige
        )
        
        # Store for later use in prestige calculations
        state.last_race_attendance = attendance
        state.last_race_attendance_details = attendance_details
        
        # Display attendance news
        attendance_news = state.world_economy.format_attendance_news(
            race_name, attendance, attendance_details
        )
        state.news.append(attendance_news)
        
        # Check for any active events affecting this race
        active_events = attendance_details.get("active_events", [])
        if active_events:
            events_str = ", ".join(active_events[:2])
            if attendance_details.get("event_modifier", 1.0) > 1.0:
                state.news.append(f"📈 Regional boost: {events_str}")
            elif attendance_details.get("event_modifier", 1.0) < 1.0:
                state.news.append(f"📉 Regional issues: {events_str}")

    # ------------------------------
    # WEATHER: WET vs DRY + HOT DAYS
    # ------------------------------

    if is_wet:
        state.news.append("Rain falls over the circuit – conditions are WET.")
    else:
        if is_hot:
            state.news.append("Baking heat grips the circuit – HOT and dry conditions.")
        else:
            state.news.append("Skies stay clear – conditions are DRY.")

    event_grid = build_event_grid(state, time, race_name, track_profile)
    grid_size = len(event_grid)
    grid_risk_mult = 1.0 + max(0, grid_size - 12) * 0.01  # +1% per car above 12

    # Check for home race heroes in the grid
    home_heroes = []
    track_country = track_profile.get("country", "")
    for d in event_grid:
        if is_home_race(d, track_profile):
            fame = d.get("fame", 0)
            if fame >= 3:  # Only report notable drivers
                home_heroes.append(d.get("name"))
    
    if home_heroes:
        if len(home_heroes) == 1:
            state.news.append(f"🏠 Home race for {home_heroes[0]}! The local crowd cheers their hero.")
        else:
            heroes_str = ", ".join(home_heroes[:3])
            if len(home_heroes) > 3:
                heroes_str += f" and {len(home_heroes) - 3} others"
            state.news.append(f"🏠 Home race for {heroes_str}! Local drivers will be fired up.")

    stage_incidents = precompute_ai_stage_incidents(
        event_grid,
        state,
        track_profile,
        time,
        is_wet,
        is_hot,
        grid_risk_mult,
        race_length_factor,
    )

    # Quali results (stored in state from simulate_qualifying)
    quali_results = getattr(state, "last_quali_results", [])
    player_in_grid = any(d == state.player_driver for d in event_grid)

    # ==========================================================================
    # NEW INTERACTIVE RACE SIMULATION
    # ==========================================================================
    if player_in_grid:
        consume_tyre_set(state, race_name, "race start")
        
        # Create the race simulator with accurate position tracking
        simulator = RaceSimulator(
            event_grid=event_grid,
            quali_results=quali_results,
            track_profile=track_profile,
            state=state,
            is_wet=is_wet,
            is_hot=is_hot,
            time=time,
            grid_risk_mult=grid_risk_mult,
            race_length_factor=race_length_factor
        )
        
        # Show starting grid
        print(f"\n{'='*60}")
        print(f"  RACE START — {race_name}")
        print(f"{'='*60}")
        standings = simulator.get_current_standings()
        print("\n📊  STARTING GRID:")
        player_name = state.player_driver.get("name") if state.player_driver else None
        for pos, d, _ in standings[:10]:
            name = d.get("name")
            constructor = d.get("constructor", "")
            if name == player_name:
                print(f"    \x1b[32mP{pos}. {name} ({constructor})\x1b[0m")
            else:
                print(f"    P{pos}. {name} ({constructor})")
        
        # Run interactive stages - decisions THEN simulation THEN display
        stage_mods = run_interactive_race_stages(simulator, state, race_name, is_wet, is_hot)
        
        # Get final results from simulator
        finishers, dnf_drivers, retire_reasons = simulator.get_final_results()
        
        # Show final results
        print(f"\n{'='*60}")
        print(f"  RACE COMPLETE — FINAL CLASSIFICATION")
        print(f"{'='*60}")
        
    else:
        # AI-only race - use simulator without interaction
        simulator = RaceSimulator(
            event_grid=event_grid,
            quali_results=quali_results,
            track_profile=track_profile,
            state=state,
            is_wet=is_wet,
            is_hot=is_hot,
            time=time,
            grid_risk_mult=grid_risk_mult,
            race_length_factor=race_length_factor
        )
        
        # Simulate all stages with neutral strategy
        for stage_idx in range(len(STAGE_LABELS)):
            simulator.simulate_stage(stage_idx, player_strategy_mult=1.0)
        
        finishers, dnf_drivers, retire_reasons = simulator.get_final_results()
        stage_mods = {
            "performance_mult": 1.0,
            "engine_fail_mult": 1.0,
            "crash_mult": 1.0,
        }

    # Sort finishers by performance (simulator already does this but be safe)
    finishers.sort(key=lambda x: x[1], reverse=True)
    
    # ------------------------------
    # DEMO FINALE (player race): force fatal DNF so they cannot be classified
    # ------------------------------
    victim = maybe_trigger_demo_finale(state, time, race_name)
    if victim:
        vname = victim.get("name")

        # Remove from classified finishers
        finishers = [(drv, perf) for (drv, perf) in finishers if drv.get("name") != vname]

        # Treat as crash retirement for prestige logic
        retire_reasons[vname] = "crash"

        # If victim is player's driver, they are a DNF and the contract ends brutally
        if state.player_driver and state.player_driver.get("name") == vname:
            dnf_drivers.append(state.player_driver)
            state.demo_player_died = True  # just a flag for after-results cleanup

        # Remove from global driver list for future seasons
        from gmr.data import drivers as global_drivers
        if victim in global_drivers:
            global_drivers.remove(victim)

    # ------------------------------
    # CAR COMFORT XP (player only)
    # ------------------------------
    if state.player_driver:
        finished = any(d == state.player_driver for d, _ in finishers)
        started = (state.player_driver in dnf_drivers) or finished

        if started:
            gain = 1.0 if finished else 0.35
            state.player_driver["car_xp"] = round(
                min(10.0, float(state.player_driver.get("car_xp", 0.0)) + gain), 2
            )

    # Track your driver's results with your team
    player_finish_pos = None
    if state.player_driver:
        for pos, (d, _) in enumerate(finishers):
            if d == state.player_driver:
                player_finish_pos = pos
                break

        # They started the race, even if they DNF'd
        state.races_entered_with_team += 1

        if player_finish_pos is not None:
            # Wins / podiums
            if player_finish_pos == 0:
                state.wins_with_team += 1
                state.podiums_with_team += 1
            elif player_finish_pos <= 2:
                state.podiums_with_team += 1

            # Championship points with your team
            if player_finish_pos < len(POINTS_TABLE):
                state.points_with_team += POINTS_TABLE[player_finish_pos]

    fame_mult = track_profile.get("fame_mult", 1.0)
    xp_mult = track_profile.get("xp_mult", 1.0)

    update_fame_after_race(
        finishers,
        fame_mult=fame_mult,
        race_name=race_name,
        season_week=season_week,
        year=time.year
    )

    # Sponsor story event: driver promo at Fame 2+
    from gmr.sponsorship import maybe_gallant_driver_promo
    maybe_gallant_driver_promo(state, time)

    player_xp_gain = update_driver_progress(state, finishers, time, xp_mult=xp_mult)
    player_xp_gain += grant_participation_xp_for_dnfs(state, dnf_drivers, time, xp_mult=xp_mult)

    # ------------------------------
    # CHAMPIONSHIP POINTS + PRIZE MONEY
    # ------------------------------

    # Award points ONLY if a championship exists
    if CHAMPIONSHIP_ACTIVE:
        for pos, (drv, _) in enumerate(finishers):
            if pos < len(POINTS_TABLE):
                state.points[drv["name"]] += POINTS_TABLE[pos]

    # Pay prize money ONLY to the player's team (your cut of organiser prize)
    if state.player_driver and player_finish_pos is not None:
        raw_prize = get_prize_for_race_and_pos(race_name, player_finish_pos)  # player_finish_pos is 0-based
        if raw_prize > 0:
            prize_cut = int(raw_prize * CONSTRUCTOR_SHARE)

            state.money += prize_cut
            state.constructor_earnings += prize_cut
            state.last_week_prize_income += prize_cut
            state.last_week_income += prize_cut

    # Appearance money (paid for taking the start; even if you DNF)
    if state.player_driver:
        pay_appearance_money(state, race_name)

    # ------------------------------
    # SPONSORSHIP PAYMENTS
    # ------------------------------
    if state.sponsor_active and state.player_driver:
        # Appearance fee is paid as long as the car turned up for the race,
        # even if it retires
        state.sponsor_races_started += 1

        mult = getattr(state, "sponsor_rate_multiplier", 1.0)

        # Appearance money
        appearance = int(60 * mult)
        state.money += appearance
        state.last_week_income += appearance
        state.last_week_sponsor_income += appearance
        state.constructor_earnings += appearance

        # Points bonus ONLY if a championship exists
        if CHAMPIONSHIP_ACTIVE and player_finish_pos is not None and player_finish_pos < len(POINTS_TABLE):
            pts = POINTS_TABLE[player_finish_pos]
            points_bonus = int(pts * 10 * mult)
            state.money += points_bonus
            state.last_week_income += points_bonus
            state.last_week_sponsor_income += points_bonus
            state.constructor_earnings += points_bonus

        # Podium bonus (always valid, championship or not)
        if player_finish_pos is not None and player_finish_pos <= 2:
            state.sponsor_podiums += 1
            podium_bonus = int(120 * mult)
            state.money += podium_bonus
            state.last_week_income += podium_bonus
            state.last_week_sponsor_income += podium_bonus
            state.constructor_earnings += podium_bonus

        # Check sponsor goals
        if not state.sponsor_goals_races_started and state.sponsor_races_started >= 3:
            state.sponsor_goals_races_started = True
            bonus = 500  # bonus for completing races started goal
            state.money += bonus
            state.last_week_income += bonus
            state.last_week_sponsor_income += bonus
            state.constructor_earnings += bonus
            state.news.append(f"Sponsor bonus: Completed 3 races started goal! +£{bonus}")

        if not state.sponsor_goals_podium and state.sponsor_podiums >= 1:
            state.sponsor_goals_podium = True
            bonus = 1000  # bonus for completing podium goal
            state.money += bonus
            state.last_week_income += bonus
            state.last_week_sponsor_income += bonus
            state.constructor_earnings += bonus
            state.news.append(f"Sponsor bonus: Achieved first podium! +£{bonus}")

    # Pay driver salary ONLY on race weeks (mercenary model)
    if state.player_driver and state.driver_pay > 0:
        state.money -= state.driver_pay
        state.last_week_driver_pay = state.driver_pay
        state.last_week_outgoings += state.driver_pay

    # ------------------------------
    # PATCH D: POST-RACE DEBRIEF (YOUR TEAM)
    # ------------------------------
    if state.player_driver:
        # Store race-scoped numbers for UI/finances if needed
        state.last_race_xp_gained = player_xp_gain
        state.last_race_prize_gained = state.last_week_prize_income
        state.last_race_sponsor_gained = state.last_week_sponsor_income
        state.last_race_driver_pay = state.last_week_driver_pay

        team_name = state.player_constructor or "Your team"
        driver_name = state.player_driver["name"]

        # How close to next stat tick?
        current_xp_bank = state.player_driver.get("xp", 0.0)
        xp_to_next = max(0.0, 5.0 - current_xp_bank)

        state.news.append("")
        state.news.append(f"--- Post-Race Debrief ({team_name}) ---")
        state.news.append(f"Driver: {driver_name}")

        # XP line
        state.news.append(
            f"Experience gained: +{player_xp_gain:.1f} XP "
            f"(banked: {current_xp_bank:.1f}/5.0, {xp_to_next:.1f} to next improvement roll)"
        )

        # Money breakdown
        prize = state.last_week_prize_income
        sponsor = state.last_week_sponsor_income
        appearance = getattr(state, "last_week_appearance_income", 0)
        travel = getattr(state, "last_week_travel_cost", 0)
        pay = state.last_week_driver_pay

        state.news.append("Financial rundown:")
        state.news.append(f"  Prize money (your cut): +£{prize}")
        state.news.append(f"  Sponsor income: +£{sponsor}")
        state.news.append(f"  Appearance / start money: +£{appearance}")
        state.news.append(f"  Travel & logistics: -£{travel}")
        state.news.append(f"  Driver pay: -£{pay}")

        net = (prize + sponsor + appearance) - (travel + pay)
        sign = "+" if net >= 0 else "-"
        state.news.append(f"  Net from race weekend: {sign}£{abs(net)}")

    # Race classification: show ALL classified finishers plus prize money
    state.news.append("Race Results:")
    for pos, (d, _) in enumerate(finishers):
        place = pos + 1

        prize = get_prize_for_race_and_pos(race_name, pos)

        line = f"{place}. {d['name']} ({d['constructor']})"

        # Only show points if the championship exists
        if CHAMPIONSHIP_ACTIVE:
            pts = POINTS_TABLE[pos] if pos < len(POINTS_TABLE) else 0
            line += f" - {pts} pts"

        if prize > 0:
            line += f", Prize: £{prize}"
            if d == state.player_driver:
                ctor_share = int(prize * CONSTRUCTOR_SHARE)
                line += f" (your cut: £{ctor_share})"

        state.news.append(line)

    # Save podium (top 3 finishers) for calendar display
    top3 = []
    for pos, (d, _) in enumerate(finishers[:3]):
        top3.append((d["name"], d["constructor"]))
    state.podiums[season_week] = top3
    state.podiums_year = time.year

    # --- Prestige gains for the player team (now fame-weighted) ---
    if state.player_driver:
        fame = state.player_driver.get("fame", 0)

        # Step 1: base prestige change (same as before)
        base_change = 0.0

        if player_finish_pos is not None:
            # Classified finish
            if player_finish_pos == 0:
                base_change = 3.0   # win
            elif player_finish_pos == 1:
                base_change = 2.0   # P2
            elif player_finish_pos == 2:
                base_change = 1.5   # P3
            elif player_finish_pos < len(POINTS_TABLE):
                base_change = 1.0   # points but no podium
            else:
                base_change = 0.3   # solid finish
        else:
            # DNF – split by cause
            reason = retire_reasons.get(state.player_driver["name"])

            if reason == "engine":
                # Mechanical DNF – frustrating, but more “unlucky”
                base_change = -0.2
            elif reason == "crash":
                # Crash DNF – more of a black mark
                base_change = -0.8
            else:
                base_change = -0.5

        # Step 2: fame multiplier (unchanged)
        fame_capped = min(fame, 8)

        if base_change > 0:
            mult = 1.0 + fame_capped * 0.07
        elif base_change < 0:
            mult = 1.0 + fame_capped * 0.05
        else:
            mult = 1.0

        change = base_change * mult

        # Step 3: Attendance multiplier (bigger crowds = more exposure = more prestige change)
        if hasattr(state, 'world_economy') and hasattr(state, 'last_race_attendance'):
            attendance_mult = state.world_economy.get_fame_modifier_from_attendance(
                state.last_race_attendance
            )
            change *= attendance_mult
            
            # Log the effect if significant
            if attendance_mult > 1.2:
                state.news.append(f"📺 Huge crowd amplifies your reputation! (x{attendance_mult:.2f} prestige)")
            elif attendance_mult < 0.8:
                state.news.append(f"📉 Small crowd limits exposure. (x{attendance_mult:.2f} prestige)")

        before = state.prestige
        state.prestige = max(0.0, min(100.0, state.prestige + change))

    # --- Post-race wear (player car only) ---
    # Calculate wear multiplier from stage choices first (used by both sections)
    avg_stage_wear = 1.0  # default
    if state.player_driver:
        stage_wear_acc = getattr(state, 'stage_wear_accumulator', 0.0)
        stage_count = getattr(state, 'stage_count', 0)
        
        if stage_count > 0:
            # Average wear multiplier from all stage decisions
            avg_stage_wear = stage_wear_acc / stage_count
        else:
            # Fallback to pre-race risk_multiplier if no stages ran
            avg_stage_wear = getattr(state, "risk_multiplier", 1.0)
        
        # Clear the accumulators for next race
        state.stage_wear_accumulator = 0.0
        state.stage_count = 0

    if state.player_driver:
        base_engine_wear = 8.0    # typical GP
        base_chassis_wear = 5.0   # chassis ages a bit slower

        danger_factor_engine = track_profile.get("engine_danger", 1.0)
        danger_factor_chassis = track_profile.get("crash_danger", 1.0)
        
        # Apply stage-based wear: Push all stages = 1.4x, Conserve all = 0.7x
        engine_wear_loss = base_engine_wear * race_length_factor * danger_factor_engine * avg_stage_wear
        chassis_wear_loss = base_chassis_wear * race_length_factor * danger_factor_chassis * avg_stage_wear

        sus = int(state.current_chassis.get("suspension", 5)) if state.current_chassis else 5
        sus_importance = suspension_track_factor(track_profile)

        wear_sus_mult = 1.06 - (sus - 5) * 0.015
        wear_sus_mult = clamp(wear_sus_mult, 0.90, 1.12)
        wear_sus_mult = 1.0 + (wear_sus_mult - 1.0) * sus_importance

        chassis_wear_loss *= wear_sus_mult

        # Heat cooks engines; wet races are slightly gentler on the chassis
        if is_hot:
            engine_wear_loss *= 1.25
        if is_wet:
            chassis_wear_loss *= 0.9

        # Small randomness so it isn't totally deterministic
        engine_wear_loss *= random.uniform(0.8, 1.2)
        chassis_wear_loss *= random.uniform(0.8, 1.2)

        # Apply to condition, clamp at 0
        old_engine = state.engine_wear
        old_chassis = state.chassis_wear

        state.engine_wear = max(0.0, state.engine_wear - engine_wear_loss)
        state.chassis_wear = max(0.0, state.chassis_wear - chassis_wear_loss)

        state.news.append(
            f"Post-race inspection: engine {old_engine:.0f}% → {state.engine_wear:.0f}%, "
            f"chassis {old_chassis:.0f}% → {state.chassis_wear:.0f}%."
        )

    # --- Long-term wear from this race (player car only) ---
    if state.player_driver:
        # Base wear from track + distance
        engine_base_wear = 4.0 * race_length_factor * track_profile.get("engine_danger", 1.0)
        chassis_base_wear = 3.0 * race_length_factor * track_profile.get("crash_danger", 1.0)

        # Use the same stage-based wear multiplier
        engine_wear = engine_base_wear * avg_stage_wear
        chassis_wear = chassis_base_wear * avg_stage_wear

        # Extra punishment if you actually finished the full distance
        player_finished = any(d == state.player_driver for d, _ in finishers)
        if player_finished:
            engine_wear *= 1.2
            chassis_wear *= 1.2
        else:
            # If you retired early, you spared some miles
            engine_wear *= 0.8
            chassis_wear *= 0.8

        # Apply wear and clamp
        state.engine_health = max(0.0, state.engine_health - engine_wear)
        state.chassis_health = max(0.0, state.chassis_health - chassis_wear)

    # Small news blurbs at thresholds – match what the player sees
    if state.engine_wear < 40:
        state.news.append(
            "Your mechanics warn that the engine is getting very tired (<40% condition)."
        )
    elif state.engine_wear < 70:
        state.news.append(
            "The engine is showing its age – performance and reliability may start to drop."
        )

    if state.chassis_wear < 40:
        state.news.append(
            "Your chassis is badly fatigued – any big hit could write it off."
        )
    elif state.chassis_wear < 70:
        state.news.append(
            "Cracks and flex are appearing in the chassis – the ride is getting rough."
        )

    # If the scripted finale killed the player's driver, wipe the contract now.
    if getattr(state, "demo_player_died", False):
        state.player_driver = None
        state.driver_pay = 0
        state.driver_contract_races = 0
        state.demo_player_died = False

    retired = []
    for d in dnf_drivers:
        retired.append((d, retire_reasons.get(d.get("name"), "unknown")))

    # ✅ Contract tick ONLY after the race is finished
    started_race = (
        (state.player_driver in dnf_drivers) or
        any(d == state.player_driver for d, _ in finishers)
    )

    tick_driver_contract_after_race_end(state, time, started_race)

    record_race_result(state, time, season_week, race_name, is_wet, is_hot, finishers, retired)

    # ✅ CRITICAL: stop the race repeating
    state.completed_races.add(season_week)

    # ✅ If you use pending_race_week, clear it so the week doesn't re-trigger
    if getattr(state, "pending_race_week", None) == season_week:
        state.pending_race_week = None
        state.completed_races.add(season_week)
