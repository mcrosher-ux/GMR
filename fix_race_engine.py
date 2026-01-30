#!/usr/bin/env python3
"""
Remove duplicate old simulation loop code from race_engine.py.
Delete lines 2114-2632 which contain the old loop.
"""

with open(r'c:\Users\mcros\Repos\GMR\gmr\race_engine.py', 'r') as f:
    lines = f.readlines()

# Keep lines 0-2112 (before the bad code starts)
# Skip lines 2113-2632 (the old loop code)
# Keep lines 2633 onwards (the real victim = ... code)

# But first let's be careful - find these markers
markers = {
    'start_bad': None,
    'end_bad': None,
}

for i, line in enumerate(lines):
    # Find where the bad code starts: "consistency_factor = max"
    if i == 2113 and 'consistency_factor = max' in line:
        markers['start_bad'] = i
    
    # Find where it ends: "# Sort by performance"
    # followed by "finishers.sort"
    if i > 2600 and i < 2635 and '# Sort by performance' in line and 'finishers.sort' in lines[i+1]:
        markers['end_bad'] = i

print(f"Start of bad code: {markers['start_bad']+1 if markers['start_bad'] else 'NOT FOUND'}")
print(f"End of bad code: {markers['end_bad']+1 if markers['end_bad'] else 'NOT FOUND'}")

if markers['start_bad'] is not None and markers['end_bad'] is not None:
    # Delete those lines
    new_lines = lines[:markers['start_bad']] + lines[markers['end_bad']:]
    
    with open(r'c:\Users\mcros\Repos\GMR\gmr\race_engine.py', 'w') as f:
        f.writelines(new_lines)
    
    print(f"Deleted {markers['end_bad'] - markers['start_bad']} lines")
    print("File updated!")
else:
    print("Could not find markers - no changes made")
