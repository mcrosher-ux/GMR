"""Tests for world_economy.py - Economic simulation."""

from gmr.world_economy import (
    COUNTRIES,
    WorldEconomy,
    is_home_race,
    get_home_crowd_bonus
)


class TestCountries:
    """Test suite for country definitions."""
    
    def test_countries_exist(self):
        """Test that countries are defined."""
        assert len(COUNTRIES) > 0
    
    def test_countries_have_required_fields(self):
        """Test that each country has required fields."""
        required_fields = [
            "name", "region", "base_economy", "population_millions",
            "motorsport_culture", "wealth_distribution", "political_stability",
            "industrial_strength", "flavor"
        ]
        
        for country_code, country_data in COUNTRIES.items():
            for field in required_fields:
                assert field in country_data, f"Country {country_code} missing {field}"
    
    def test_country_values_in_valid_ranges(self):
        """Test that country values are in expected ranges."""
        for country_code, country_data in COUNTRIES.items():
            # Economy should be 1-10
            assert 1 <= country_data["base_economy"] <= 10
            
            # Population should be positive
            assert country_data["population_millions"] > 0
            
            # Culture should be 1-10
            assert 1 <= country_data["motorsport_culture"] <= 10
            
            # Wealth distribution should be 0-1
            assert 0 <= country_data["wealth_distribution"] <= 1
            
            # Stability should be 1-10
            assert 1 <= country_data["political_stability"] <= 10
            
            # Industrial strength should be 1-10
            assert 1 <= country_data["industrial_strength"] <= 10
    
    def test_major_countries_exist(self):
        """Test that major racing nations exist."""
        major_countries = ["Italy", "UK", "France", "Germany", "USA"]
        
        for country in major_countries:
            assert country in COUNTRIES


class TestWorldEconomy:
    """Test suite for WorldEconomy class."""
    
    def test_world_economy_initialization(self):
        """Test WorldEconomy initializes correctly."""
        economy = WorldEconomy()
        
        assert economy is not None
        # Check basic attributes exist
        assert hasattr(economy, "country_economies")
        assert hasattr(economy, "active_events")
    
    def test_world_economy_has_countries(self):
        """Test that world economy has countries."""
        economy = WorldEconomy()
        
        # Should have country economies
        assert hasattr(economy, "country_economies")
        assert len(economy.country_economies) > 0


class TestIsHomeRace:
    """Test suite for home race detection."""
    
    def test_is_home_race_with_driver_dict(self):
        """Test detecting home race with driver dict and track dict."""
        driver = {"name": "Test Driver", "country": "Italy"}
        track = {"name": "Monza", "country": "Italy"}
        
        result = is_home_race(driver, track)
        assert result is True
    
    def test_is_home_race_non_matching_country(self):
        """Test detecting non-home race."""
        driver = {"name": "Test Driver", "country": "Italy"}
        track = {"name": "Silverstone", "country": "UK"}
        
        result = is_home_race(driver, track)
        assert result is False


class TestGetHomeCrowdBonus:
    """Test suite for home crowd bonus calculation."""
    
    def test_get_home_crowd_bonus_for_home_race(self):
        """Test home crowd bonus is positive for home races."""
        driver = {"name": "Test Driver", "country": "Italy", "fame": 5}
        track = {"name": "Monza", "country": "Italy"}
        
        bonus = get_home_crowd_bonus(driver, track)
        
        assert isinstance(bonus, (int, float))
        # Home races should provide bonus > 1.0
        assert bonus > 1.0
    
    def test_get_home_crowd_bonus_for_away_race(self):
        """Test home crowd bonus for away races."""
        driver = {"name": "Test Driver", "country": "Italy", "fame": 5}
        track = {"name": "Silverstone", "country": "UK"}
        
        bonus = get_home_crowd_bonus(driver, track)
        
        # Away races should have no bonus (1.0)
        assert isinstance(bonus, (int, float))
        assert bonus == 1.0
    
    def test_get_home_crowd_bonus_scales_with_fame(self):
        """Test that bonus scales with driver fame."""
        driver_low = {"name": "Test Driver", "country": "Italy", "fame": 1}
        driver_high = {"name": "Test Driver", "country": "Italy", "fame": 10}
        track = {"name": "Monza", "country": "Italy"}
        
        bonus_low_fame = get_home_crowd_bonus(driver_low, track)
        bonus_high_fame = get_home_crowd_bonus(driver_high, track)
        
        # Higher fame should give better bonus
        assert bonus_high_fame >= bonus_low_fame
