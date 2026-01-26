"""Lightweight smoke tests to ensure core wiring works."""

from gmr.core_state import GameState
from gmr.core_time import GameTime
from gmr.world_logic import create_regen_driver


def test_can_bootstrap_game_state():
    """GameState should construct cleanly with expected defaults."""
    state = GameState()
    assert state is not None
    assert state.money == 5000
    assert state.garage is not None


def test_create_regen_driver_returns_driver_profile():
    """Regeneration driver factory should return a minimally valid profile."""
    time = GameTime()
    driver = create_regen_driver(time)

def test_injury_system_initialized():
    """Injury system fields should be properly initialized."""
    state = GameState()
    assert hasattr(state, 'player_driver_injured')
    assert state.player_driver_injured == False
    assert hasattr(state, 'player_driver_injury_weeks_remaining')
    assert state.player_driver_injury_weeks_remaining == 0
    assert hasattr(state, 'player_driver_injury_severity')
    assert state.player_driver_injury_severity == 0
