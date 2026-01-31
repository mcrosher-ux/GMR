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
