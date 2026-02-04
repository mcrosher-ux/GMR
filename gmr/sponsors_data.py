# gmr/sponsors_data.py
# Expanded sponsorship system with multiple sponsors, goals, and events

"""
SPONSORSHIP SYSTEM OVERVIEW:
- Teams can have multiple sponsor slots (starts with 1, increases over time and prestige)
- Each sponsor has a TIER: Title (pays most), Technical, Associate (pays least)
- Different sponsors have different goals, payment structures, and random events
- Failing goals has consequences; exceeding them gives bonuses
"""

import random

# =============================================================================
# SPONSOR SLOT RULES
# =============================================================================
def get_max_sponsor_slots(year, prestige):
    """
    Determine how many sponsor slots a team can have.
    Early era: 1 slot
    Late 50s: 2 slots  
    60s with high prestige: 3 slots
    """
    base_slots = 1
    
    # Second slot unlocks in 1958 (commercial era begins)
    if year >= 1958:
        base_slots = 2
    
    # Third slot requires 1965+ AND high prestige (era of livery sponsorship)
    if year >= 1965 and prestige >= 12.0:
        base_slots = 3
    
    return base_slots


# =============================================================================
# SPONSOR TIERS - Determines payment level and exclusivity
# =============================================================================
SPONSOR_TIERS = {
    "title": {
        "name": "Title Sponsor",
        "description": "Primary sponsor - name on the car, biggest payments",
        "payment_mult": 1.0,
        "max_per_team": 1,
        "min_prestige": 3.0,
    },
    "technical": {
        "name": "Technical Partner", 
        "description": "Supplies equipment or expertise, medium payments",
        "payment_mult": 0.6,
        "max_per_team": 1,
        "min_prestige": 2.0,
    },
    "associate": {
        "name": "Associate Sponsor",
        "description": "Secondary branding, smaller payments",
        "payment_mult": 0.35,
        "max_per_team": 2,
        "min_prestige": 1.0,
    },
}


# =============================================================================
# SPONSOR DATABASE - All available sponsors
# =============================================================================
SPONSORS = {
    # =========================================================================
    # TOBACCO COMPANIES (High paying, controversial later)
    # =========================================================================
    "Gallant Leaf Tobacco": {
        "industry": "tobacco",
        "tier": "title",
        "flavor": "The ambitious tobacco brand pushing into motorsport",
        "personality": "aggressive_marketing",
        "available_from": 1947,
        "available_until": 2005,  # Tobacco bans
        "min_prestige": 2.0,
        "base_payments": {
            "signing_bonus": 2000,
            "appearance": 60,
            "points": 10,
            "podium": 120,
            "win": 250,
        },
        "goals": {
            "races_to_start": 3,
            "podiums_required": 1,
        },
        "goal_bonuses": {
            "races_completed": 500,
            "podium_achieved": 1000,
        },
        "events": ["driver_promo", "advert_shoot", "brand_controversy"],
    },
    
    "Imperial Smoke Co.": {
        "industry": "tobacco",
        "tier": "title",
        "flavor": "The established tobacco empire seeking racing prestige",
        "personality": "corporate_traditional",
        "available_from": 1950,
        "available_until": 2005,
        "min_prestige": 5.0,
        "base_payments": {
            "signing_bonus": 3500,
            "appearance": 85,
            "points": 15,
            "podium": 180,
            "win": 400,
        },
        "goals": {
            "races_to_start": 5,
            "podiums_required": 2,
            "min_finish": 6,
        },
        "goal_bonuses": {
            "races_completed": 800,
            "podium_achieved": 1500,
            "all_goals": 2000,
        },
        "events": ["driver_promo", "brand_controversy", "exclusive_party"],
    },

    # =========================================================================
    # ALCOHOL / BEVERAGES
    # =========================================================================
    "Valdieri Wines": {
        "industry": "alcohol",
        "tier": "title",
        "flavor": "The prestigious Italian wine family branching into racing",
        "personality": "elegant_traditional",
        "available_from": 1947,
        "available_until": 2100,
        "min_prestige": 3.0,
        "base_payments": {
            "signing_bonus": 2500,
            "appearance": 80,
            "points": 15,
            "podium": 150,
            "win": 300,
        },
        "goals": {
            "races_to_start": 4,
            "podiums_required": 1,
        },
        "goal_bonuses": {
            "races_completed": 600,
            "podium_achieved": 1200,
        },
        "events": ["vip_dinner", "wine_tasting", "charity_gala"],
    },
    
    "Brennan's Whisky": {
        "industry": "alcohol",
        "tier": "associate",
        "flavor": "The Scottish distillery seeking international exposure",
        "personality": "traditional_proud",
        "available_from": 1948,
        "available_until": 2100,
        "min_prestige": 1.5,
        "base_payments": {
            "signing_bonus": 800,
            "appearance": 30,
            "points": 5,
            "podium": 60,
            "win": 120,
        },
        "goals": {
            "races_to_start": 3,
        },
        "goal_bonuses": {
            "races_completed": 300,
        },
        "events": ["brand_event", "hospitality"],
    },
    
    "Côte d'Or Champagne": {
        "industry": "alcohol", 
        "tier": "title",
        "flavor": "The French champagne house celebrating victory in style",
        "personality": "luxurious_elite",
        "available_from": 1952,
        "available_until": 2100,
        "min_prestige": 6.0,
        "base_payments": {
            "signing_bonus": 3000,
            "appearance": 90,
            "points": 18,
            "podium": 200,
            "win": 450,
        },
        "goals": {
            "races_to_start": 4,
            "wins_required": 1,
            "podiums_required": 2,
        },
        "goal_bonuses": {
            "races_completed": 700,
            "podium_achieved": 1000,
            "win_achieved": 2500,
        },
        "events": ["podium_celebration", "vip_dinner", "exclusive_party"],
    },

    # =========================================================================
    # FUEL / OIL COMPANIES
    # =========================================================================
    "Petrolux Fuels": {
        "industry": "fuel",
        "tier": "technical",
        "flavor": "The fuel company proving their blend on the track",
        "personality": "technical_focused",
        "available_from": 1947,
        "available_until": 2100,
        "min_prestige": 2.0,
        "base_payments": {
            "signing_bonus": 1500,
            "appearance": 50,
            "points": 8,
            "podium": 100,
            "win": 200,
        },
        "goals": {
            "races_to_start": 4,
            "no_engine_failures": 3,  # Complete 3 races without engine DNF
        },
        "goal_bonuses": {
            "races_completed": 400,
            "reliability_bonus": 800,
        },
        "events": ["fuel_test", "technical_demo"],
        "special_bonus": {"engine_reliability": 0.02},  # Slight reliability boost
    },
    
    "Royal Dutch Petroleum": {
        "industry": "fuel",
        "tier": "title",
        "flavor": "The petroleum giant investing heavily in motorsport",
        "personality": "corporate_ambitious",
        "available_from": 1950,
        "available_until": 2100,
        "min_prestige": 4.0,
        "base_payments": {
            "signing_bonus": 2800,
            "appearance": 75,
            "points": 12,
            "podium": 140,
            "win": 300,
        },
        "goals": {
            "races_to_start": 5,
            "podiums_required": 1,
            "min_finish": 8,
        },
        "goal_bonuses": {
            "races_completed": 600,
            "podium_achieved": 1000,
        },
        "events": ["fuel_test", "press_conference", "technical_demo"],
        "special_bonus": {"engine_reliability": 0.03},
    },

    # =========================================================================
    # TYRE COMPANIES
    # =========================================================================
    "Rossi Tires": {
        "industry": "tyres",
        "tier": "technical",
        "flavor": "The Italian tire manufacturer proving their rubber on the track",
        "personality": "performance_driven",
        "available_from": 1947,
        "available_until": 2100,
        "min_prestige": 2.0,
        "base_payments": {
            "signing_bonus": 1200,
            "appearance": 45,
            "points": 8,
            "podium": 90,
            "win": 180,
        },
        "goals": {
            "races_to_start": 4,
            "min_finish": 10,
        },
        "goal_bonuses": {
            "races_completed": 350,
            "finish_bonus": 500,
        },
        "events": ["tyre_test", "technical_demo", "performance_review"],
        "special_bonus": {"free_tyres": 2},  # Free tyre sets per race
    },
    
    "Continental Gummi": {
        "industry": "tyres",
        "tier": "technical",
        "flavor": "The German tyre manufacturer with engineering precision",
        "personality": "methodical_german",
        "available_from": 1952,
        "available_until": 2100,
        "min_prestige": 4.0,
        "base_payments": {
            "signing_bonus": 1800,
            "appearance": 55,
            "points": 10,
            "podium": 110,
            "win": 220,
        },
        "goals": {
            "races_to_start": 5,
            "podiums_required": 1,
        },
        "goal_bonuses": {
            "races_completed": 500,
            "podium_achieved": 800,
        },
        "events": ["tyre_test", "engineering_review", "technical_demo"],
        "special_bonus": {"free_tyres": 3},
    },

    # =========================================================================
    # ELECTRONICS / TECHNOLOGY
    # =========================================================================
    "Marconi Electronics": {
        "industry": "electronics",
        "tier": "technical",
        "flavor": "The electronics giant showcasing cutting-edge technology",
        "personality": "innovative_technical",
        "available_from": 1950,
        "available_until": 2100,
        "min_prestige": 4.0,
        "base_payments": {
            "signing_bonus": 2200,
            "appearance": 65,
            "points": 12,
            "podium": 130,
            "win": 260,
        },
        "goals": {
            "races_to_start": 4,
            "min_finish": 8,
        },
        "goal_bonuses": {
            "races_completed": 500,
            "finish_bonus": 700,
        },
        "events": ["tech_demo", "innovation_showcase", "press_conference"],
    },
    
    "Horizon Radio Co.": {
        "industry": "electronics",
        "tier": "associate",
        "flavor": "The radio company seeking a younger audience",
        "personality": "modern_media",
        "available_from": 1948,
        "available_until": 1975,
        "min_prestige": 1.0,
        "base_payments": {
            "signing_bonus": 600,
            "appearance": 25,
            "points": 4,
            "podium": 50,
            "win": 100,
        },
        "goals": {
            "races_to_start": 3,
        },
        "goal_bonuses": {
            "races_completed": 250,
        },
        "events": ["radio_interview", "brand_event"],
    },

    # =========================================================================
    # WATCHES / LUXURY GOODS
    # =========================================================================
    "Chronos Watches": {
        "industry": "luxury",
        "tier": "associate",
        "flavor": "The Swiss watchmaker timing racing excellence",
        "personality": "precision_craftsmanship",
        "available_from": 1947,
        "available_until": 2100,
        "min_prestige": 3.0,
        "base_payments": {
            "signing_bonus": 1000,
            "appearance": 40,
            "points": 6,
            "podium": 80,
            "win": 150,
        },
        "goals": {
            "races_to_start": 3,
            "fastest_laps": 1,  # Set at least 1 fastest lap
        },
        "goal_bonuses": {
            "races_completed": 300,
            "fastest_lap_bonus": 600,
        },
        "events": ["timing_partnership", "luxury_showcase"],
    },
    
    "Maison Laurent": {
        "industry": "luxury",
        "tier": "title",
        "flavor": "The Parisian fashion house embracing motorsport glamour",
        "personality": "glamorous_elite",
        "available_from": 1955,
        "available_until": 2100,
        "min_prestige": 8.0,
        "base_payments": {
            "signing_bonus": 4000,
            "appearance": 100,
            "points": 20,
            "podium": 220,
            "win": 500,
        },
        "goals": {
            "races_to_start": 5,
            "podiums_required": 3,
            "wins_required": 1,
        },
        "goal_bonuses": {
            "races_completed": 800,
            "podium_achieved": 1500,
            "win_achieved": 3000,
        },
        "events": ["fashion_photoshoot", "exclusive_party", "vip_dinner"],
    },

    # =========================================================================
    # BANKING / FINANCE
    # =========================================================================
    "Castello Banking": {
        "industry": "finance",
        "tier": "title",
        "flavor": "The international banking house with racing ambitions",
        "personality": "prestigious_elite",
        "available_from": 1952,
        "available_until": 2100,
        "min_prestige": 7.0,
        "base_payments": {
            "signing_bonus": 3500,
            "appearance": 100,
            "points": 20,
            "podium": 200,
            "win": 450,
        },
        "goals": {
            "races_to_start": 5,
            "podiums_required": 2,
            "championship_position": 5,  # Finish top 5 in championship
        },
        "goal_bonuses": {
            "races_completed": 700,
            "podium_achieved": 1200,
            "championship_bonus": 2500,
        },
        "events": ["private_dinner", "elite_gathering", "philanthropy_event"],
    },
    
    "Merchant's Trust": {
        "industry": "finance",
        "tier": "associate",
        "flavor": "The merchant bank seeking sporting prestige",
        "personality": "conservative_business",
        "available_from": 1950,
        "available_until": 2100,
        "min_prestige": 3.0,
        "base_payments": {
            "signing_bonus": 1200,
            "appearance": 45,
            "points": 8,
            "podium": 90,
            "win": 180,
        },
        "goals": {
            "races_to_start": 4,
            "min_finish": 10,
        },
        "goal_bonuses": {
            "races_completed": 400,
            "finish_bonus": 500,
        },
        "events": ["corporate_dinner", "press_conference"],
    },

    # =========================================================================
    # AVIATION / AEROSPACE
    # =========================================================================
    "Aero Dynamics Ltd": {
        "industry": "aerospace",
        "tier": "technical",
        "flavor": "The aviation spin-off bringing aerospace tech to racing",
        "personality": "cutting_edge_research",
        "available_from": 1950,
        "available_until": 2100,
        "min_prestige": 5.0,
        "base_payments": {
            "signing_bonus": 2000,
            "appearance": 60,
            "points": 12,
            "podium": 140,
            "win": 280,
        },
        "goals": {
            "races_to_start": 4,
            "podiums_required": 1,
        },
        "goal_bonuses": {
            "races_completed": 500,
            "podium_achieved": 900,
        },
        "events": ["wind_tunnel_demo", "research_presentation", "technical_demo"],
        "special_bonus": {"aero_development": 0.05},  # Faster aero development
    },
    
    "Skyward Aviation": {
        "industry": "aerospace",
        "tier": "title",
        "flavor": "The aircraft manufacturer investing in ground-level speed",
        "personality": "ambitious_technical",
        "available_from": 1955,
        "available_until": 2100,
        "min_prestige": 6.0,
        "base_payments": {
            "signing_bonus": 3200,
            "appearance": 85,
            "points": 16,
            "podium": 180,
            "win": 380,
        },
        "goals": {
            "races_to_start": 5,
            "podiums_required": 2,
            "fastest_laps": 2,
        },
        "goal_bonuses": {
            "races_completed": 650,
            "podium_achieved": 1100,
            "fastest_lap_bonus": 800,
        },
        "events": ["air_show_appearance", "technical_demo", "press_conference"],
    },

    # =========================================================================
    # AUTOMOTIVE PARTS
    # =========================================================================
    "Bosch Components": {
        "industry": "auto_parts",
        "tier": "technical",
        "flavor": "The German precision engineering company",
        "personality": "methodical_german",
        "available_from": 1948,
        "available_until": 2100,
        "min_prestige": 2.5,
        "base_payments": {
            "signing_bonus": 1400,
            "appearance": 45,
            "points": 8,
            "podium": 95,
            "win": 190,
        },
        "goals": {
            "races_to_start": 4,
            "no_engine_failures": 2,
        },
        "goal_bonuses": {
            "races_completed": 400,
            "reliability_bonus": 600,
        },
        "events": ["engineering_demo", "technical_review"],
        "special_bonus": {"engine_reliability": 0.025},
    },
    
    "Brembo Brakes": {
        "industry": "auto_parts",
        "tier": "technical",
        "flavor": "The Italian brake specialist pushing stopping power",
        "personality": "performance_driven",
        "available_from": 1961,
        "available_until": 2100,
        "min_prestige": 4.0,
        "base_payments": {
            "signing_bonus": 1600,
            "appearance": 50,
            "points": 10,
            "podium": 110,
            "win": 220,
        },
        "goals": {
            "races_to_start": 4,
            "min_finish": 8,
        },
        "goal_bonuses": {
            "races_completed": 450,
            "finish_bonus": 600,
        },
        "events": ["brake_test", "technical_demo"],
    },

    # =========================================================================
    # CONSUMER GOODS
    # =========================================================================
    "Sunburst Sunglasses": {
        "industry": "consumer",
        "tier": "associate",
        "flavor": "The eyewear brand chasing the racing lifestyle",
        "personality": "trendy_youthful",
        "available_from": 1955,
        "available_until": 2100,
        "min_prestige": 1.0,
        "base_payments": {
            "signing_bonus": 500,
            "appearance": 20,
            "points": 3,
            "podium": 40,
            "win": 80,
        },
        "goals": {
            "races_to_start": 3,
        },
        "goal_bonuses": {
            "races_completed": 200,
        },
        "events": ["photoshoot", "brand_event"],
    },
    
    "Atlas Luggage": {
        "industry": "consumer",
        "tier": "associate",
        "flavor": "The travel goods company following the racing circuit",
        "personality": "practical_reliable",
        "available_from": 1950,
        "available_until": 2100,
        "min_prestige": 1.5,
        "base_payments": {
            "signing_bonus": 700,
            "appearance": 28,
            "points": 4,
            "podium": 55,
            "win": 110,
        },
        "goals": {
            "races_to_start": 4,
        },
        "goal_bonuses": {
            "races_completed": 280,
        },
        "events": ["travel_feature", "brand_event"],
    },
    
    "Velocita Coffee": {
        "industry": "consumer",
        "tier": "associate",
        "flavor": "The Italian coffee brand fueling racing passion",
        "personality": "passionate_italian",
        "available_from": 1947,
        "available_until": 2100,
        "min_prestige": 1.0,
        "base_payments": {
            "signing_bonus": 550,
            "appearance": 22,
            "points": 3,
            "podium": 45,
            "win": 90,
        },
        "goals": {
            "races_to_start": 3,
        },
        "goal_bonuses": {
            "races_completed": 220,
        },
        "events": ["coffee_morning", "brand_event"],
    },
}


# =============================================================================
# SPONSOR EVENTS - Random events triggered by sponsors
# =============================================================================
SPONSOR_EVENTS = {
    "driver_promo": {
        "name": "Driver Promotional Day",
        "description": "Your sponsor wants the driver for promotional activities",
        "options": [
            {
                "text": "Agree to the full day of promotion",
                "money": 150,
                "prestige": 0.2,
                "sponsor_happiness": 5,
                "fatigue": 1,  # Minor car prep penalty
            },
            {
                "text": "Negotiate a shorter session",
                "money": 80,
                "prestige": 0,
                "sponsor_happiness": 0,
                "fatigue": 0,
            },
            {
                "text": "Decline - focus on racing",
                "money": 0,
                "prestige": 0.3,
                "sponsor_happiness": -10,
                "fatigue": 0,
            },
        ],
    },
    
    "advert_shoot": {
        "name": "Advertising Campaign",
        "description": "Your sponsor wants to feature the car in a major campaign",
        "options": [
            {
                "text": "Full participation - star in the campaign",
                "money": 300,
                "prestige": 0.5,
                "sponsor_happiness": 10,
                "fatigue": 2,
            },
            {
                "text": "Limited involvement - just the car",
                "money": 150,
                "prestige": 0.1,
                "sponsor_happiness": 3,
                "fatigue": 1,
            },
            {
                "text": "Decline - you're racers, not models",
                "money": 0,
                "prestige": 0.4,
                "sponsor_happiness": -15,
                "fatigue": 0,
            },
        ],
    },
    
    "brand_controversy": {
        "name": "Industry Controversy",
        "description": "Your sponsor's industry is facing public criticism",
        "options": [
            {
                "text": "Stand by your sponsor publicly",
                "money": 200,
                "prestige": -0.5,
                "sponsor_happiness": 15,
                "fatigue": 0,
            },
            {
                "text": "Stay neutral - no comment",
                "money": 0,
                "prestige": 0,
                "sponsor_happiness": -5,
                "fatigue": 0,
            },
            {
                "text": "Distance yourself from the controversy",
                "money": -100,  # Penalty payment
                "prestige": 0.3,
                "sponsor_happiness": -20,
                "fatigue": 0,
            },
        ],
    },
    
    "vip_dinner": {
        "name": "VIP Dinner Event",
        "description": "Your sponsor is hosting an exclusive dinner",
        "options": [
            {
                "text": "Attend and charm the guests",
                "money": 100,
                "prestige": 0.4,
                "sponsor_happiness": 8,
                "fatigue": 0,
            },
            {
                "text": "Send apologies - racing comes first",
                "money": 0,
                "prestige": 0,
                "sponsor_happiness": -5,
                "fatigue": 0,
            },
        ],
    },
    
    "wine_tasting": {
        "name": "Wine Tasting Event",
        "description": "An exclusive tasting event with important clients",
        "options": [
            {
                "text": "Attend and network enthusiastically",
                "money": 120,
                "prestige": 0.3,
                "sponsor_happiness": 10,
                "fatigue": 0,
            },
            {
                "text": "Make a brief appearance",
                "money": 50,
                "prestige": 0.1,
                "sponsor_happiness": 3,
                "fatigue": 0,
            },
        ],
    },
    
    "charity_gala": {
        "name": "Charity Gala",
        "description": "Your sponsor is hosting a charity event",
        "options": [
            {
                "text": "Attend and auction racing memorabilia",
                "money": 80,
                "prestige": 0.6,
                "sponsor_happiness": 12,
                "fatigue": 0,
            },
            {
                "text": "Donate to the cause but skip the event",
                "money": -50,
                "prestige": 0.2,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
    
    "exclusive_party": {
        "name": "Exclusive Party",
        "description": "A glamorous party with celebrities and press",
        "options": [
            {
                "text": "Attend and enjoy the spotlight",
                "money": 150,
                "prestige": 0.5,
                "sponsor_happiness": 10,
                "fatigue": 1,
            },
            {
                "text": "Skip it - you have a race to prepare for",
                "money": 0,
                "prestige": -0.1,
                "sponsor_happiness": -8,
                "fatigue": 0,
            },
        ],
    },
    
    "fuel_test": {
        "name": "Fuel Testing Session",
        "description": "Your fuel sponsor wants data from a test session",
        "options": [
            {
                "text": "Provide full access and detailed feedback",
                "money": 100,
                "prestige": 0.1,
                "sponsor_happiness": 8,
                "fatigue": 1,
                "special": {"reliability_boost": 0.01},
            },
            {
                "text": "Limited data sharing",
                "money": 50,
                "prestige": 0,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
    
    "tyre_test": {
        "name": "Tyre Testing Day",
        "description": "Your tyre sponsor wants feedback on new compounds",
        "options": [
            {
                "text": "Full day of testing and detailed reports",
                "money": 80,
                "prestige": 0.1,
                "sponsor_happiness": 10,
                "fatigue": 2,
                "special": {"free_tyres": 2},
            },
            {
                "text": "Quick test run only",
                "money": 30,
                "prestige": 0,
                "sponsor_happiness": 3,
                "fatigue": 1,
                "special": {"free_tyres": 1},
            },
        ],
    },
    
    "tech_demo": {
        "name": "Technology Demonstration",
        "description": "Your sponsor wants to showcase their technology",
        "options": [
            {
                "text": "Host a full demonstration day",
                "money": 120,
                "prestige": 0.3,
                "sponsor_happiness": 8,
                "fatigue": 1,
            },
            {
                "text": "Brief press presentation only",
                "money": 60,
                "prestige": 0.1,
                "sponsor_happiness": 3,
                "fatigue": 0,
            },
        ],
    },
    
    "press_conference": {
        "name": "Press Conference",
        "description": "Your sponsor is organizing a major press event",
        "options": [
            {
                "text": "Full participation with Q&A",
                "money": 100,
                "prestige": 0.4,
                "sponsor_happiness": 8,
                "fatigue": 0,
            },
            {
                "text": "Prepared statement only",
                "money": 50,
                "prestige": 0.1,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
    
    "technical_demo": {
        "name": "Technical Showcase",
        "description": "Demonstrate the technical partnership to media",
        "options": [
            {
                "text": "Full garage access and driver interview",
                "money": 90,
                "prestige": 0.2,
                "sponsor_happiness": 7,
                "fatigue": 1,
            },
            {
                "text": "Static display only",
                "money": 40,
                "prestige": 0,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
    
    "hospitality": {
        "name": "Hospitality Event",
        "description": "Entertain sponsor guests at the track",
        "options": [
            {
                "text": "Full paddock tour and meet-and-greet",
                "money": 60,
                "prestige": 0.2,
                "sponsor_happiness": 6,
                "fatigue": 0,
            },
            {
                "text": "Quick photo opportunity",
                "money": 20,
                "prestige": 0,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
    
    "brand_event": {
        "name": "Brand Promotion",
        "description": "A standard promotional appearance",
        "options": [
            {
                "text": "Enthusiastic participation",
                "money": 50,
                "prestige": 0.1,
                "sponsor_happiness": 5,
                "fatigue": 0,
            },
            {
                "text": "Minimal effort appearance",
                "money": 20,
                "prestige": 0,
                "sponsor_happiness": 1,
                "fatigue": 0,
            },
        ],
    },
    
    "photoshoot": {
        "name": "Photoshoot",
        "description": "A promotional photoshoot with the car",
        "options": [
            {
                "text": "Full cooperation",
                "money": 70,
                "prestige": 0.2,
                "sponsor_happiness": 5,
                "fatigue": 1,
            },
            {
                "text": "Quick session",
                "money": 30,
                "prestige": 0,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
    
    "podium_celebration": {
        "name": "Podium Celebration",
        "trigger": "after_podium",  # Only triggers after a podium
        "description": "Your champagne sponsor wants a special celebration",
        "options": [
            {
                "text": "Celebrate in style with sponsor branding",
                "money": 200,
                "prestige": 0.4,
                "sponsor_happiness": 15,
                "fatigue": 0,
            },
        ],
    },
    
    "timing_partnership": {
        "name": "Official Timing Partner",
        "description": "Opportunity to become official timing partner",
        "options": [
            {
                "text": "Accept the timing partnership",
                "money": 150,
                "prestige": 0.3,
                "sponsor_happiness": 10,
                "fatigue": 0,
            },
            {
                "text": "Decline the additional commitment",
                "money": 0,
                "prestige": 0,
                "sponsor_happiness": -3,
                "fatigue": 0,
            },
        ],
    },
    
    "luxury_showcase": {
        "name": "Luxury Brand Showcase",
        "description": "Appear at a prestigious showcase event",
        "options": [
            {
                "text": "Attend in full racing attire",
                "money": 100,
                "prestige": 0.5,
                "sponsor_happiness": 8,
                "fatigue": 0,
            },
            {
                "text": "Send apologies",
                "money": 0,
                "prestige": -0.1,
                "sponsor_happiness": -5,
                "fatigue": 0,
            },
        ],
    },
    
    "fashion_photoshoot": {
        "name": "Fashion Magazine Feature",
        "description": "A high-end fashion magazine wants to feature the team",
        "options": [
            {
                "text": "Full cooperation - driver and car",
                "money": 250,
                "prestige": 0.7,
                "sponsor_happiness": 12,
                "fatigue": 2,
            },
            {
                "text": "Car only - driver is busy",
                "money": 100,
                "prestige": 0.2,
                "sponsor_happiness": 4,
                "fatigue": 1,
            },
        ],
    },
    
    "private_dinner": {
        "name": "Private Dinner with Executives",
        "description": "A private dinner with sponsor board members",
        "options": [
            {
                "text": "Attend and discuss the partnership",
                "money": 150,
                "prestige": 0.3,
                "sponsor_happiness": 10,
                "fatigue": 0,
            },
            {
                "text": "Politely decline",
                "money": 0,
                "prestige": 0,
                "sponsor_happiness": -5,
                "fatigue": 0,
            },
        ],
    },
    
    "elite_gathering": {
        "name": "Elite Social Gathering",
        "description": "An invitation to an exclusive social event",
        "options": [
            {
                "text": "Attend and represent the team",
                "money": 100,
                "prestige": 0.6,
                "sponsor_happiness": 8,
                "fatigue": 0,
            },
            {
                "text": "Too busy with racing",
                "money": 0,
                "prestige": 0,
                "sponsor_happiness": -3,
                "fatigue": 0,
            },
        ],
    },
    
    "philanthropy_event": {
        "name": "Philanthropic Initiative",
        "description": "Sponsor wants team involvement in charity work",
        "options": [
            {
                "text": "Full participation - visit hospitals etc.",
                "money": 50,
                "prestige": 0.8,
                "sponsor_happiness": 15,
                "fatigue": 1,
            },
            {
                "text": "Financial contribution only",
                "money": -30,
                "prestige": 0.3,
                "sponsor_happiness": 5,
                "fatigue": 0,
            },
        ],
    },
    
    "engineering_demo": {
        "name": "Engineering Demonstration",
        "description": "Showcase sponsor's engineering contribution",
        "options": [
            {
                "text": "Full technical walkthrough",
                "money": 80,
                "prestige": 0.2,
                "sponsor_happiness": 8,
                "fatigue": 1,
            },
            {
                "text": "Brief overview only",
                "money": 35,
                "prestige": 0,
                "sponsor_happiness": 3,
                "fatigue": 0,
            },
        ],
    },
    
    "radio_interview": {
        "name": "Radio Interview",
        "description": "Live radio interview about the sponsorship",
        "options": [
            {
                "text": "Enthusiastic interview",
                "money": 40,
                "prestige": 0.2,
                "sponsor_happiness": 6,
                "fatigue": 0,
            },
            {
                "text": "Brief statement only",
                "money": 15,
                "prestige": 0,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
    
    "coffee_morning": {
        "name": "Sponsor Coffee Morning",
        "description": "Informal meeting with sponsor representatives",
        "options": [
            {
                "text": "Attend and socialize",
                "money": 30,
                "prestige": 0.1,
                "sponsor_happiness": 5,
                "fatigue": 0,
            },
            {
                "text": "Skip it",
                "money": 0,
                "prestige": 0,
                "sponsor_happiness": -2,
                "fatigue": 0,
            },
        ],
    },
    
    "travel_feature": {
        "name": "Travel Feature Story",
        "description": "Feature about the team's travels with sponsor luggage",
        "options": [
            {
                "text": "Cooperate with the story",
                "money": 45,
                "prestige": 0.1,
                "sponsor_happiness": 5,
                "fatigue": 0,
            },
            {
                "text": "Decline the feature",
                "money": 0,
                "prestige": 0,
                "sponsor_happiness": -2,
                "fatigue": 0,
            },
        ],
    },
    
    "wind_tunnel_demo": {
        "name": "Wind Tunnel Demonstration",
        "description": "Showcase aerospace technology in action",
        "options": [
            {
                "text": "Full demonstration with press",
                "money": 120,
                "prestige": 0.3,
                "sponsor_happiness": 10,
                "fatigue": 2,
            },
            {
                "text": "Private session only",
                "money": 50,
                "prestige": 0.1,
                "sponsor_happiness": 4,
                "fatigue": 1,
            },
        ],
    },
    
    "research_presentation": {
        "name": "Research Presentation",
        "description": "Present research findings to sponsor executives",
        "options": [
            {
                "text": "Detailed technical presentation",
                "money": 100,
                "prestige": 0.2,
                "sponsor_happiness": 8,
                "fatigue": 1,
            },
            {
                "text": "Summary report only",
                "money": 40,
                "prestige": 0,
                "sponsor_happiness": 3,
                "fatigue": 0,
            },
        ],
    },
    
    "corporate_dinner": {
        "name": "Corporate Dinner",
        "description": "Formal dinner with sponsor corporate team",
        "options": [
            {
                "text": "Attend in full",
                "money": 80,
                "prestige": 0.2,
                "sponsor_happiness": 7,
                "fatigue": 0,
            },
            {
                "text": "Brief appearance only",
                "money": 30,
                "prestige": 0,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
    
    "brake_test": {
        "name": "Brake Testing Session",
        "description": "Test and provide feedback on new brake components",
        "options": [
            {
                "text": "Full testing day with reports",
                "money": 90,
                "prestige": 0.1,
                "sponsor_happiness": 10,
                "fatigue": 2,
            },
            {
                "text": "Quick assessment",
                "money": 35,
                "prestige": 0,
                "sponsor_happiness": 4,
                "fatigue": 1,
            },
        ],
    },
    
    "innovation_showcase": {
        "name": "Innovation Showcase",
        "description": "Present innovative technology to the media",
        "options": [
            {
                "text": "Host a full showcase event",
                "money": 130,
                "prestige": 0.4,
                "sponsor_happiness": 10,
                "fatigue": 1,
            },
            {
                "text": "Static display at the track",
                "money": 50,
                "prestige": 0.1,
                "sponsor_happiness": 4,
                "fatigue": 0,
            },
        ],
    },
    
    "air_show_appearance": {
        "name": "Air Show Appearance",
        "description": "Display car at sponsor's air show event",
        "options": [
            {
                "text": "Full display with demonstration",
                "money": 150,
                "prestige": 0.4,
                "sponsor_happiness": 12,
                "fatigue": 1,
            },
            {
                "text": "Static display only",
                "money": 60,
                "prestige": 0.1,
                "sponsor_happiness": 5,
                "fatigue": 0,
            },
        ],
    },
    
    "engineering_review": {
        "name": "Engineering Review Meeting",
        "description": "Technical review with sponsor engineers",
        "options": [
            {
                "text": "Detailed technical review",
                "money": 70,
                "prestige": 0.1,
                "sponsor_happiness": 8,
                "fatigue": 1,
            },
            {
                "text": "Summary discussion",
                "money": 30,
                "prestige": 0,
                "sponsor_happiness": 3,
                "fatigue": 0,
            },
        ],
    },
    
    "performance_review": {
        "name": "Performance Review",
        "description": "Review season performance with sponsor",
        "options": [
            {
                "text": "Thorough analysis presentation",
                "money": 60,
                "prestige": 0.1,
                "sponsor_happiness": 7,
                "fatigue": 0,
            },
            {
                "text": "Brief summary",
                "money": 25,
                "prestige": 0,
                "sponsor_happiness": 2,
                "fatigue": 0,
            },
        ],
    },
}


def get_available_sponsors(year, prestige, current_sponsors=None):
    """
    Get list of sponsors that could approach the team.
    Excludes current sponsors and respects year/prestige requirements.
    """
    if current_sponsors is None:
        current_sponsors = []
    
    current_names = {s.get("name") for s in current_sponsors}
    available = []
    
    for name, info in SPONSORS.items():
        # Skip current sponsors
        if name in current_names:
            continue
            
        # Check availability period
        if year < info.get("available_from", 1900):
            continue
        if year > info.get("available_until", 2100):
            continue
            
        # Check prestige requirement
        if prestige < info.get("min_prestige", 0):
            continue
            
        # Check if we already have a sponsor of this tier (for title)
        tier = info.get("tier", "associate")
        if tier == "title":
            if any(SPONSORS.get(s.get("name"), {}).get("tier") == "title" for s in current_sponsors):
                continue
        
        available.append((name, info))
    
    return available


def get_sponsor_by_tier(available_sponsors, tier):
    """Filter available sponsors by tier."""
    return [(name, info) for name, info in available_sponsors if info.get("tier") == tier]
