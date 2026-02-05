# gmr/driver_traits.py
# Driver personality traits system

import random

# =============================================================================
# DRIVER TRAITS DEFINITIONS
# =============================================================================

DRIVER_TRAITS = {
    # POSITIVE TRAITS
    "natural_talent": {
        "name": "Natural Talent",
        "description": "Learns faster than other drivers",
        "type": "positive",
        "effects": {
            "xp_multiplier": 1.3,
        },
        "rarity": 0.08,  # 8% chance
    },
    "ice_cool": {
        "name": "Ice Cool",
        "description": "Exceptional composure under pressure",
        "type": "positive",
        "effects": {
            "consistency_bonus": 1,
            "crash_mult": 0.85,
        },
        "rarity": 0.10,
    },
    "rain_master": {
        "name": "Rain Master",
        "description": "Thrives in wet conditions",
        "type": "positive",
        "effects": {
            "wet_skill_bonus": 2,
            "wet_crash_mult": 0.7,
        },
        "rarity": 0.12,
    },
    "mechanical_genius": {
        "name": "Mechanical Genius",
        "description": "Exceptional car care and feedback",
        "type": "positive",
        "effects": {
            "mechanical_sympathy_bonus": 2,
            "engine_fail_mult": 0.8,
        },
        "rarity": 0.10,
    },
    "quali_specialist": {
        "name": "Qualifying Specialist",
        "description": "Extracts maximum performance over one lap",
        "type": "positive",
        "effects": {
            "quali_pace_bonus": 1,
        },
        "rarity": 0.12,
    },
    "crowd_favorite": {
        "name": "Crowd Favorite",
        "description": "Natural charisma builds fame faster",
        "type": "positive",
        "effects": {
            "fame_multiplier": 1.4,
        },
        "rarity": 0.10,
    },
    "overtaking_ace": {
        "name": "Overtaking Ace",
        "description": "Exceptional at passing other drivers",
        "type": "positive",
        "effects": {
            "overtake_bonus": 1.2,
        },
        "rarity": 0.10,
    },
    
    # NEGATIVE TRAITS
    "hothead": {
        "name": "Hothead",
        "description": "Aggressive and crash-prone under pressure",
        "type": "negative",
        "effects": {
            "crash_mult": 1.4,
            "aggression_bonus": 1,
        },
        "rarity": 0.12,
    },
    "gold_digger": {
        "name": "Gold Digger",
        "description": "Always demands top dollar",
        "type": "negative",
        "effects": {
            "salary_multiplier": 1.5,
        },
        "rarity": 0.10,
    },
    "inconsistent": {
        "name": "Inconsistent",
        "description": "Performance varies wildly race to race",
        "type": "negative",
        "effects": {
            "consistency_penalty": 1,
            "performance_variance": 1.4,
        },
        "rarity": 0.12,
    },
    "mechanical_ignorance": {
        "name": "Hard on Equipment",
        "description": "Tough on machinery, more breakdowns",
        "type": "negative",
        "effects": {
            "mechanical_sympathy_penalty": 1,
            "engine_fail_mult": 1.3,
        },
        "rarity": 0.10,
    },
    "slow_learner": {
        "name": "Slow Learner",
        "description": "Takes longer to improve and adapt",
        "type": "negative",
        "effects": {
            "xp_multiplier": 0.7,
        },
        "rarity": 0.08,
    },
    "camera_shy": {
        "name": "Camera Shy",
        "description": "Avoids publicity, gains fame slowly",
        "type": "negative",
        "effects": {
            "fame_multiplier": 0.6,
        },
        "rarity": 0.08,
    },
    "wet_weather_weakness": {
        "name": "Wet Weather Weakness",
        "description": "Struggles badly in the rain",
        "type": "negative",
        "effects": {
            "wet_skill_penalty": 1,
            "wet_crash_mult": 1.4,
        },
        "rarity": 0.10,
    },
    
    # NEUTRAL/MIXED TRAITS
    "maverick": {
        "name": "Maverick",
        "description": "Unpredictable: brilliant or disastrous",
        "type": "mixed",
        "effects": {
            "pace_bonus": 1,
            "crash_mult": 1.2,
            "performance_variance": 1.3,
        },
        "rarity": 0.10,
    },
    "showboat": {
        "name": "Showboat",
        "description": "Loves the spotlight but takes risks",
        "type": "mixed",
        "effects": {
            "fame_multiplier": 1.3,
            "aggression_bonus": 1,
            "crash_mult": 1.15,
        },
        "rarity": 0.08,
    },
}

# Traits that can be earned during career based on achievements/events
EARNABLE_TRAITS = {
    "veteran_wisdom": {
        "name": "Veteran Wisdom",
        "description": "Years of experience pay dividends",
        "type": "positive",
        "effects": {
            "consistency_bonus": 1,
            "mechanical_sympathy_bonus": 1,
        },
        "earn_condition": "age >= 40 and total_starts >= 50",
    },
    "championship_mentality": {
        "name": "Championship Mentality",
        "description": "Proven winner with killer instinct",
        "type": "positive",
        "effects": {
            "pace_bonus": 1,
            "consistency_bonus": 1,
        },
        "earn_condition": "championships >= 1",
    },
    "crash_prone": {
        "name": "Crash Prone",
        "description": "History of accidents follows them",
        "type": "negative",
        "effects": {
            "crash_mult": 1.3,
        },
        "earn_condition": "crash_dnfs >= 10",
    },
    "reliable_finisher": {
        "name": "Reliable Finisher",
        "description": "Always brings the car home",
        "type": "positive",
        "effects": {
            "engine_fail_mult": 0.85,
            "mechanical_sympathy_bonus": 1,
        },
        "earn_condition": "consecutive_finishes >= 8",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_trait_effect(traits, effect_name, default=1.0):
    """
    Get the combined effect of all traits for a specific stat.
    Multipliers are multiplicative, bonuses are additive.
    """
    if not traits:
        return default
    
    total = default
    for trait_id in traits:
        trait_data = DRIVER_TRAITS.get(trait_id) or EARNABLE_TRAITS.get(trait_id)
        if not trait_data:
            continue
        
        effects = trait_data.get("effects", {})
        if effect_name in effects:
            value = effects[effect_name]
            # Multipliers are multiplicative
            if "_multiplier" in effect_name or "_mult" in effect_name:
                total *= value
            # Bonuses/penalties are additive
            elif "_bonus" in effect_name or "_penalty" in effect_name:
                if "_penalty" in effect_name:
                    total -= value
                else:
                    total += value
    
    return total


def assign_starting_traits(driver):
    """
    Assign 0-2 random traits to a driver at game start.
    Chance for traits increases with fame.
    """
    if "traits" not in driver:
        driver["traits"] = []
    
    fame = driver.get("fame", 0)
    
    # Base chance: 40% for first trait, 20% for second
    # Fame increases odds: +10% per fame point
    first_trait_chance = 0.4 + (fame * 0.1)
    second_trait_chance = 0.2 + (fame * 0.08)
    
    # Roll for first trait
    if random.random() < first_trait_chance:
        available_traits = [
            trait_id for trait_id, data in DRIVER_TRAITS.items()
            if random.random() < data["rarity"]
        ]
        if available_traits:
            trait = random.choice(available_traits)
            driver["traits"].append(trait)
    
    # Roll for second trait (if they have first)
    if len(driver["traits"]) > 0 and random.random() < second_trait_chance:
        # Can't have the same trait twice
        available_traits = [
            trait_id for trait_id, data in DRIVER_TRAITS.items()
            if trait_id not in driver["traits"] and random.random() < data["rarity"]
        ]
        if available_traits:
            trait = random.choice(available_traits)
            driver["traits"].append(trait)


def check_earnable_traits(driver, state):
    """
    Check if driver has earned any new traits based on their career stats.
    Called after each race.
    """
    if "traits" not in driver:
        driver["traits"] = []
    
    driver_name = driver.get("name")
    if not driver_name:
        return
    
    # Get driver history
    history = None
    if hasattr(state, 'driver_histories') and state.driver_histories:
        history = state.driver_histories.get(driver_name)
    
    if not history:
        return
    
    summary = history.get_career_summary()
    age = driver.get("age", 25)
    
    # Build context for eval
    context = {
        "age": age,
        "total_starts": summary.get("starts", 0),
        "championships": summary.get("championships", 0),
        "crash_dnfs": sum(1 for r in history.race_results if r.get("dnf") and r.get("dnf_reason") == "crash"),
        "consecutive_finishes": history.consecutive_finishes,
    }
    
    # Check each earnable trait
    for trait_id, trait_data in EARNABLE_TRAITS.items():
        # Skip if already has this trait
        if trait_id in driver["traits"]:
            continue
        
        condition = trait_data.get("earn_condition", "")
        try:
            if eval(condition, {"__builtins__": {}}, context):
                driver["traits"].append(trait_id)
                # News event
                state.news.append(
                    f"🏆 {driver_name} earns the '{trait_data['name']}' trait: {trait_data['description']}"
                )
        except:
            pass  # Silently fail on bad conditions


def format_trait_display(trait_id):
    """Format a trait for UI display."""
    trait_data = DRIVER_TRAITS.get(trait_id) or EARNABLE_TRAITS.get(trait_id)
    if not trait_data:
        return ""
    
    trait_type = trait_data.get("type", "neutral")
    emoji = "✨" if trait_type == "positive" else "⚠️" if trait_type == "negative" else "🔀"
    
    return f"{emoji} {trait_data['name']}: {trait_data['description']}"


def get_trait_modifiers_summary(driver):
    """Get a readable summary of all trait effects on a driver."""
    if "traits" not in driver or not driver["traits"]:
        return []
    
    effects = []
    for trait_id in driver["traits"]:
        trait_data = DRIVER_TRAITS.get(trait_id) or EARNABLE_TRAITS.get(trait_id)
        if not trait_data:
            continue
        
        trait_effects = trait_data.get("effects", {})
        for effect_name, value in trait_effects.items():
            if "_multiplier" in effect_name:
                pct = int((value - 1.0) * 100)
                effects.append(f"{effect_name.replace('_multiplier', '')}: {pct:+d}%")
            elif "_mult" in effect_name:
                pct = int((value - 1.0) * 100)
                effects.append(f"{effect_name.replace('_mult', '')}: {pct:+d}%")
            elif "_bonus" in effect_name:
                effects.append(f"{effect_name.replace('_bonus', '')}: +{int(value)}")
            elif "_penalty" in effect_name:
                effects.append(f"{effect_name.replace('_penalty', '')}: -{int(value)}")
    
    return effects
