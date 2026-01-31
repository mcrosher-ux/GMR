"""Tests for world_logic.py - Driver generation and car calculations."""

import pytest
from gmr.world_logic import (
    generate_random_driver_name,
    calculate_car_speed,
    get_car_speed_for_track,
    initialise_driver_age_profiles,
    DRIVER_FIRST_NAMES,
    DRIVER_LAST_NAMES
)
from gmr.core_state import GameState
from gmr.data import drivers


class TestDriverNameGeneration:
    """Test suite for driver name generation."""
    
    def test_generate_random_driver_name_format(self):
        """Test that generated names have correct format."""
        name = generate_random_driver_name()
        
        # Should be "FirstName LastName"
        parts = name.split()
        assert len(parts) == 2
        
        first_name, last_name = parts
        assert first_name in DRIVER_FIRST_NAMES
        assert last_name in DRIVER_LAST_NAMES
    
    def test_generate_random_driver_name_uniqueness(self):
        """Test that multiple calls can generate different names."""
        names = set()
        for _ in range(50):
            names.add(generate_random_driver_name())
        
        # Should generate some variety (not all the same)
        assert len(names) > 1


class TestCarSpeedCalculation:
    """Test suite for car speed calculations."""
    
    def test_calculate_car_speed_with_valid_components(self):
        """Test car speed calculation with valid engine and chassis."""
        engine = {
            "speed": 7,
            "acceleration": 6
        }
        chassis = {
            "weight": 5,
            "aero": 6
        }
        
        speed = calculate_car_speed(engine, chassis)
        
        # Should return a numeric value
        assert isinstance(speed, (int, float))
        assert speed > 0
        assert speed <= 10  # Should be on 1-10 scale
    
    def test_calculate_car_speed_with_none_engine(self):
        """Test car speed calculation when engine is None."""
        chassis = {
            "weight": 5,
            "aero": 6
        }
        
        speed = calculate_car_speed(None, chassis)
        assert speed == 0
    
    def test_calculate_car_speed_with_none_chassis(self):
        """Test car speed calculation when chassis is None."""
        engine = {
            "speed": 7,
            "acceleration": 6
        }
        
        speed = calculate_car_speed(engine, None)
        assert speed == 0
    
    def test_calculate_car_speed_both_none(self):
        """Test car speed calculation when both are None."""
        speed = calculate_car_speed(None, None)
        assert speed == 0
    
    def test_calculate_car_speed_formula_consistency(self):
        """Test that the formula produces consistent results."""
        engine = {
            "speed": 8,
            "acceleration": 7
        }
        chassis = {
            "weight": 4,
            "aero": 7
        }
        
        # Calculate multiple times - should be deterministic
        speed1 = calculate_car_speed(engine, chassis)
        speed2 = calculate_car_speed(engine, chassis)
        
        assert speed1 == speed2
    
    def test_calculate_car_speed_higher_stats_better(self):
        """Test that higher stats result in higher speed."""
        engine_low = {"speed": 3, "acceleration": 3}
        engine_high = {"speed": 9, "acceleration": 9}
        chassis = {"weight": 5, "aero": 5}
        
        speed_low = calculate_car_speed(engine_low, chassis)
        speed_high = calculate_car_speed(engine_high, chassis)
        
        assert speed_high > speed_low
    
    def test_calculate_car_speed_weight_inverse(self):
        """Test that lower weight (lighter car) is better."""
        engine = {"speed": 7, "acceleration": 6}
        chassis_heavy = {"weight": 9, "aero": 5}
        chassis_light = {"weight": 3, "aero": 5}
        
        speed_heavy = calculate_car_speed(engine, chassis_heavy)
        speed_light = calculate_car_speed(engine, chassis_light)
        
        # Lighter should be faster
        assert speed_light > speed_heavy


class TestGetCarSpeedForTrack:
    """Test suite for track-specific car speed calculations."""
    
    def test_get_car_speed_for_track_with_valid_state(self):
        """Test track-specific speed calculation."""
        state = GameState()
        state.current_engine = {"speed": 7, "acceleration": 6}
        state.current_chassis = {"weight": 5, "aero": 6}
        state.car_speed = 7.0
        
        track_profile = {
            "name": "Test Track",
            "pace_weight": 1.0,
            "consistency_weight": 1.0
        }
        
        speed = get_car_speed_for_track(state, track_profile)
        
        # Should return a numeric value
        assert isinstance(speed, (int, float))
        assert speed >= 0
    
    def test_get_car_speed_for_track_fallback_without_components(self):
        """Test fallback when engine or chassis missing."""
        state = GameState()
        state.current_engine = None
        state.current_chassis = None
        state.car_speed = 5.0
        
        track_profile = {
            "name": "Test Track",
            "pace_weight": 1.0
        }
        
        speed = get_car_speed_for_track(state, track_profile)
        
        # Should fall back to car_speed
        assert speed == 5.0


class TestDriverAgeProfiles:
    """Test suite for driver age profile initialization."""
    
    def test_initialise_driver_age_profiles(self):
        """Test that driver age profiles are initialized."""
        # This modifies the global drivers list
        initialise_driver_age_profiles()
        
        # Check that each driver has the new fields
        for driver in drivers:
            assert "age" in driver
            assert "peak_age" in driver
            assert "decline_age" in driver
            
            # Peak age should be reasonable
            assert driver["peak_age"] >= 25
            assert driver["peak_age"] <= 45
            
            # Decline should be after peak
            assert driver["decline_age"] > driver["peak_age"]
            
            # Age relationships should make sense
            age = driver["age"]
            peak = driver["peak_age"]
            decline = driver["decline_age"]
            
            assert decline > peak
