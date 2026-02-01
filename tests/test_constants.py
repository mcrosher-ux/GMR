"""Tests for constants.py - Game constants and helper functions."""

from gmr.constants import (
    MONTHS,
    POINTS_TABLE,
    CONSTRUCTOR_SHARE,
    WEEKS_PER_YEAR,
    get_reliability_mult,
    get_crash_mult,
    get_prize_for_race_and_pos,
    DEFAULT_PRIZE_TOP3,
    CHASSIS_AERO_MIN,
    CHASSIS_AERO_MAX,
    CHASSIS_SUSPENSION_MIN,
    CHASSIS_SUSPENSION_MAX,
    CHASSIS_WEIGHT_MIN,
    CHASSIS_WEIGHT_MAX,
    clamp_chassis_aero,
    clamp_chassis_suspension,
    clamp_chassis_weight,
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


class TestChassisStatLimits:
    """Test suite for chassis stat limit constants."""
    
    def test_aero_limits_valid(self):
        """Test aero limits are in valid range."""
        assert CHASSIS_AERO_MIN == 1
        assert CHASSIS_AERO_MAX == 12
        assert CHASSIS_AERO_MIN < CHASSIS_AERO_MAX
    
    def test_suspension_limits_valid(self):
        """Test suspension limits are in valid range."""
        assert CHASSIS_SUSPENSION_MIN == 1
        assert CHASSIS_SUSPENSION_MAX == 10
        assert CHASSIS_SUSPENSION_MIN < CHASSIS_SUSPENSION_MAX
    
    def test_weight_limits_valid(self):
        """Test weight limits are in valid range."""
        assert CHASSIS_WEIGHT_MIN == 3
        assert CHASSIS_WEIGHT_MAX == 10
        assert CHASSIS_WEIGHT_MIN < CHASSIS_WEIGHT_MAX


class TestClampChassisAero:
    """Test suite for clamp_chassis_aero function."""
    
    def test_clamp_aero_within_range(self):
        """Test aero values within range are unchanged."""
        assert clamp_chassis_aero(5) == 5
        assert clamp_chassis_aero(1) == 1
        assert clamp_chassis_aero(12) == 12
    
    def test_clamp_aero_below_min(self):
        """Test aero values below min are clamped."""
        assert clamp_chassis_aero(0) == CHASSIS_AERO_MIN
        assert clamp_chassis_aero(-5) == CHASSIS_AERO_MIN
    
    def test_clamp_aero_above_max(self):
        """Test aero values above max are clamped."""
        assert clamp_chassis_aero(13) == CHASSIS_AERO_MAX
        assert clamp_chassis_aero(15) == CHASSIS_AERO_MAX
        assert clamp_chassis_aero(100) == CHASSIS_AERO_MAX
    
    def test_clamp_aero_boundary_development_scenario(self):
        """Test clamping during development: aero=11 + 2 = 13 should clamp to 12."""
        current_aero = 11
        delta = 2
        result = clamp_chassis_aero(current_aero + delta)
        assert result == 12  # Clamped to max
    
    def test_clamp_aero_big_gain_scenario(self):
        """Test clamping during big gain: aero=10 + 3 = 13 should clamp to 12."""
        current_aero = 10
        delta = 3
        result = clamp_chassis_aero(current_aero + delta)
        assert result == 12


class TestClampChassisSuspension:
    """Test suite for clamp_chassis_suspension function."""
    
    def test_clamp_suspension_within_range(self):
        """Test suspension values within range are unchanged."""
        assert clamp_chassis_suspension(5) == 5
        assert clamp_chassis_suspension(1) == 1
        assert clamp_chassis_suspension(10) == 10
    
    def test_clamp_suspension_below_min(self):
        """Test suspension values below min are clamped."""
        assert clamp_chassis_suspension(0) == CHASSIS_SUSPENSION_MIN
        assert clamp_chassis_suspension(-3) == CHASSIS_SUSPENSION_MIN
    
    def test_clamp_suspension_above_max(self):
        """Test suspension values above max are clamped."""
        assert clamp_chassis_suspension(11) == CHASSIS_SUSPENSION_MAX
        assert clamp_chassis_suspension(15) == CHASSIS_SUSPENSION_MAX
    
    def test_clamp_suspension_big_gain_scenario(self):
        """Test clamping during big gain: suspension=8 + 3 = 11 should clamp to 10."""
        current = 8
        delta = 3
        result = clamp_chassis_suspension(current + delta)
        assert result == 10


class TestClampChassisWeight:
    """Test suite for clamp_chassis_weight function."""
    
    def test_clamp_weight_within_range(self):
        """Test weight values within range are unchanged."""
        assert clamp_chassis_weight(5) == 5
        assert clamp_chassis_weight(3) == 3
        assert clamp_chassis_weight(10) == 10
    
    def test_clamp_weight_below_min(self):
        """Test weight values below min are clamped."""
        assert clamp_chassis_weight(2) == CHASSIS_WEIGHT_MIN
        assert clamp_chassis_weight(0) == CHASSIS_WEIGHT_MIN
        assert clamp_chassis_weight(-1) == CHASSIS_WEIGHT_MIN
    
    def test_clamp_weight_above_max(self):
        """Test weight values above max are clamped."""
        assert clamp_chassis_weight(11) == CHASSIS_WEIGHT_MAX
        assert clamp_chassis_weight(15) == CHASSIS_WEIGHT_MAX
    
    def test_clamp_weight_big_reduction_scenario(self):
        """Test clamping during big reduction: weight=4 - 2 = 2 should clamp to 3."""
        current = 4
        delta = 2
        result = clamp_chassis_weight(current - delta)
        assert result == 3  # Clamped to min


class TestSequentialModifications:
    """Test that sequential modifications stay within bounds."""
    
    def test_sequential_aero_increases(self):
        """Test that multiple aero increases never exceed max."""
        aero = 5
        for _ in range(20):  # 20 sequential +2 gains
            aero = clamp_chassis_aero(aero + 2)
        assert aero == CHASSIS_AERO_MAX
        assert aero <= 12
    
    def test_sequential_suspension_increases(self):
        """Test that multiple suspension increases never exceed max."""
        suspension = 3
        for _ in range(20):  # 20 sequential +3 gains
            suspension = clamp_chassis_suspension(suspension + 3)
        assert suspension == CHASSIS_SUSPENSION_MAX
        assert suspension <= 10
    
    def test_sequential_weight_decreases(self):
        """Test that multiple weight decreases never go below min."""
        weight = 8
        for _ in range(20):  # 20 sequential -2 reductions
            weight = clamp_chassis_weight(weight - 2)
        assert weight == CHASSIS_WEIGHT_MIN
        assert weight >= 3
    
    def test_mixed_modifications_stay_valid(self):
        """Test that mixed good/bad outcomes keep values valid."""
        import random
        random.seed(42)  # Reproducible
        
        aero = 6
        suspension = 5
        weight = 7
        
        for _ in range(100):
            # Random development outcomes
            aero = clamp_chassis_aero(aero + random.choice([-1, 1, 2, 3]))
            suspension = clamp_chassis_suspension(suspension + random.choice([-1, 1, 2, 3]))
            weight = clamp_chassis_weight(weight + random.choice([-2, -1, 1]))
            
            # Verify bounds after every modification
            assert CHASSIS_AERO_MIN <= aero <= CHASSIS_AERO_MAX
            assert CHASSIS_SUSPENSION_MIN <= suspension <= CHASSIS_SUSPENSION_MAX
            assert CHASSIS_WEIGHT_MIN <= weight <= CHASSIS_WEIGHT_MAX
