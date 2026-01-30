#!/usr/bin/env python3
"""
Clean up race_engine.py to remove the old duplicate simulation loop.
Keep only:
1. Player damage handling (lines ~2036-2106)
2. Demo finale and post-race logic (from demo finale onwards)
"""

with open(r'c:\Users\mcros\Repos\GMR\gmr\race_engine.py', 'r') as f:
    lines = f.readlines()

# Find all key sections
demo_idx = None
player_damage_start = None
player_damage_end = None
sort_perf_idx = None

for i, line in enumerate(lines):
    # Find player damage code (starts with "# Apply player-specific damage")
    if '# Apply player-specific damage' in line:
        player_damage_start = i
    
    # Find end of player damage (look for "# Sort finishers from simulation")
    if '# Sort finishers from simulation' in line and player_damage_start and not player_damage_end:
        player_damage_end = i
    
    # Find the second "DEMO FINALE" (player race version, around line 2640)
    if i > 2100 and '# DEMO FINALE' in line and 'player race' in line and 'force fatal DNF' in line:
        demo_idx = i
        break

print(f"Player damage starts at: {player_damage_start + 1 if player_damage_start else 'NOT FOUND'}")
print(f"Player damage ends at: {player_damage_end + 1 if player_damage_end else 'NOT FOUND'}")
print(f"Demo finale (player) at: {demo_idx + 1 if demo_idx else 'NOT FOUND'}")

# Now check lines in the old loop area to see what needs to be deleted
print("\nChecking lines 2110-2120 for old loop code:")
for i in range(2109, min(2120, len(lines))):
    print(f"{i+1}: {lines[i][:80]}", end='')

print("\nChecking lines 2630-2645:")
for i in range(2629, min(2645, len(lines))):
    print(f"{i+1}: {lines[i][:80]}", end='')
