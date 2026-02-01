"""Tests for world_economy.py - Economic simulation."""

from gmr.world_economy import (
    COUNTRIES,
    WorldEconomy,
    is_home_race,
    get_home_crowd_bonus,
    validate_country,
    get_all_valid_regions,
    _warned_countries,
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


class TestValidateCountry:
    """Test suite for country validation."""
    
    def test_validate_known_country(self):
        """Test validating a known country returns correct data."""
        country_data, region, is_valid = validate_country("Italy")
        
        assert is_valid is True
        assert country_data["name"] == "Italy"
        assert region == "Southern Europe"
    
    def test_validate_all_countries_have_regions(self):
        """Test that all defined countries have valid regions."""
        for country_name in COUNTRIES:
            country_data, region, is_valid = validate_country(country_name)
            
            assert is_valid is True, f"Country '{country_name}' failed validation"
            assert region, f"Country '{country_name}' has no region"
            assert len(region) > 0, f"Country '{country_name}' has empty region"
    
    def test_validate_unknown_country_returns_fallback(self):
        """Test that unknown country returns fallback data."""
        # Clear warnings to ensure test sees the warning
        _warned_countries.discard("Atlantis")
        
        country_data, region, is_valid = validate_country("Atlantis")
        
        assert is_valid is False
        assert region == ""
        # Fallback data should have reasonable defaults
        assert country_data["base_economy"] == 5
        assert country_data["population_millions"] == 20
        assert country_data["motorsport_culture"] == 5
    
    def test_validate_unknown_country_typo(self):
        """Test that a typo is detected as unknown."""
        # Clear warnings
        _warned_countries.discard("Itlay")
        
        country_data, region, is_valid = validate_country("Itlay")  # Typo for Italy
        
        assert is_valid is False
        assert "Itlay" in _warned_countries  # Warning was logged
    
    def test_validate_tracks_have_valid_countries(self):
        """Test that common track countries are all valid."""
        # These are countries used by tracks in the game
        track_countries = [
            "Italy", "UK", "France", "Germany", "USA", 
            "Spain", "Belgium", "Switzerland", "Monaco",
            "Argentina", "Brazil", "Poland", "Japan", "Australia"
        ]
        
        for country in track_countries:
            country_data, region, is_valid = validate_country(country)
            assert is_valid is True, f"Track country '{country}' is not defined in COUNTRIES"


class TestGetAllValidRegions:
    """Test suite for region enumeration."""
    
    def test_get_all_valid_regions_not_empty(self):
        """Test that regions are defined."""
        regions = get_all_valid_regions()
        
        assert len(regions) > 0
    
    def test_get_all_valid_regions_expected_regions(self):
        """Test that expected regions exist."""
        regions = get_all_valid_regions()
        
        expected = [
            "Southern Europe", "Northern Europe", "Western Europe", 
            "Central Europe", "Eastern Europe", "North America",
            "South America", "Asia", "Oceania"
        ]
        
        for region in expected:
            assert region in regions, f"Expected region '{region}' not found"
    
    def test_all_countries_have_valid_region(self):
        """Test that every country's region is in the valid regions set."""
        valid_regions = get_all_valid_regions()
        
        for country_name, country_data in COUNTRIES.items():
            region = country_data.get("region")
            assert region in valid_regions, \
                f"Country '{country_name}' has unknown region '{region}'"


class TestWorldEconomyWithUnknownCountry:
    """Test suite for WorldEconomy handling of unknown countries."""
    
    def test_calculate_attendance_unknown_country(self):
        """Test attendance calculation with unknown country falls back gracefully."""
        # Clear warnings
        _warned_countries.discard("Narnia")
        
        economy = WorldEconomy()
        track_data = {
            "name": "Fantasy Circuit",
            "country": "Narnia",  # Unknown country
            "appearance_base": 50,
            "appearance_prestige_mult": 15,
        }
        
        # Should not crash, should return valid attendance
        attendance, details = economy.calculate_attendance(
            "Fantasy Circuit", track_data, 5.0, 5.0
        )
        
        assert attendance > 0
        assert attendance >= 5000  # Minimum bound
        assert attendance <= 500000  # Maximum bound
        assert details["country"] == "Narnia"
    
    def test_get_current_economy_unknown_country(self):
        """Test economy lookup with unknown country returns default."""
        # Clear warnings
        _warned_countries.discard("Mordor")
        
        economy = WorldEconomy()
        
        # Should return default economy (5) without crashing
        econ = economy.get_current_economy("Mordor")
        
        assert econ == 5  # Default
    
    def test_get_attendance_modifier_unknown_country(self):
        """Test attendance modifier with unknown country returns 1.0."""
        # Clear warnings
        _warned_countries.discard("Westeros")
        
        economy = WorldEconomy()
        
        # Should return 1.0 (no modifier) without crashing
        modifier = economy.get_attendance_modifier("Westeros")
        
        assert modifier == 1.0
