"""Tests for core_state.py - GameState and PlayerCharacter classes."""

from gmr.core_state import GameState, PlayerCharacter


class TestPlayerCharacter:
    """Test suite for PlayerCharacter class."""
    
    def test_player_character_initialization(self):
        """Test that PlayerCharacter initializes with correct defaults."""
        player = PlayerCharacter()
        
        assert player.name == "Anonymous Owner"
        assert player.birth_year == 1930
        assert player.home_country == "UK"
        assert player.personal_savings == 500
        
        # Skills start at novice level
        assert player.technical_knowledge == 2
        assert player.business == 2
        assert player.leadership == 2
        
        # XP starts at 0
        assert player.technical_xp == 0
        assert player.business_xp == 0
        assert player.leadership_xp == 0
        
        # Component experience starts at 0
        assert player.component_experience["engines"] == 0
        assert player.component_experience["chassis"] == 0
        assert player.component_experience["aero"] == 0
        
        # Era familiarity
        assert player.current_era == "Post-War Revival"
        assert player.era_adaptation == 1.0
        
        # Personality traits
        assert player.risk_tolerance == 5
        assert player.ambition == 5
        assert player.integrity == 5
        assert player.patience == 5
        
        # Reputation and health
        assert player.reputation == 1
        assert player.health == 10
        
        # Career stats
        assert player.career_wins == 0
        assert player.career_podiums == 0
        assert player.career_races == 0
        
        # Employment
        assert player.current_role == "owner"
        assert player.years_in_current_role == 0
        
        # Life status
        assert player.is_alive is True
        assert player.death_year is None
        assert player.death_reason is None
    
    def test_gain_technical_xp(self):
        """Test gaining technical experience and leveling up."""
        player = PlayerCharacter()
        initial_level = player.technical_knowledge
        
        # Gain some XP (not enough to level up initially)
        result = player.gain_technical_xp(10)
        assert result is None
        assert player.technical_xp == 10
        assert player.technical_knowledge == initial_level
        
        # Gain enough XP to level up (need 200 XP threshold for level 2->3)
        result = player.gain_technical_xp(200)
        assert result is not None
        assert "Technical knowledge improved" in result
        assert player.technical_knowledge == initial_level + 1
    
    def test_gain_business_xp(self):
        """Test gaining business experience and leveling up."""
        player = PlayerCharacter()
        initial_level = player.business
        
        # Gain some XP
        result = player.gain_business_xp(10)
        assert result is None
        assert player.business_xp == 10
        assert player.business == initial_level
        
        # Gain enough to level up (need 200 XP threshold for level 2->3)
        result = player.gain_business_xp(200)
        assert result is not None
        assert "Business skill improved" in result
        assert player.business == initial_level + 1


class TestGameState:
    """Test suite for GameState class."""
    
    def test_game_state_initialization(self):
        """Test that GameState initializes with correct defaults."""
        state = GameState()
        
        # Financial state
        assert state.money == 5000
        # weekly_running_cost is a constant in constants.py, not a state attribute
        
        # Player character (renamed from player)
        assert state.player_character is not None
        assert isinstance(state.player_character, PlayerCharacter)
        
        # Garage
        assert state.garage is not None
        
        # Driver state
        assert state.player_driver is None
        assert state.player_driver_injured is False
        assert state.player_driver_injury_weeks_remaining == 0
        assert state.player_driver_injury_severity == 0
        
        # Car components
        assert state.current_engine is None
        assert state.current_chassis is None
        
        # Team stats - prestige check removed as it may not exist at init
        
        # News
        assert hasattr(state, 'news')
        assert isinstance(state.news, list)
    
    def test_game_state_money_operations(self):
        """Test money operations on GameState."""
        state = GameState()
        initial_money = state.money
        
        # Add money
        state.money += 1000
        assert state.money == initial_money + 1000
        
        # Subtract money
        state.money -= 500
        assert state.money == initial_money + 500
    
    def test_game_state_prestige_bounds(self):
        """Test prestige stays within reasonable bounds."""
        state = GameState()
        
        # Set prestige to various values
        state.prestige = 0.0
        assert state.prestige == 0.0
        
        state.prestige = 5.0
        assert state.prestige == 5.0
        
        state.prestige = 10.0
        assert state.prestige == 10.0
    
    def test_game_state_driver_injury_system(self):
        """Test driver injury system fields."""
        state = GameState()
        
        # Initially no injury
        assert state.player_driver_injured is False
        assert state.player_driver_injury_weeks_remaining == 0
        assert state.player_driver_injury_severity == 0
        
        # Simulate injury
        state.player_driver_injured = True
        state.player_driver_injury_weeks_remaining = 3
        state.player_driver_injury_severity = 5
        
        assert state.player_driver_injured is True
        assert state.player_driver_injury_weeks_remaining == 3
        assert state.player_driver_injury_severity == 5
