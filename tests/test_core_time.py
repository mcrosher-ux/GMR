"""Tests for core_time.py - GameTime and time management."""

import pytest
from gmr.core_time import GameTime, get_season_week
from gmr.constants import WEEKS_PER_YEAR


class TestGameTime:
    """Test suite for GameTime class."""
    
    def test_game_time_initialization_default(self):
        """Test GameTime initializes with default year."""
        time = GameTime()
        
        assert time.year == 1947
        assert time.month == 0
        assert time.week == 1
        assert time.absolute_week == 1
    
    def test_game_time_initialization_custom_year(self):
        """Test GameTime initializes with custom year."""
        time = GameTime(1960)
        
        assert time.year == 1960
        assert time.month == 0
        assert time.week == 1
        assert time.absolute_week == 1
    
    def test_advance_week_basic(self):
        """Test advancing by one week."""
        time = GameTime()
        initial_week = time.week
        initial_absolute = time.absolute_week
        
        time.advance_week()
        
        assert time.week == initial_week + 1
        assert time.absolute_week == initial_absolute + 1
        assert time.month == 0
        assert time.year == 1947
    
    def test_advance_week_month_rollover(self):
        """Test advancing from week 4 to week 1 of next month."""
        time = GameTime()
        time.week = 4
        
        time.advance_week()
        
        assert time.week == 1
        assert time.month == 1
        assert time.year == 1947
    
    def test_advance_week_year_rollover(self):
        """Test advancing from December to January."""
        time = GameTime()
        time.month = 11  # December (0-indexed)
        time.week = 4
        
        time.advance_week()
        
        assert time.week == 1
        assert time.month == 0  # January
        assert time.year == 1948
    
    def test_advance_multiple_weeks(self):
        """Test advancing multiple weeks."""
        time = GameTime()
        
        # Advance 10 weeks
        for _ in range(10):
            time.advance_week()
        
        assert time.absolute_week == 11
        # 10 weeks = 2 full months + 2 weeks
        assert time.month == 2
        assert time.week == 3
    
    def test_absolute_week_increases_continuously(self):
        """Test that absolute_week increases continuously without reset."""
        time = GameTime()
        
        # Advance through multiple years
        for _ in range(100):
            time.advance_week()
        
        assert time.absolute_week == 101


class TestGetSeasonWeek:
    """Test suite for get_season_week function."""
    
    def test_get_season_week_first_week(self):
        """Test season week for first week."""
        time = GameTime()
        assert get_season_week(time) == 1
    
    def test_get_season_week_mid_season(self):
        """Test season week in middle of first season."""
        time = GameTime()
        time.absolute_week = 20
        
        week = get_season_week(time)
        assert week == 20
    
    def test_get_season_week_wraps_per_year(self):
        """Test that season week wraps after WEEKS_PER_YEAR."""
        time = GameTime()
        time.absolute_week = WEEKS_PER_YEAR + 1
        
        week = get_season_week(time)
        assert week == 1
    
    def test_get_season_week_second_year(self):
        """Test season week in second year."""
        time = GameTime()
        time.absolute_week = WEEKS_PER_YEAR + 10
        
        week = get_season_week(time)
        assert week == 10
    
    def test_get_season_week_last_week_of_season(self):
        """Test last week of season."""
        time = GameTime()
        time.absolute_week = WEEKS_PER_YEAR
        
        week = get_season_week(time)
        assert week == WEEKS_PER_YEAR
