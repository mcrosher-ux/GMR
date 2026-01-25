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

    # Basic shape checks so we catch accidental breakages.
    assert isinstance(driver, dict)
    assert driver.get("name")
    assert isinstance(driver.get("pace"), int)
    assert isinstance(driver.get("age"), int)
    assert driver.get("peak_age") >= driver.get("age")
