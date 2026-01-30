#!/usr/bin/env python3
"""
Remove the duplicate render_player_stage_output call
"""

with open(r'c:\Users\mcros\Repos\GMR\gmr\race_engine.py', 'r') as f:
    lines = f.readlines()

# Find and remove the duplicate render call (lines 2147-2149)
# Looking for the pattern:
# "    # Now we have accurate results..."
# "    if player_in_grid and stage_output:"
# "        stage_overtakes = compute_stage_overtakes_from_results..."
# "        render_player_stage_output..."

new_lines = []
skip_until = None

for i, line in enumerate(lines):
    if skip_until is not None:
        if i < skip_until:
            continue
        else:
            skip_until = None
    
    if 'Now we have accurate results' in line:
        # Mark these lines for deletion
        # Look ahead to find the render call
        print(f"Found at line {i+1}: {line.strip()}")
        # Skip the next few lines
        skip_until = i + 7  # Skip this and next 6 lines approximately
        continue
    
    new_lines.append(line)

with open(r'c:\Users\mcros\Repos\GMR\gmr\race_engine.py', 'w') as f:
    f.writelines(new_lines)

print(f"Removed duplicate render call. Total lines before: {len(lines)}, after: {len(new_lines)}")
