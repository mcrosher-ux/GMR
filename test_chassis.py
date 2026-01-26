from gmr.core_state import GameState
from gmr.core_time import GameTime

# Test chassis development initialization
state = GameState()
state.player_constructor = 'Test Team'
time = GameTime(1947)

# Simulate starting a chassis project
state.current_chassis = {
    'id': 'test_chassis',
    'name': 'Test Chassis',
    'supplier': 'Test Supplier',
    'aero': 2,
    'suspension': 3,
    'weight': 7,
    'dev_slots': 1,
    'dev_runs_done': 0
}

print('Chassis development test setup complete')
print(f'Chassis supplier: {state.current_chassis.get("supplier", "None")}')

# Test the supplier_key logic
if state.chassis_project_active and state.current_chassis:
    ch = state.current_chassis
    supplier_key = ch.get("supplier", "")
    print(f'Supplier key: {supplier_key}')