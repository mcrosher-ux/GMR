"""Tests for constants.py - Game constants and helper functions."""

import pytest
from gmr.constants import (
    MONTHS,
    POINTS_TABLE,
    CONSTRUCTOR_SHARE,
    WEEKS_PER_YEAR,
    get_reliability_mult,
    get_crash_mult,
    get_prize_for_race_and_pos,
    DEFAULT_PRIZE_TOP3
)
from gmr.core_time import GameTime


class TestConstants:
    """Test suite for basic constants."""
    
    def test_months_count(self):
        """Test that MONTHS has 12 entries."""
        assert len(MONTHS) == 12
    
    def test_months_names(self):
        """Test that month names are correct."""
        assert MONTHS[0] == "January"
        assert MONTHS[11] == "December"
    
    def test_points_table_length(self):
        """Test points table has 6 positions."""
        assert len(POINTS_TABLE) == 6
    
    def test_points_table_descending(self):
        """Test that points decrease for lower positions."""
        for i in range(len(POINTS_TABLE) - 1):
            assert POINTS_TABLE[i] > POINTS_TABLE[i + 1]
    
    def test_constructor_share_valid(self):
        """Test constructor share is a valid percentage."""
        assert 0 <= CONSTRUCTOR_SHARE <= 1
    
    def test_weeks_per_year_valid(self):
        """Test weeks per year is reasonable."""
        assert WEEKS_PER_YEAR == 48


class TestGetReliabilityMult:
    """Test suite for reliability multiplier function."""
    
    def test_reliability_mult_1950s_unreliable(self):
        """Test that 1950s has high unreliability."""
        time = GameTime(1950)
        mult = get_reliability_mult(time)
        
        assert mult >= 2.0
        assert isinstance(mult, (int, float))
    
    def test_reliability_mult_improves_over_time(self):
        """Test that reliability improves in later eras."""
        time_1950 = GameTime(1950)
        time_1980 = GameTime(1980)
        time_2000 = GameTime(2000)
        
        mult_1950 = get_reliability_mult(time_1950)
        mult_1980 = get_reliability_mult(time_1980)
        mult_2000 = get_reliability_mult(time_2000)
        
        # Later eras should be more reliable (lower multiplier)
        assert mult_1950 > mult_1980
        assert mult_1980 > mult_2000
    
    def test_reliability_mult_modern_era(self):
        """Test reliability in modern era."""
        time = GameTime(2020)
        mult = get_reliability_mult(time)
        
        # Modern era should be very reliable
        assert mult <= 1.0


class TestGetCrashMult:
    """Test suite for crash multiplier function."""
    
    def test_crash_mult_1950s_dangerous(self):
        """Test that 1950s has high crash danger."""
        time = GameTime(1950)
        mult = get_crash_mult(time)
        
        assert mult >= 1.0
        assert isinstance(mult, (int, float))
    
    def test_crash_mult_improves_over_time(self):
        """Test that crash rates improve with better safety."""
        time_1950 = GameTime(1950)
        time_1990 = GameTime(1990)
        time_2015 = GameTime(2015)
        
        mult_1950 = get_crash_mult(time_1950)
        mult_1990 = get_crash_mult(time_1990)
        mult_2015 = get_crash_mult(time_2015)
        
        # Later eras should be safer (lower multiplier)
        assert mult_1950 > mult_1990
        assert mult_1990 >= mult_2015


class TestGetPrizeForRaceAndPos:
    """Test suite for prize money calculation."""
    
    def test_get_prize_for_winner(self):
        """Test prize for race winner."""
        prize = get_prize_for_race_and_pos("Bradley Fields", 0)
        
        assert isinstance(prize, int)
        assert prize > 0
    
    def test_get_prize_for_second_place(self):
        """Test prize for second place."""
        prize_1st = get_prize_for_race_and_pos("Bradley Fields", 0)
        prize_2nd = get_prize_for_race_and_pos("Bradley Fields", 1)
        
        # Second place should get less than winner
        assert prize_2nd < prize_1st
        assert prize_2nd > 0
    
    def test_get_prize_for_third_place(self):
        """Test prize for third place."""
        prize_2nd = get_prize_for_race_and_pos("Bradley Fields", 1)
        prize_3rd = get_prize_for_race_and_pos("Bradley Fields", 2)
        
        # Third place should get less than second
        assert prize_3rd < prize_2nd
        assert prize_3rd >= 0
    
    def test_get_prize_for_low_position(self):
        """Test prize for positions outside top 3."""
        prize_4th = get_prize_for_race_and_pos("Bradley Fields", 3)
        
        # Should return 0 or finisher bonus
        assert prize_4th >= 0
    
    def test_get_prize_vallone_gp(self):
        """Test prize for prestigious Vallone GP."""
        prize_vallone = get_prize_for_race_and_pos("Vallone GP", 0)
        prize_small = get_prize_for_race_and_pos("Bradley Fields", 0)
        
        # Vallone should pay more than small races
        assert prize_vallone > prize_small
    
    def test_get_prize_ardennes_highest(self):
        """Test that Ardennes Endurance GP has highest prize."""
        prize_ardennes = get_prize_for_race_and_pos("Ardennes Endurance GP", 0)
        prize_vallone = get_prize_for_race_and_pos("Vallone GP", 0)
        prize_small = get_prize_for_race_and_pos("Bradley Fields", 0)
        
        # Ardennes should be the most prestigious
        assert prize_ardennes > prize_vallone
        assert prize_ardennes > prize_small
    
    def test_get_prize_unknown_race_uses_default(self):
        """Test that unknown races use default prize structure."""
        prize = get_prize_for_race_and_pos("Unknown GP", 0)
        
        # Should use default prize
        assert prize == DEFAULT_PRIZE_TOP3[0]
    
    def test_get_prize_finisher_bonus(self):
        """Test races with finisher bonus."""
        # Château-des-Prés has finisher bonus
        prize_4th = get_prize_for_race_and_pos("Château-des-Prés GP", 3)
        
        # Should get finisher bonus (50)
        assert prize_4th == 50
