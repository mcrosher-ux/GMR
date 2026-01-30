#!/usr/bin/env python
"""Test the RaceSimulator class."""

from gmr.race_engine import RaceSimulator, STAGE_LABELS, get_ai_car_stats

# Quick test to make sure the class works
print("Testing RaceSimulator...")

# Mock minimal data
class MockState:
    player_driver = {"name": "Test Driver", "pace": 7, "consistency": 6}
    engine_health = 100
    engine_wear = 80
    car_reliability = 7
    current_engine = {"speed": 7, "acceleration": 6, "heat_tolerance": 5}
    current_chassis = {"weight": 5, "aero": 5, "brakes": 5, "suspension": 5}
    car_speed = 7

mock_drivers = [
    {"name": "Driver A", "pace": 8, "consistency": 7, "constructor": "Ferrari", "aggression": 6, "mechanical_sympathy": 5, "wet_skill": 5, "heat_tolerance": 5},
    {"name": "Driver B", "pace": 7, "consistency": 8, "constructor": "Mercedes", "aggression": 4, "mechanical_sympathy": 6, "wet_skill": 6, "heat_tolerance": 6},
    {"name": "Test Driver", "pace": 7, "consistency": 6, "constructor": "Williams", "aggression": 5, "mechanical_sympathy": 5, "wet_skill": 5, "heat_tolerance": 5},
]

mock_quali = [(d, d["pace"]) for d in mock_drivers]
mock_track = {"pace_weight": 1.0, "consistency_weight": 1.0, "engine_danger": 1.0, "crash_danger": 1.0}

state = MockState()
state.player_driver = mock_drivers[2]

try:
    sim = RaceSimulator(
        event_grid=mock_drivers,
        quali_results=mock_quali,
        track_profile=mock_track,
        state=state,
        is_wet=False,
        is_hot=False,
        time=1960,
        grid_risk_mult=1.0,
        race_length_factor=1.0
    )
    print("Created simulator OK")
    
    standings = sim.get_current_standings()
    print(f"Initial standings: {[(pos, d['name']) for pos, d, _ in standings]}")
    
    # Simulate all stages
    for stage_idx in range(3):
        result = sim.simulate_stage(stage_idx, player_strategy_mult=1.0)
        print(f"Stage {stage_idx} result: {len(result['overtakes'])} overtakes, {len(result['incidents'])} incidents")
        
        standings = sim.get_current_standings()
        print(f"  After stage {stage_idx}: {[(pos, d['name']) for pos, d, _ in standings]}")
    
    finishers, dnfs, reasons = sim.get_final_results()
    print(f"\nFinal results: {[(d['name'], score) for d, score in finishers]}")
    print(f"DNFs: {[d['name'] for d in dnfs]}")
    print(f"Reasons: {reasons}")
    
    print("Test PASSED!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
