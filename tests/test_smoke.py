"""Minimal smoke tests to keep CI green when the suite is empty."""


def test_can_import_core_modules():
    import gmr.world_logic
    import gmr.race_day
    import gmr.careers
    import gmr.constants
    # If imports succeed, the core package wiring is intact.
    assert True
