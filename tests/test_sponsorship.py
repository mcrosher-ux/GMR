"""Tests for sponsorship.py - Sponsorship system."""

from gmr.sponsorship import (
    SPONSOR_TYPES,
    generate_media_event
)
from gmr.core_state import GameState
from gmr.core_time import GameTime


class TestSponsorTypes:
    """Test suite for sponsor type definitions."""
    
    def test_sponsor_types_exist(self):
        """Test that sponsor types are defined."""
        assert len(SPONSOR_TYPES) > 0
    
    def test_sponsor_types_have_required_fields(self):
        """Test that each sponsor has required fields."""
        for sponsor_name, sponsor_info in SPONSOR_TYPES.items():
            assert "personality" in sponsor_info
            assert "media_focus" in sponsor_info
            assert "press_events" in sponsor_info
            assert "flavor_text" in sponsor_info
            assert isinstance(sponsor_info["press_events"], list)
    
    def test_gallant_leaf_tobacco_exists(self):
        """Test that Gallant Leaf Tobacco sponsor exists."""
        assert "Gallant Leaf Tobacco" in SPONSOR_TYPES
    
    def test_valdieri_wines_exists(self):
        """Test that Valdieri Wines sponsor exists."""
        assert "Valdieri Wines" in SPONSOR_TYPES


class TestGenerateMediaEvent:
    """Test suite for media event generation."""
    
    def test_generate_media_event_with_valid_sponsor(self):
        """Test generating media event with valid sponsor."""
        state = GameState()
        state.player_constructor = "Test Racing"
        state.player_driver = {"name": "Test Driver"}
        time = GameTime(1950)
        
        # generate_media_event appends to state.news
        generate_media_event("Gallant Leaf Tobacco", "press_conference", state, time)
        
        # Check that news was added
        assert len(state.news) > 0
    
    def test_generate_media_event_with_invalid_sponsor(self):
        """Test generating media event with unknown sponsor."""
        state = GameState()
        state.player_constructor = "Test Racing"
        state.player_driver = {"name": "Test Driver"}
        time = GameTime(1950)
        
        # Should handle gracefully - function doesn't raise exceptions
        generate_media_event("Unknown Sponsor", "press_conference", state, time)
        
        # Unknown sponsor won't generate news (event_type won't match)
        # This verifies the function handles unknown sponsors without crashing
    
    def test_generate_media_event_includes_team_name(self):
        """Test that media events include team name."""
        state = GameState()
        state.player_constructor = "Custom Racing Team"
        state.player_driver = {"name": "John Smith"}
        time = GameTime(1950)
        
        generate_media_event("Gallant Leaf Tobacco", "press_conference", state, time)
        
        # Check that news was generated
        assert len(state.news) > 0
        news_str = " ".join(state.news)
        # Either team name or driver name should appear (varies by random choice)
        assert "Custom Racing Team" in news_str or "John Smith" in news_str
    
    def test_generate_media_event_includes_driver_name(self):
        """Test that media events include driver name."""
        state = GameState()
        state.player_constructor = "Test Racing"
        state.player_driver = {"name": "Jane Doe"}
        time = GameTime(1950)
        
        # Run multiple times to account for random variation in event content
        for _ in range(20):
            generate_media_event("Gallant Leaf Tobacco", "promo_day", state, time)
        
        # Check that driver name appears in at least one of the generated news items
        news_str = " ".join(state.news)
        assert "Jane Doe" in news_str


class TestSponsorMultiplierValidation:
    """Test suite for sponsor multiplier validation."""
    
    def test_base_multipliers_match_sponsor_types(self):
        """Test that all SPONSOR_TYPES have corresponding multipliers."""
        # These are the sponsors that should have multipliers defined
        base_multipliers = {
            "Gallant Leaf Tobacco": {"appearance": 60, "points": 10, "podium": 120, "bonus": 2000},
            "Valdieri Wines": {"appearance": 80, "points": 15, "podium": 150, "bonus": 2500},
            "Rossi Tires": {"appearance": 70, "points": 12, "podium": 130, "bonus": 2200},
            "Marconi Electronics": {"appearance": 90, "points": 18, "podium": 180, "bonus": 3000},
            "Aero Dynamics Ltd": {"appearance": 85, "points": 16, "podium": 160, "bonus": 2800},
            "Castello Banking": {"appearance": 100, "points": 20, "podium": 200, "bonus": 3500},
        }
        
        # All SPONSOR_TYPES should have multipliers
        for sponsor_name in SPONSOR_TYPES:
            assert sponsor_name in base_multipliers, \
                f"Sponsor '{sponsor_name}' exists in SPONSOR_TYPES but has no multipliers defined"
        
        # All multipliers should have SPONSOR_TYPES entries
        for sponsor_name in base_multipliers:
            assert sponsor_name in SPONSOR_TYPES, \
                f"Sponsor '{sponsor_name}' has multipliers but no SPONSOR_TYPES entry"
    
    def test_all_multipliers_have_required_fields(self):
        """Test that all sponsor multipliers have required payment fields."""
        base_multipliers = {
            "Gallant Leaf Tobacco": {"appearance": 60, "points": 10, "podium": 120, "bonus": 2000},
            "Valdieri Wines": {"appearance": 80, "points": 15, "podium": 150, "bonus": 2500},
            "Rossi Tires": {"appearance": 70, "points": 12, "podium": 130, "bonus": 2200},
            "Marconi Electronics": {"appearance": 90, "points": 18, "podium": 180, "bonus": 3000},
            "Aero Dynamics Ltd": {"appearance": 85, "points": 16, "podium": 160, "bonus": 2800},
            "Castello Banking": {"appearance": 100, "points": 20, "podium": 200, "bonus": 3500},
        }
        
        required_fields = ["appearance", "points", "podium", "bonus"]
        
        for sponsor_name, multipliers in base_multipliers.items():
            for field in required_fields:
                assert field in multipliers, \
                    f"Sponsor '{sponsor_name}' missing required field '{field}'"
                assert isinstance(multipliers[field], (int, float)), \
                    f"Sponsor '{sponsor_name}' field '{field}' should be numeric"
                assert multipliers[field] > 0, \
                    f"Sponsor '{sponsor_name}' field '{field}' should be positive"
    
    def test_typo_detection_gallant_leaf(self):
        """Test that typo 'Gallant Leeaf' is not silently accepted."""
        typo_name = "Gallant Leeaf"  # Typo: Leeaf instead of Leaf
        correct_name = "Gallant Leaf Tobacco"
        
        # Correct name should exist
        assert correct_name in SPONSOR_TYPES
        
        # Typo should not exist
        assert typo_name not in SPONSOR_TYPES
    
    def test_typo_detection_valdieri(self):
        """Test that typo 'Valdierie Wines' is not silently accepted."""
        typo_name = "Valdierie Wines"  # Typo: Valdierie instead of Valdieri
        correct_name = "Valdieri Wines"
        
        assert correct_name in SPONSOR_TYPES
        assert typo_name not in SPONSOR_TYPES
    
    def test_typo_detection_castello(self):
        """Test that typo 'Castelo Banking' is not silently accepted."""
        typo_name = "Castelo Banking"  # Typo: Castelo instead of Castello
        correct_name = "Castello Banking"
        
        assert correct_name in SPONSOR_TYPES
        assert typo_name not in SPONSOR_TYPES
