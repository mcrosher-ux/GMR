"""Tests for calendar.py - Calendar generation and race scheduling."""

import pytest
from gmr.calendar import (
    generate_calendar_for_year,
    get_race_tier,
    BIG_RACES,
    MEDIUM_RACES,
    SMALL_RACES
)


class TestGetRaceTier:
    """Test suite for get_race_tier function."""
    
    def test_get_race_tier_big_races(self):
        """Test that big races are identified correctly."""
        for race in BIG_RACES:
            assert get_race_tier(race) == "big"
    
    def test_get_race_tier_medium_races(self):
        """Test that medium races are identified correctly."""
        for race in MEDIUM_RACES:
            assert get_race_tier(race) == "medium"
    
    def test_get_race_tier_small_races(self):
        """Test that small races are identified correctly."""
        for race in SMALL_RACES:
            assert get_race_tier(race) == "small"
    
    def test_get_race_tier_unknown_race(self):
        """Test that unknown races default to small tier."""
        assert get_race_tier("Unknown GP") == "small"


class TestGenerateCalendarForYear:
    """Test suite for calendar generation."""
    
    def test_generate_calendar_for_1947(self):
        """Test calendar generation for inaugural 1947 season."""
        calendar = generate_calendar_for_year(1947)
        
        # Should return a dictionary
        assert isinstance(calendar, dict)
        
        # Should have some races
        assert len(calendar) > 0
        
        # All keys should be week numbers
        for week in calendar.keys():
            assert isinstance(week, int)
            assert 1 <= week <= 48
        
        # All values should be race names (strings)
        for race_name in calendar.values():
            assert isinstance(race_name, str)
    
    def test_generate_calendar_anchored_races(self):
        """Test that anchored races appear in correct weeks."""
        calendar = generate_calendar_for_year(1947)
        
        # Vallone GP should be at week 20 (sponsor trigger)
        assert calendar.get(20) == "Vallone GP"
        
        # Ardennes should be at week 40 (finale)
        assert calendar.get(40) == "Ardennes Endurance GP"
    
    def test_generate_calendar_1948_adds_americas(self):
        """Test that 1948+ includes Americas races."""
        calendar_1947 = generate_calendar_for_year(1947)
        calendar_1948 = generate_calendar_for_year(1948)
        
        # Check for Buenos Aires in 1948
        has_buenos_aires = "Autódromo General San Martín" in calendar_1948.values()
        assert has_buenos_aires
    
    def test_generate_calendar_1950_adds_union_speedway(self):
        """Test that Union Speedway appears from 1950."""
        calendar_1949 = generate_calendar_for_year(1949)
        calendar_1950 = generate_calendar_for_year(1950)
        
        # Should not be in 1949
        assert "Union Speedway" not in calendar_1949.values()
        
        # Should be in 1950
        assert "Union Speedway" in calendar_1950.values()
    
    def test_generate_calendar_deterministic_per_year(self):
        """Test that calendar generation is deterministic for same year."""
        calendar1 = generate_calendar_for_year(1955)
        calendar2 = generate_calendar_for_year(1955)
        
        # Should generate identical calendars
        assert calendar1 == calendar2
    
    def test_generate_calendar_different_years_vary(self):
        """Test that different years produce different calendars."""
        calendar1 = generate_calendar_for_year(1955)
        calendar2 = generate_calendar_for_year(1956)
        
        # Should not be identical (at least some differences)
        # Only compare non-anchored races
        non_anchor_1 = {k: v for k, v in calendar1.items() if k not in [20, 25, 40]}
        non_anchor_2 = {k: v for k, v in calendar2.items() if k not in [20, 25, 40]}
        
        # There should be some variation
        assert non_anchor_1 != non_anchor_2 or len(calendar1) != len(calendar2)
    
    def test_generate_calendar_races_in_season(self):
        """Test that races are scheduled within racing season (Mar-Oct)."""
        calendar = generate_calendar_for_year(1955)
        
        for week in calendar.keys():
            # Racing season is weeks 9-40 (March to October)
            assert 9 <= week <= 40
    
    def test_generate_calendar_no_empty_race_names(self):
        """Test that all races have names."""
        calendar = generate_calendar_for_year(1950)
        
        for race_name in calendar.values():
            assert race_name
            assert len(race_name) > 0
    
    def test_generate_calendar_vallone_appears_twice(self):
        """Test that Vallone GP can appear twice in season."""
        calendar = generate_calendar_for_year(1950)
        
        # Count Vallone GP appearances
        vallone_count = sum(1 for race in calendar.values() if race == "Vallone GP")
        
        # Should appear at least once (at week 20), possibly twice
        assert vallone_count >= 1
        assert vallone_count <= 2
