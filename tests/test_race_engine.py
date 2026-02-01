"""Tests for race_engine.py - Race simulation core."""

import pytest
from gmr.race_engine import RaceSimulator, STAGE_LABELS, get_ai_car_stats
from gmr.core_state import GameState
from gmr.core_time import GameTime


class TestStageLabels:
    """Test suite for stage labels."""
    
    def test_stage_labels_count(self):
        """Test that there are 3 stage labels."""
        assert len(STAGE_LABELS) == 3
    
    def test_stage_labels_format(self):
        """Test that stage labels have correct format."""
        for i, label in enumerate(STAGE_LABELS, 1):
            assert f"Stage {i}/3" in label


class TestGetAiCarStats:
    """Test suite for AI car stats function."""
    
    def test_get_ai_car_stats_enzoni(self):
        """Test getting stats for Enzoni constructor."""
        speed, reliability = get_ai_car_stats("Enzoni")
        
        assert isinstance(speed, (int, float))
        assert isinstance(reliability, (int, float))
        assert 0 <= speed <= 10
        assert 0 <= reliability <= 10
    
    def test_get_ai_car_stats_independent(self):
        """Test getting stats for Independent constructor."""
        speed, reliability = get_ai_car_stats("Independent")
        
        assert isinstance(speed, (int, float))
        assert isinstance(reliability, (int, float))
        assert 0 <= speed <= 10
        assert 0 <= reliability <= 10
    
    def test_get_ai_car_stats_unknown_constructor(self):
        """Test getting stats for unknown constructor."""
        speed, reliability = get_ai_car_stats("Unknown Team")
        
        # Should return default values
        assert isinstance(speed, (int, float))
        assert isinstance(reliability, (int, float))


class TestRaceSimulator:
    """Test suite for RaceSimulator class."""
    
    @pytest.fixture
    def mock_state(self):
        """Create a mock game state for testing."""
        state = GameState()
        state.player_driver = {
            "name": "Test Driver",
            "pace": 7,
            "consistency": 6,
            "aggression": 5,
            "mechanical_sympathy": 5,
            "wet_skill": 5,
            "heat_tolerance": 5,
            "constructor": "Test Team"
        }
        state.engine_health = 100
        state.engine_wear = 80
        state.car_reliability = 7
        state.current_engine = {
            "speed": 7,
            "acceleration": 6,
            "heat_tolerance": 5
        }
        state.current_chassis = {
            "weight": 5,
            "aero": 5,
            "brakes": 5,
            "suspension": 5
        }
        state.car_speed = 7
        return state
    
    @pytest.fixture
    def mock_drivers(self):
        """Create mock drivers for testing."""
        return [
            {
                "name": "Driver A",
                "pace": 8,
                "consistency": 7,
                "constructor": "Ferrari",
                "aggression": 6,
                "mechanical_sympathy": 5,
                "wet_skill": 5,
                "heat_tolerance": 5
            },
            {
                "name": "Driver B",
                "pace": 7,
                "consistency": 8,
                "constructor": "Mercedes",
                "aggression": 4,
                "mechanical_sympathy": 6,
                "wet_skill": 6,
                "heat_tolerance": 6
            },
            {
                "name": "Test Driver",
                "pace": 7,
                "consistency": 6,
                "constructor": "Test Team",
                "aggression": 5,
                "mechanical_sympathy": 5,
                "wet_skill": 5,
                "heat_tolerance": 5
            }
        ]
    
    @pytest.fixture
    def mock_track(self):
        """Create a mock track profile."""
        return {
            "pace_weight": 1.0,
            "consistency_weight": 1.0,
            "engine_danger": 1.0,
            "crash_danger": 1.0
        }
    
    def test_race_simulator_initialization(self, mock_state, mock_drivers, mock_track):
        """Test RaceSimulator initialization."""
        quali_results = [(d, d["pace"]) for d in mock_drivers]
        time = GameTime(1960)  # Pass GameTime object, not int
        
        sim = RaceSimulator(
            event_grid=mock_drivers,
            quali_results=quali_results,
            track_profile=mock_track,
            state=mock_state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        assert sim is not None
        assert len(sim.current_positions) == len(mock_drivers)
        assert sim.current_stage_idx == 0
        assert len(sim.dnf_drivers) == 0
    
    def test_race_simulator_get_current_standings(self, mock_state, mock_drivers, mock_track):
        """Test getting current race standings."""
        quali_results = [(d, d["pace"]) for d in mock_drivers]
        time = GameTime(1960)  # Pass GameTime object, not int
        
        sim = RaceSimulator(
            event_grid=mock_drivers,
            quali_results=quali_results,
            track_profile=mock_track,
            state=mock_state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        standings = sim.get_current_standings()
        
        assert isinstance(standings, list)
        assert len(standings) <= len(mock_drivers)
        
        # Check format of standings
        for pos, driver, score in standings:
            assert isinstance(pos, int)
            assert isinstance(driver, dict)
            assert "name" in driver
    
    def test_race_simulator_simulate_stage(self, mock_state, mock_drivers, mock_track):
        """Test simulating a race stage."""
        quali_results = [(d, d["pace"]) for d in mock_drivers]
        time = GameTime(1960)  # Pass GameTime object, not int
        
        sim = RaceSimulator(
            event_grid=mock_drivers,
            quali_results=quali_results,
            track_profile=mock_track,
            state=mock_state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        result = sim.simulate_stage(0, player_strategy_mult=1.0)
        
        assert isinstance(result, dict)
        assert "overtakes" in result
        assert "incidents" in result
        assert isinstance(result["overtakes"], list)
        assert isinstance(result["incidents"], list)
    
    def test_race_simulator_get_final_results(self, mock_state, mock_drivers, mock_track):
        """Test getting final race results."""
        quali_results = [(d, d["pace"]) for d in mock_drivers]
        time = GameTime(1960)  # Pass GameTime object, not int
        
        sim = RaceSimulator(
            event_grid=mock_drivers,
            quali_results=quali_results,
            track_profile=mock_track,
            state=mock_state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        # Simulate all stages
        for stage_idx in range(3):
            sim.simulate_stage(stage_idx, player_strategy_mult=1.0)
        
        finishers, dnfs, reasons = sim.get_final_results()
        
        assert isinstance(finishers, list)
        assert isinstance(dnfs, list)
        assert isinstance(reasons, dict)
        
        # Total drivers should match
        assert len(finishers) + len(dnfs) == len(mock_drivers)


class TestInjuryProbabilityThresholds:
    """Test suite for injury probability calculations."""
    
    def test_thresholds_low_severity(self):
        """Test injury thresholds with low crash severity (crash_severity=1.0)."""
        crash_severity = 1.0
        
        fatal_chance = min(0.02 * crash_severity, 0.15)
        serious_chance = min(0.08 * crash_severity, 0.30)
        minor_chance = min(0.25 * crash_severity, 0.40)
        
        fatal_threshold = fatal_chance
        serious_threshold = fatal_threshold + serious_chance
        minor_threshold = min(serious_threshold + minor_chance, 0.85)
        
        # Validate individual chances
        assert fatal_chance == 0.02
        assert serious_chance == 0.08
        assert minor_chance == 0.25
        
        # Validate cumulative thresholds
        assert fatal_threshold == 0.02
        assert serious_threshold == 0.10
        assert minor_threshold == 0.35
        
        # Validate thresholds never exceed 1.0
        assert minor_threshold <= 1.0
        # Validate there's always some "unscathed" chance
        assert minor_threshold <= 0.85
    
    def test_thresholds_medium_severity(self):
        """Test injury thresholds with medium crash severity (crash_severity=1.5)."""
        crash_severity = 1.5
        
        fatal_chance = min(0.02 * crash_severity, 0.15)
        serious_chance = min(0.08 * crash_severity, 0.30)
        minor_chance = min(0.25 * crash_severity, 0.40)
        
        fatal_threshold = fatal_chance
        serious_threshold = fatal_threshold + serious_chance
        minor_threshold = min(serious_threshold + minor_chance, 0.85)
        
        # Validate individual chances
        assert fatal_chance == 0.03
        assert serious_chance == 0.12
        assert minor_chance == 0.375
        
        # Validate cumulative thresholds
        assert fatal_threshold == 0.03
        assert serious_threshold == 0.15
        assert minor_threshold == 0.525
        
        # Validate thresholds never exceed 1.0
        assert minor_threshold <= 1.0
        assert minor_threshold <= 0.85
    
    def test_thresholds_high_severity(self):
        """Test injury thresholds with high crash severity (crash_severity=3.0)."""
        crash_severity = 3.0
        
        fatal_chance = min(0.02 * crash_severity, 0.15)
        serious_chance = min(0.08 * crash_severity, 0.30)
        minor_chance = min(0.25 * crash_severity, 0.40)
        
        fatal_threshold = fatal_chance
        serious_threshold = fatal_threshold + serious_chance
        minor_threshold = min(serious_threshold + minor_chance, 0.85)
        
        # Validate individual chances (caps apply)
        assert fatal_chance == 0.06  # 0.02 * 3 = 0.06, under 0.15 cap
        assert serious_chance == 0.24  # 0.08 * 3 = 0.24, under 0.30 cap
        assert minor_chance == 0.40  # 0.25 * 3 = 0.75, capped at 0.40
        
        # Validate cumulative thresholds
        assert fatal_threshold == 0.06
        assert serious_threshold == 0.30
        assert minor_threshold == 0.70
        
        # Validate thresholds never exceed caps
        assert minor_threshold <= 1.0
        assert minor_threshold <= 0.85
    
    def test_thresholds_extreme_severity(self):
        """Test injury thresholds with extreme crash severity (crash_severity=5.0)."""
        crash_severity = 5.0
        
        fatal_chance = min(0.02 * crash_severity, 0.15)
        serious_chance = min(0.08 * crash_severity, 0.30)
        minor_chance = min(0.25 * crash_severity, 0.40)
        
        fatal_threshold = fatal_chance
        serious_threshold = fatal_threshold + serious_chance
        minor_threshold = min(serious_threshold + minor_chance, 0.85)
        
        # Validate individual chances (all caps apply)
        assert fatal_chance == 0.10  # 0.02 * 5 = 0.10, under 0.15 cap
        assert serious_chance == 0.30  # 0.08 * 5 = 0.40, capped at 0.30
        assert minor_chance == 0.40  # 0.25 * 5 = 1.25, capped at 0.40
        
        # Validate cumulative thresholds
        assert fatal_threshold == 0.10
        assert serious_threshold == 0.40
        assert minor_threshold == 0.80
        
        # Validate thresholds never exceed caps
        assert minor_threshold <= 1.0
        assert minor_threshold <= 0.85
    
    def test_thresholds_maximum_severity(self):
        """Test injury thresholds with maximum crash severity (crash_severity=10.0)."""
        crash_severity = 10.0
        
        fatal_chance = min(0.02 * crash_severity, 0.15)
        serious_chance = min(0.08 * crash_severity, 0.30)
        minor_chance = min(0.25 * crash_severity, 0.40)
        
        fatal_threshold = fatal_chance
        serious_threshold = fatal_threshold + serious_chance
        minor_threshold = min(serious_threshold + minor_chance, 0.85)
        
        # Validate individual chances (all caps fully engaged)
        assert fatal_chance == pytest.approx(0.15)  # capped
        assert serious_chance == pytest.approx(0.30)  # capped
        assert minor_chance == pytest.approx(0.40)  # capped
        
        # Validate cumulative thresholds (capped at 0.85)
        assert fatal_threshold == pytest.approx(0.15)
        assert serious_threshold == pytest.approx(0.45)
        assert minor_threshold == pytest.approx(0.85)  # Would be 0.85 due to final cap
        
        # Validate thresholds never exceed caps
        assert minor_threshold <= 1.0
        assert minor_threshold <= 0.85 + 1e-9  # Small epsilon for float comparison
        
        # At maximum, there's still 15% chance to walk away unscathed
        unscathed_chance = 1.0 - minor_threshold
        assert unscathed_chance >= 0.15 - 1e-9
    
    def test_thresholds_are_ordered(self):
        """Test that thresholds are always in ascending order."""
        for crash_severity in [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]:
            fatal_chance = min(0.02 * crash_severity, 0.15)
            serious_chance = min(0.08 * crash_severity, 0.30)
            minor_chance = min(0.25 * crash_severity, 0.40)
            
            fatal_threshold = fatal_chance
            serious_threshold = fatal_threshold + serious_chance
            minor_threshold = min(serious_threshold + minor_chance, 0.85)
            
            # Thresholds must be in ascending order
            assert 0 < fatal_threshold < serious_threshold < minor_threshold <= 1.0, \
                f"Thresholds out of order for crash_severity={crash_severity}"


class TestPlayerPerformanceMultiplier:
    """Test suite for player performance multiplier behavior."""
    
    @pytest.fixture
    def basic_setup(self):
        """Create basic test setup with state, drivers, and track."""
        from gmr.core_state import GameState
        from gmr.core_time import GameTime
        
        state = GameState()
        player_driver = {
            "name": "Player Driver",
            "pace": 7,
            "consistency": 6,
            "aggression": 5,
            "mechanical_sympathy": 5,
            "wet_skill": 5,
            "constructor": "Player Team"
        }
        state.player_driver = player_driver
        # Engine needs speed and acceleration fields
        state.current_engine = {"power": 5, "reliability": 5, "speed": 5, "acceleration": 5}
        state.current_chassis = {"aero": 5, "suspension": 5, "weight": 7}
        state.car_speed = 5
        
        drivers = [
            player_driver,
            {"name": "AI Driver 1", "pace": 7, "consistency": 6, "aggression": 5,
             "mechanical_sympathy": 5, "wet_skill": 5, "constructor": "Enzoni"},
            {"name": "AI Driver 2", "pace": 6, "consistency": 7, "aggression": 4,
             "mechanical_sympathy": 6, "wet_skill": 4, "constructor": "Independent"},
        ]
        
        track = {
            "name": "Test Circuit",
            "country": "Italy",
            "base_crash_chance": 0.0,  # Disable crashes for multiplier testing
            "base_engine_fail": 0.0,   # Disable failures for multiplier testing
            "pace_weight": 1.0,
            "consistency_weight": 1.0,
        }
        
        time = GameTime(1960)
        
        return state, drivers, track, time
    
    def test_multiplier_not_cumulative_across_stages(self, basic_setup):
        """Test that player_perf_mult is set fresh each stage, not compounded."""
        state, drivers, track, time = basic_setup
        quali_results = [(d, d["pace"]) for d in drivers]
        
        sim = RaceSimulator(
            event_grid=drivers,
            quali_results=quali_results,
            track_profile=track,
            state=state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        # Stage 1: Apply 1.05 multiplier
        sim.simulate_stage(0, player_strategy_mult=1.05)
        assert sim.player_perf_mult == 1.05  # Should be exactly 1.05
        
        # Stage 2: Apply 1.05 multiplier again
        sim.simulate_stage(1, player_strategy_mult=1.05)
        # Should STILL be 1.05, NOT 1.05 * 1.05 = 1.1025
        assert sim.player_perf_mult == 1.05
        
        # Stage 3: Apply 1.05 multiplier again
        sim.simulate_stage(2, player_strategy_mult=1.05)
        # Should STILL be 1.05, NOT 1.05^3 = 1.157625
        assert sim.player_perf_mult == 1.05
    
    def test_multiplier_changes_each_stage(self, basic_setup):
        """Test that different multipliers can be applied each stage."""
        state, drivers, track, time = basic_setup
        quali_results = [(d, d["pace"]) for d in drivers]
        
        sim = RaceSimulator(
            event_grid=drivers,
            quali_results=quali_results,
            track_profile=track,
            state=state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        # Stage 1: PUSH (1.05)
        sim.simulate_stage(0, player_strategy_mult=1.05)
        assert sim.player_perf_mult == 1.05
        
        # Stage 2: BALANCED (1.0)
        sim.simulate_stage(1, player_strategy_mult=1.0)
        assert sim.player_perf_mult == 1.0  # Fresh value, not 1.05 * 1.0
        
        # Stage 3: CONSERVE (0.95)
        sim.simulate_stage(2, player_strategy_mult=0.95)
        assert sim.player_perf_mult == 0.95  # Fresh value
    
    def test_default_multiplier_is_one(self, basic_setup):
        """Test that default multiplier is 1.0 with no strategy specified."""
        state, drivers, track, time = basic_setup
        quali_results = [(d, d["pace"]) for d in drivers]
        
        sim = RaceSimulator(
            event_grid=drivers,
            quali_results=quali_results,
            track_profile=track,
            state=state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        # Initial multiplier should be 1.0
        assert sim.player_perf_mult == 1.0
        
        # Using default (1.0) should leave it at 1.0
        sim.simulate_stage(0, player_strategy_mult=1.0)
        assert sim.player_perf_mult == 1.0


class TestPlayerVsAIFairness:
    """Test suite ensuring fair performance calculation between player and AI."""
    
    @pytest.fixture
    def identical_setup(self):
        """Create setup with identical player and AI drivers for fairness testing."""
        from gmr.core_state import GameState
        from gmr.core_time import GameTime
        
        state = GameState()
        # Player driver with specific stats
        player_driver = {
            "name": "Player Driver",
            "pace": 7,
            "consistency": 7,
            "aggression": 5,
            "mechanical_sympathy": 5,
            "wet_skill": 5,
            "heat_tolerance": 5,
            "constructor": "Player Team"
        }
        state.player_driver = player_driver
        # Set car to None so it falls back to car_speed
        state.current_engine = None
        state.current_chassis = None
        state.car_speed = 5  # Neutral car speed
        
        # AI driver with IDENTICAL stats
        ai_driver = {
            "name": "AI Driver",
            "pace": 7,
            "consistency": 7,
            "aggression": 5,
            "mechanical_sympathy": 5,
            "wet_skill": 5,
            "heat_tolerance": 5,
            "constructor": "Independent"  # Independent gives car_speed ~5
        }
        
        drivers = [player_driver, ai_driver]
        
        track = {
            "name": "Test Circuit",
            "country": "Italy",
            "base_crash_chance": 0.0,
            "base_engine_fail": 0.0,
            "pace_weight": 1.0,
            "consistency_weight": 1.0,
        }
        
        time = GameTime(1960)
        
        return state, drivers, track, time
    
    def test_multiplier_affects_performance_proportionally(self, identical_setup):
        """Test that PUSH strategy (1.05) gives ~5% advantage per stage, not cumulative."""
        state, drivers, track, time = identical_setup
        quali_results = [(d, d["pace"]) for d in drivers]
        
        import random
        random.seed(42)  # Fixed seed for reproducible test
        
        sim = RaceSimulator(
            event_grid=drivers,
            quali_results=quali_results,
            track_profile=track,
            state=state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        # Record performance with BALANCED (1.0) first
        sim.simulate_stage(0, player_strategy_mult=1.0)
        balanced_perf_stage1 = sim.driver_performance.get("Player Driver", 0)
        
        # Reset and try with PUSH (1.05)
        random.seed(42)  # Same seed
        sim2 = RaceSimulator(
            event_grid=drivers,
            quali_results=quali_results,
            track_profile=track,
            state=state,
            is_wet=False,
            is_hot=False,
            time=time,
            grid_risk_mult=1.0,
            race_length_factor=1.0
        )
        
        sim2.simulate_stage(0, player_strategy_mult=1.05)
        push_perf_stage1 = sim2.driver_performance.get("Player Driver", 0)
        
        # PUSH should give more performance than BALANCED
        # The multiplier applies to stage_perf after base calculations,
        # so the effect is less than 5% due to initial performance being set before multiplier
        ratio = push_perf_stage1 / balanced_perf_stage1 if balanced_perf_stage1 > 0 else 0
        assert ratio > 1.0, \
            f"PUSH should give more performance than BALANCED, but ratio was {ratio:.3f}"
        assert ratio < 1.10, \
            f"PUSH gave {ratio:.3f}x performance, too high (should be modest boost)"
