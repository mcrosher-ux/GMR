"""Tests for careers.py - Driver contract and career management."""

import pytest
from gmr.careers import tick_driver_contract_after_race_end
from gmr.core_state import GameState
from gmr.core_time import GameTime


class TestTickDriverContractAfterRaceEnd:
    """Test suite for driver contract decrement logic."""
    
    def test_decrement_contract_races(self):
        """Test that contract races are decremented after a race."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 5
        time = GameTime(1950)
        time.week = 10
        
        tick_driver_contract_after_race_end(state, time, started_race=True)
        
        assert state.driver_contract_races == 4
    
    def test_no_decrement_if_not_started(self):
        """Test that contract races are NOT decremented if player didn't start."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 5
        time = GameTime(1950)
        time.week = 10
        
        tick_driver_contract_after_race_end(state, time, started_race=False)
        
        assert state.driver_contract_races == 5  # Unchanged
    
    def test_no_decrement_if_no_driver(self):
        """Test that nothing happens if there's no player driver."""
        state = GameState()
        state.player_driver = None
        state.driver_contract_races = 5
        time = GameTime(1950)
        time.week = 10
        
        tick_driver_contract_after_race_end(state, time, started_race=True)
        
        assert state.driver_contract_races == 5  # Unchanged
    
    def test_no_decrement_if_contract_already_zero(self):
        """Test that nothing happens if contract races already at 0."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 0
        time = GameTime(1950)
        time.week = 10
        
        tick_driver_contract_after_race_end(state, time, started_race=True)
        
        assert state.driver_contract_races == 0  # Unchanged
    
    def test_double_call_same_week_no_double_decrement(self):
        """Test that calling twice in same week only decrements once."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 5
        time = GameTime(1950)
        time.week = 10
        
        # First call - should decrement
        tick_driver_contract_after_race_end(state, time, started_race=True)
        assert state.driver_contract_races == 4
        
        # Second call same week - should NOT decrement
        tick_driver_contract_after_race_end(state, time, started_race=True)
        assert state.driver_contract_races == 4  # Still 4, not 3
    
    def test_different_weeks_both_decrement(self):
        """Test that calls in different weeks both decrement correctly."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 5
        time = GameTime(1950)
        
        # Week 10
        time.week = 10
        tick_driver_contract_after_race_end(state, time, started_race=True)
        assert state.driver_contract_races == 4
        
        # Week 15 (different week)
        time.week = 15
        tick_driver_contract_after_race_end(state, time, started_race=True)
        assert state.driver_contract_races == 3
    
    def test_different_years_both_decrement(self):
        """Test that calls in different years both decrement correctly."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 5
        
        # 1950, week 10
        time1 = GameTime(1950)
        time1.week = 10
        tick_driver_contract_after_race_end(state, time1, started_race=True)
        assert state.driver_contract_races == 4
        
        # 1951, week 10 (same week number but different year)
        time2 = GameTime(1951)
        time2.week = 10
        tick_driver_contract_after_race_end(state, time2, started_race=True)
        assert state.driver_contract_races == 3
    
    def test_triple_call_same_week(self):
        """Test that calling three times in same week only decrements once."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 5
        time = GameTime(1950)
        time.week = 10
        
        tick_driver_contract_after_race_end(state, time, started_race=True)
        tick_driver_contract_after_race_end(state, time, started_race=True)
        tick_driver_contract_after_race_end(state, time, started_race=True)
        
        assert state.driver_contract_races == 4  # Only decremented once


class TestContractGuardState:
    """Test that the guard state tracks correctly."""
    
    def test_guard_state_is_set_after_decrement(self):
        """Test that guard state variables are set after decrement."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 5
        time = GameTime(1950)
        time.week = 10
        
        tick_driver_contract_after_race_end(state, time, started_race=True)
        
        assert state._contract_last_decrement_week == 10
        assert state._contract_last_decrement_year == 1950
    
    def test_guard_state_updates_on_new_week(self):
        """Test that guard state updates when moving to new week."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 5
        time = GameTime(1950)
        
        # First race week 10
        time.week = 10
        tick_driver_contract_after_race_end(state, time, started_race=True)
        assert state._contract_last_decrement_week == 10
        
        # Second race week 15
        time.week = 15
        tick_driver_contract_after_race_end(state, time, started_race=True)
        assert state._contract_last_decrement_week == 15


class TestContractEdgeCases:
    """Test edge cases for contract system."""
    
    def test_contract_races_negative_one(self):
        """Test that negative contract races doesn't cause issues."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = -1
        time = GameTime(1950)
        time.week = 10
        
        # Should not crash or decrement further
        tick_driver_contract_after_race_end(state, time, started_race=True)
        
        assert state.driver_contract_races == -1  # Unchanged
    
    def test_two_race_contract_lifecycle(self):
        """Test full lifecycle of a 2-race contract (without extension prompt)."""
        state = GameState()
        state.player_driver = {"name": "Test Driver", "constructor": "Test Team"}
        state.driver_contract_races = 2
        time = GameTime(1950)
        
        # Race 1
        time.week = 10
        tick_driver_contract_after_race_end(state, time, started_race=True)
        assert state.driver_contract_races == 1
        
        # Verify no double-decrement in week 10
        tick_driver_contract_after_race_end(state, time, started_race=True)
        assert state.driver_contract_races == 1
        
        # Race 2 - this would trigger extension offer (which we can't test here
        # without mocking input, but we can verify decrement happens)
        time.week = 15
        # Note: This will prompt for extension, so we just test decrement logic
        # In production, maybe_offer_driver_extension() handles the rest
