# GMR - Motorsport Management Game

A motorsport management simulation game written in Python. Build your racing team from a humble garage in 1947 and compete in the chaotic world of Grand Prix racing through multiple decades and eras akin to Greydog Software simulations and Champ Manager 97.

## Description

In GMR, you inherit your father's old racing car, starting with a small shed and a single mechanic. Navigate the post-war motorsport scene, era of champions, modern age. 

Manage your team's finances, hire drivers, develop your car, secure sponsorships, and race against other constructors across Europe. Survive the era's reliability issues, crashes, and economic challenges to build a legendary racing outfit.

## Features

- **Career Progression**: Start from humble beginnings and grow your team over multiple seasons
- **Car Development**: Upgrade engines, chassis, and manage reliability
- **Driver Management**: Hire, fire, and manage driver contracts and careers
- **Financial Management**: Balance budgets, secure sponsors, and handle expenses
- **Racing Calendar**: Compete in various Grand Prix events across the world
- **Dynamic World**: Rumors, team expansions, and changing market conditions
- **Historical Setting**: Starting in 1947, capturing the spirit of the history of motorsport
- **Track Evolution**: Circuits improve safety and facilities over time, with FIA grade requirements changing through the eras
- **Global Expansion**: Race in Europe, Americas, Africa, and Asia as the calendar expands through the years

## Requirements

- Python 3.6 or higher
- No external dependencies required

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mcrosher-ux/GMR.git
   cd GMR
   ```

2. Run the game:
   ```bash
   python main.py
   ```

## Gameplay

The game is played through a text-based interface. You'll make decisions each week about:

- Racing strategy
- Car upgrades
- Driver hires/fires
- Business development
- PR activities



Follow the on-screen prompts to manage your team and compete in races.

## Future Development Notes

### Track Evolution System (Implemented)
Tracks are now living entities with dynamic ratings:
- **Safety Rating** (1-10): Affects driver survival chances in crashes
- **Facilities Rating** (1-10): Grandstands, pits, medical facilities
- **Prestige Rating** (1-10): Historical importance and crowd appeal
- **FIA Grades**: A (World Championship), B (International), C (Regional), D (Club)

FIA thresholds increase over time:
- **1947-1955**: Lenient standards (Grade A needs safety 3+)
- **1956-1965**: Rising standards (Grade A needs safety 5+)
- **1966-1975**: Safety focus (Grade A needs safety 6+)
- **1976+**: Modern era (Grade A needs safety 7+)

Tracks can upgrade after:
- Fatal accidents (public pressure for safety)
- Profitable seasons (grandstand expansion)
- FIA mandates (meet new standards or lose grade)

### Cars as Entities (Planned)
Currently, teams have a `max_drivers` limit but cars are implicit. Future plans include:
- **Car Objects**: Each team owns explicit car entities that must be built/purchased
- **Multi-Car Teams**: Teams with resources can build additional cars to field more drivers
- **Car Lifespan**: Cars degrade, can be crashed/destroyed, requiring rebuilds
- **Driver-Car Assignment**: Drivers assigned to specific chassis
- **Entry Rules**: Some races limit entries per team based on regulations
- **Privateer Sales**: Big teams may sell customer chassis to smaller outfits

This system would make poaching more meaningful - stealing a driver leaves the car without a pilot until the team can recruit a replacement, rather than the car magically disappearing.

## Credits

A/M Crosher
