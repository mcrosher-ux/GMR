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
