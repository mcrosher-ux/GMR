# gmr/world_economy.py
# World economy simulation - countries, economic events, and attendance calculation

import random

# =============================================================================
# COUNTRY DATA
# =============================================================================

COUNTRIES = {
    "Italy": {
        "name": "Italy",
        "region": "Southern Europe",
        "base_economy": 6,  # 1-10 scale
        "population_millions": 47,
        "motorsport_culture": 9,  # How much they love racing (1-10)
        "wealth_distribution": 0.6,  # 0-1, higher = more people can afford tickets
        "political_stability": 5,  # 1-10, affects economic swings
        "industrial_strength": 7,  # Affects constructor presence
        "flavor": "The spiritual home of motorsport passion. The tifosi live and breathe racing.",
    },
    "UK": {
        "name": "United Kingdom",
        "region": "Northern Europe",
        "base_economy": 7,
        "population_millions": 50,
        "motorsport_culture": 8,
        "wealth_distribution": 0.65,
        "political_stability": 8,
        "industrial_strength": 8,
        "flavor": "A nation of engineering excellence and gentleman racers.",
    },
    "France": {
        "name": "France",
        "region": "Western Europe",
        "base_economy": 6,
        "population_millions": 42,
        "motorsport_culture": 7,
        "wealth_distribution": 0.55,
        "political_stability": 5,
        "industrial_strength": 6,
        "flavor": "Wine, cheese, and the roar of engines on country roads.",
    },
    "Germany": {
        "name": "Germany",
        "region": "Central Europe",
        "base_economy": 5,  # Still recovering post-war in 1950s
        "population_millions": 68,
        "motorsport_culture": 8,
        "wealth_distribution": 0.5,
        "political_stability": 6,
        "industrial_strength": 7,
        "flavor": "Precision engineering rises from the ashes. The Silver Arrows will return.",
    },
    "USA": {
        "name": "United States",
        "region": "North America",
        "base_economy": 9,
        "population_millions": 150,
        "motorsport_culture": 7,
        "wealth_distribution": 0.7,
        "political_stability": 9,
        "industrial_strength": 10,
        "flavor": "The land of opportunity, where speed equals freedom and ovals dominate.",
    },
    "Spain": {
        "name": "Spain",
        "region": "Southern Europe",
        "base_economy": 4,
        "population_millions": 28,
        "motorsport_culture": 6,
        "wealth_distribution": 0.4,
        "political_stability": 4,
        "industrial_strength": 4,
        "flavor": "A proud nation where passion burns hot and budgets run thin.",
    },
    "Belgium": {
        "name": "Belgium",
        "region": "Western Europe",
        "base_economy": 6,
        "population_millions": 9,
        "motorsport_culture": 7,
        "wealth_distribution": 0.6,
        "political_stability": 7,
        "industrial_strength": 6,
        "flavor": "Small but mighty. The Ardennes have witnessed legends born.",
    },
    "Switzerland": {
        "name": "Switzerland",
        "region": "Central Europe",
        "base_economy": 8,
        "population_millions": 5,
        "motorsport_culture": 5,
        "wealth_distribution": 0.8,
        "political_stability": 10,
        "industrial_strength": 6,
        "flavor": "Neutral, wealthy, precise. Racing here is about perfection.",
    },
    "Monaco": {
        "name": "Monaco",
        "region": "Southern Europe",
        "base_economy": 10,
        "population_millions": 0.02,
        "motorsport_culture": 8,
        "wealth_distribution": 0.95,
        "political_stability": 9,
        "industrial_strength": 1,
        "flavor": "The playground of the rich. Every race is a party for the elite.",
    },
    "Argentina": {
        "name": "Argentina",
        "region": "South America",
        "base_economy": 5,
        "population_millions": 17,
        "motorsport_culture": 8,
        "wealth_distribution": 0.45,
        "political_stability": 4,
        "industrial_strength": 4,
        "flavor": "Fangio's homeland. Racing is religion here.",
    },
    "Brazil": {
        "name": "Brazil",
        "region": "South America",
        "base_economy": 4,
        "population_millions": 52,
        "motorsport_culture": 7,
        "wealth_distribution": 0.35,
        "political_stability": 5,
        "industrial_strength": 3,
        "flavor": "Emerging giant with a passion for speed and samba.",
    },
    "Poland": {
        "name": "Poland",
        "region": "Eastern Europe",
        "base_economy": 3,
        "population_millions": 25,
        "motorsport_culture": 4,
        "wealth_distribution": 0.3,
        "political_stability": 3,
        "industrial_strength": 4,
        "flavor": "Behind the iron curtain, but dreams of racing persist.",
    },
    "Japan": {
        "name": "Japan",
        "region": "Asia",
        "base_economy": 4,  # Still rebuilding in 1950s
        "population_millions": 84,
        "motorsport_culture": 6,
        "wealth_distribution": 0.4,
        "political_stability": 7,
        "industrial_strength": 5,
        "flavor": "Rising from ruin. The future of motorsport is being forged here.",
    },
    "Australia": {
        "name": "Australia",
        "region": "Oceania",
        "base_economy": 7,
        "population_millions": 8,
        "motorsport_culture": 6,
        "wealth_distribution": 0.7,
        "political_stability": 9,
        "industrial_strength": 4,
        "flavor": "Far from Europe but close to the spirit of racing.",
    },
}


# =============================================================================
# ECONOMIC EVENTS
# =============================================================================

REGIONAL_EVENTS = {
    "Southern Europe": [
        {
            "name": "Tourism Boom",
            "description": "Post-war recovery brings tourists flooding back to the Mediterranean",
            "economy_modifier": 1.3,
            "attendance_modifier": 1.4,
            "duration_weeks": 12,
            "chance": 0.02,
        },
        {
            "name": "Political Unrest",
            "description": "Strikes and protests disrupt daily life",
            "economy_modifier": 0.7,
            "attendance_modifier": 0.6,
            "duration_weeks": 8,
            "chance": 0.03,
        },
        {
            "name": "Harvest Festival",
            "description": "Wine harvest brings celebration and spending",
            "economy_modifier": 1.1,
            "attendance_modifier": 1.25,
            "duration_weeks": 4,
            "chance": 0.04,
        },
        {
            "name": "Heatwave",
            "description": "Scorching temperatures keep people at home",
            "economy_modifier": 0.95,
            "attendance_modifier": 0.8,
            "duration_weeks": 3,
            "chance": 0.05,
        },
    ],
    "Northern Europe": [
        {
            "name": "Industrial Expansion",
            "description": "Factories are booming, workers have money to spend",
            "economy_modifier": 1.25,
            "attendance_modifier": 1.2,
            "duration_weeks": 16,
            "chance": 0.02,
        },
        {
            "name": "Coal Shortage",
            "description": "Energy crisis grips the nation",
            "economy_modifier": 0.75,
            "attendance_modifier": 0.85,
            "duration_weeks": 8,
            "chance": 0.03,
        },
        {
            "name": "Royal Event",
            "description": "A royal occasion boosts national morale",
            "economy_modifier": 1.05,
            "attendance_modifier": 1.35,
            "duration_weeks": 2,
            "chance": 0.02,
        },
        {
            "name": "Dock Strike",
            "description": "Port workers strike, disrupting trade",
            "economy_modifier": 0.85,
            "attendance_modifier": 0.9,
            "duration_weeks": 4,
            "chance": 0.03,
        },
    ],
    "Western Europe": [
        {
            "name": "Marshall Plan Investment",
            "description": "American aid flows into rebuilding efforts",
            "economy_modifier": 1.35,
            "attendance_modifier": 1.15,
            "duration_weeks": 20,
            "chance": 0.015,
        },
        {
            "name": "Currency Crisis",
            "description": "Inflation erodes purchasing power",
            "economy_modifier": 0.65,
            "attendance_modifier": 0.75,
            "duration_weeks": 10,
            "chance": 0.025,
        },
        {
            "name": "Wine Glut",
            "description": "Excellent harvest means cheap wine and happy farmers",
            "economy_modifier": 1.1,
            "attendance_modifier": 1.2,
            "duration_weeks": 6,
            "chance": 0.03,
        },
    ],
    "Central Europe": [
        {
            "name": "Economic Miracle",
            "description": "Rapid industrial recovery astounds the world",
            "economy_modifier": 1.4,
            "attendance_modifier": 1.25,
            "duration_weeks": 24,
            "chance": 0.01,
        },
        {
            "name": "Refugee Crisis",
            "description": "Displaced populations strain resources",
            "economy_modifier": 0.8,
            "attendance_modifier": 0.7,
            "duration_weeks": 12,
            "chance": 0.02,
        },
        {
            "name": "Trade Fair",
            "description": "International trade fair brings business and visitors",
            "economy_modifier": 1.15,
            "attendance_modifier": 1.3,
            "duration_weeks": 3,
            "chance": 0.03,
        },
    ],
    "North America": [
        {
            "name": "Post-War Prosperity",
            "description": "The American dream is in full swing",
            "economy_modifier": 1.2,
            "attendance_modifier": 1.3,
            "duration_weeks": 20,
            "chance": 0.02,
        },
        {
            "name": "Steel Strike",
            "description": "Major industrial action hits the heartland",
            "economy_modifier": 0.85,
            "attendance_modifier": 0.9,
            "duration_weeks": 6,
            "chance": 0.025,
        },
        {
            "name": "State Fair Season",
            "description": "Summer fairs draw crowds and spending",
            "economy_modifier": 1.05,
            "attendance_modifier": 1.4,
            "duration_weeks": 8,
            "chance": 0.04,
        },
        {
            "name": "Baseball Finals",
            "description": "National attention shifts to America's pastime",
            "economy_modifier": 1.0,
            "attendance_modifier": 0.75,  # Competing for attention
            "duration_weeks": 3,
            "chance": 0.03,
        },
    ],
    "South America": [
        {
            "name": "Commodity Boom",
            "description": "Coffee and beef prices soar, money flows",
            "economy_modifier": 1.35,
            "attendance_modifier": 1.3,
            "duration_weeks": 16,
            "chance": 0.02,
        },
        {
            "name": "Military Coup",
            "description": "Political instability rattles the region",
            "economy_modifier": 0.6,
            "attendance_modifier": 0.5,
            "duration_weeks": 8,
            "chance": 0.04,
        },
        {
            "name": "Carnival Season",
            "description": "Festival fever grips the nation",
            "economy_modifier": 1.0,
            "attendance_modifier": 1.5,
            "duration_weeks": 2,
            "chance": 0.03,
        },
        {
            "name": "Drought",
            "description": "Agricultural disaster hits rural areas",
            "economy_modifier": 0.75,
            "attendance_modifier": 0.85,
            "duration_weeks": 12,
            "chance": 0.03,
        },
    ],
    "Eastern Europe": [
        {
            "name": "Five-Year Plan Success",
            "description": "Industrial quotas met, workers rewarded",
            "economy_modifier": 1.15,
            "attendance_modifier": 1.1,
            "duration_weeks": 8,
            "chance": 0.02,
        },
        {
            "name": "State Crackdown",
            "description": "Political repression dampens public life",
            "economy_modifier": 0.85,
            "attendance_modifier": 0.6,
            "duration_weeks": 6,
            "chance": 0.04,
        },
        {
            "name": "International Sports Event",
            "description": "State-sponsored athletics bring crowds",
            "economy_modifier": 1.0,
            "attendance_modifier": 1.3,
            "duration_weeks": 2,
            "chance": 0.03,
        },
    ],
    "Asia": [
        {
            "name": "Manufacturing Surge",
            "description": "Factories spring up across the landscape",
            "economy_modifier": 1.3,
            "attendance_modifier": 1.1,
            "duration_weeks": 20,
            "chance": 0.015,
        },
        {
            "name": "Natural Disaster",
            "description": "Typhoon or earthquake devastates the region",
            "economy_modifier": 0.6,
            "attendance_modifier": 0.4,
            "duration_weeks": 8,
            "chance": 0.03,
        },
        {
            "name": "Cultural Festival",
            "description": "Traditional celebrations bring communities together",
            "economy_modifier": 1.05,
            "attendance_modifier": 1.25,
            "duration_weeks": 2,
            "chance": 0.04,
        },
    ],
    "Oceania": [
        {
            "name": "Mining Boom",
            "description": "Gold and mineral wealth flows",
            "economy_modifier": 1.25,
            "attendance_modifier": 1.15,
            "duration_weeks": 16,
            "chance": 0.02,
        },
        {
            "name": "Bushfire Season",
            "description": "Fires rage across the outback",
            "economy_modifier": 0.85,
            "attendance_modifier": 0.7,
            "duration_weeks": 6,
            "chance": 0.04,
        },
        {
            "name": "Immigration Wave",
            "description": "New arrivals boost population and spending",
            "economy_modifier": 1.15,
            "attendance_modifier": 1.2,
            "duration_weeks": 12,
            "chance": 0.025,
        },
    ],
}

# Global events that affect everyone
GLOBAL_EVENTS = [
    {
        "name": "Oil Price Spike",
        "description": "Global oil prices surge, affecting transport costs",
        "economy_modifier": 0.85,
        "attendance_modifier": 0.9,
        "duration_weeks": 8,
        "chance": 0.01,
    },
    {
        "name": "International Peace Summit",
        "description": "Hope for lasting peace boosts global optimism",
        "economy_modifier": 1.1,
        "attendance_modifier": 1.15,
        "duration_weeks": 4,
        "chance": 0.01,
    },
    {
        "name": "Global Recession Fear",
        "description": "Economic uncertainty grips world markets",
        "economy_modifier": 0.75,
        "attendance_modifier": 0.8,
        "duration_weeks": 12,
        "chance": 0.008,
    },
    {
        "name": "Motorsport Golden Age",
        "description": "Racing fever sweeps the globe",
        "economy_modifier": 1.0,
        "attendance_modifier": 1.4,
        "duration_weeks": 16,
        "chance": 0.005,
    },
]


# =============================================================================
# WORLD STATE CLASS
# =============================================================================

class WorldEconomy:
    """
    Tracks the global and regional economic state of the world.
    """
    
    def __init__(self):
        # Current economy levels for each country (can drift from base)
        self.country_economies = {
            name: data["base_economy"] 
            for name, data in COUNTRIES.items()
        }
        
        # Active events: list of {event, country/region, weeks_remaining}
        self.active_events = []
        
        # Historical attendance records for prestige calculation
        self.attendance_history = {}  # track_name -> [attendance values]
        
        # News/event log
        self.event_log = []
    
    def get_country(self, country_name):
        """Get country data by name."""
        return COUNTRIES.get(country_name)
    
    def get_current_economy(self, country_name):
        """Get current economy level for a country (affected by events)."""
        base = self.country_economies.get(country_name, 5)
        
        # Apply active event modifiers
        modifier = 1.0
        country_data = COUNTRIES.get(country_name, {})
        region = country_data.get("region", "")
        
        for event_data in self.active_events:
            event = event_data["event"]
            scope = event_data["scope"]
            
            if scope == "global" or scope == region or scope == country_name:
                modifier *= event.get("economy_modifier", 1.0)
        
        return min(10, max(1, base * modifier))
    
    def get_attendance_modifier(self, country_name):
        """Get current attendance modifier for a country (affected by events)."""
        modifier = 1.0
        country_data = COUNTRIES.get(country_name, {})
        region = country_data.get("region", "")
        
        for event_data in self.active_events:
            event = event_data["event"]
            scope = event_data["scope"]
            
            if scope == "global" or scope == region or scope == country_name:
                modifier *= event.get("attendance_modifier", 1.0)
        
        return modifier
    
    def tick_week(self):
        """
        Advance the world economy by one week.
        - Decay/expire active events
        - Potentially trigger new events
        - Drift country economies slightly
        """
        news = []
        
        # Decay active events
        expired = []
        for event_data in self.active_events:
            event_data["weeks_remaining"] -= 1
            if event_data["weeks_remaining"] <= 0:
                expired.append(event_data)
                news.append(f"WORLD: {event_data['event']['name']} has ended in {event_data['scope']}.")
        
        for e in expired:
            self.active_events.remove(e)
        
        # Check for new global events
        for event in GLOBAL_EVENTS:
            if random.random() < event["chance"]:
                self.active_events.append({
                    "event": event,
                    "scope": "global",
                    "weeks_remaining": event["duration_weeks"],
                })
                news.append(f"WORLD NEWS: {event['name']} — {event['description']}")
                self.event_log.append(event["name"])
        
        # Check for new regional events
        for region, events in REGIONAL_EVENTS.items():
            for event in events:
                if random.random() < event["chance"]:
                    # Check if similar event already active in this region
                    already_active = any(
                        e["scope"] == region and e["event"]["name"] == event["name"]
                        for e in self.active_events
                    )
                    if not already_active:
                        self.active_events.append({
                            "event": event,
                            "scope": region,
                            "weeks_remaining": event["duration_weeks"],
                        })
                        news.append(f"REGIONAL NEWS ({region}): {event['name']} — {event['description']}")
                        self.event_log.append(event["name"])
        
        # Small random drift in country economies (±0.1)
        for country in self.country_economies:
            drift = random.uniform(-0.1, 0.1)
            country_data = COUNTRIES.get(country, {})
            stability = country_data.get("political_stability", 5)
            
            # More stable countries drift less
            drift *= (11 - stability) / 10.0
            
            base = COUNTRIES.get(country, {}).get("base_economy", 5)
            current = self.country_economies[country]
            
            # Tendency to revert to base
            reversion = (base - current) * 0.05
            
            self.country_economies[country] = min(10, max(1, current + drift + reversion))
        
        return news
    
    def calculate_attendance(self, track_name, track_data, player_prestige, event_prestige):
        """
        Calculate race attendance based on multiple factors.
        
        Returns: (attendance, attendance_details)
        """
        country_name = track_data.get("country", "Italy")
        country_data = COUNTRIES.get(country_name, {})
        
        # Base attendance from track data
        base_attendance = track_data.get("appearance_base", 50) * 1000
        prestige_mult = track_data.get("appearance_prestige_mult", 15)
        
        # Country factors
        population = country_data.get("population_millions", 20)
        motorsport_culture = country_data.get("motorsport_culture", 5)
        wealth = country_data.get("wealth_distribution", 0.5)
        
        # Current economy
        economy = self.get_current_economy(country_name)
        economy_factor = economy / 5.0  # Normalized around 1.0
        
        # Event modifiers (regional/global events)
        event_modifier = self.get_attendance_modifier(country_name)
        
        # Prestige factors
        combined_prestige = (player_prestige * 0.4 + event_prestige * 0.6)
        prestige_bonus = combined_prestige * prestige_mult * 1000
        
        # Motorsport culture bonus
        culture_factor = motorsport_culture / 5.0
        
        # Wealth factor (can people afford tickets?)
        wealth_factor = 0.5 + wealth * 0.5
        
        # Population factor (more people = potentially bigger crowds)
        # Logarithmic so huge populations don't dominate
        import math
        pop_factor = math.log10(population + 1) / 2.0
        
        # Calculate final attendance
        attendance = base_attendance
        attendance += prestige_bonus
        attendance *= economy_factor
        attendance *= event_modifier
        attendance *= culture_factor
        attendance *= wealth_factor
        attendance *= pop_factor
        
        # Random variance (±15%)
        variance = random.uniform(0.85, 1.15)
        attendance *= variance
        
        # Ensure reasonable bounds
        attendance = max(5000, min(500000, int(attendance)))
        
        # Build details for news/display
        details = {
            "base": base_attendance,
            "prestige_bonus": int(prestige_bonus),
            "economy_factor": economy_factor,
            "event_modifier": event_modifier,
            "culture_factor": culture_factor,
            "wealth_factor": wealth_factor,
            "pop_factor": pop_factor,
            "final": attendance,
            "country": country_name,
            "active_events": [e["event"]["name"] for e in self.active_events 
                           if e["scope"] == "global" or e["scope"] == country_data.get("region", "")],
        }
        
        # Store in history
        if track_name not in self.attendance_history:
            self.attendance_history[track_name] = []
        self.attendance_history[track_name].append(attendance)
        
        return attendance, details
    
    def get_fame_modifier_from_attendance(self, attendance):
        """
        Calculate fame gain/loss modifier based on attendance.
        Bigger crowds = more exposure = more fame change (good or bad).
        """
        # Baseline is 50,000 attendance
        baseline = 50000
        
        # Logarithmic scaling so huge crowds don't give infinite fame
        import math
        if attendance <= 0:
            return 0.5
        
        ratio = attendance / baseline
        modifier = 0.5 + (math.log10(ratio + 0.1) + 1) * 0.5
        
        return max(0.3, min(2.5, modifier))
    
    def format_attendance_news(self, track_name, attendance, details):
        """Generate news text about attendance."""
        if attendance >= 200000:
            size_desc = "A record-breaking crowd"
        elif attendance >= 100000:
            size_desc = "Massive crowds"
        elif attendance >= 50000:
            size_desc = "Strong attendance"
        elif attendance >= 25000:
            size_desc = "Moderate crowds"
        elif attendance >= 10000:
            size_desc = "Sparse attendance"
        else:
            size_desc = "A disappointing turnout"
        
        news = f"{size_desc} of {attendance:,} spectators gathered at {track_name}."
        
        # Add event context if relevant
        if details.get("active_events"):
            events_str = ", ".join(details["active_events"][:2])
            if details["event_modifier"] > 1.1:
                news += f" Regional events ({events_str}) boosted attendance."
            elif details["event_modifier"] < 0.9:
                news += f" Regional issues ({events_str}) dampened attendance."
        
        return news
    
    def get_active_events_summary(self):
        """Get a summary of all active events for UI display."""
        if not self.active_events:
            return "The world is quiet — no major events affecting the racing calendar."
        
        summaries = []
        for event_data in self.active_events:
            event = event_data["event"]
            scope = event_data["scope"]
            weeks = event_data["weeks_remaining"]
            summaries.append(f"• {event['name']} ({scope}) — {weeks} weeks remaining")
        
        return "\n".join(summaries)
    
    def get_country_report(self, country_name):
        """Get a detailed report on a country's current state."""
        country = COUNTRIES.get(country_name)
        if not country:
            return f"Unknown country: {country_name}"
        
        economy = self.get_current_economy(country_name)
        attendance_mod = self.get_attendance_modifier(country_name)
        
        report = []
        report.append(f"=== {country['name']} ===")
        report.append(f"Region: {country['region']}")
        report.append(f"Population: {country['population_millions']}M")
        report.append(f"")
        report.append(f"Economy: {'★' * int(economy)} ({economy:.1f}/10)")
        report.append(f"Motorsport Culture: {'★' * country['motorsport_culture']} ({country['motorsport_culture']}/10)")
        report.append(f"Political Stability: {'★' * country['political_stability']} ({country['political_stability']}/10)")
        report.append(f"")
        report.append(f"Current attendance modifier: {attendance_mod:.0%}")
        report.append(f"")
        report.append(country['flavor'])
        
        # Active events affecting this country
        region = country["region"]
        affecting_events = [
            e for e in self.active_events 
            if e["scope"] == "global" or e["scope"] == region or e["scope"] == country_name
        ]
        
        if affecting_events:
            report.append(f"")
            report.append("Active Events:")
            for e in affecting_events:
                report.append(f"  • {e['event']['name']} ({e['weeks_remaining']} weeks)")
        
        return "\n".join(report)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_driver_home_country(driver):
    """Get a driver's home country."""
    return driver.get("country", "Italy")


def is_home_race(driver, track_data):
    """Check if this is a home race for the driver."""
    driver_country = get_driver_home_country(driver)
    track_country = track_data.get("country", "")
    return driver_country == track_country


def get_home_crowd_bonus(driver, track_data):
    """
    Get attendance/fame bonus for a driver racing at home.
    Home heroes draw bigger crowds.
    """
    if is_home_race(driver, track_data):
        fame = driver.get("fame", 0)
        # More famous drivers get bigger home bonuses
        return 1.0 + (fame * 0.05)  # Up to 1.25x for fame 5
    return 1.0


def calculate_prestige_change(finish_position, attendance, dnf=False):
    """
    Calculate prestige change based on result and attendance.
    More people watching = more prestige gained/lost.
    """
    # Base prestige from position
    if dnf:
        base_prestige = -0.5
    elif finish_position == 1:
        base_prestige = 3.0
    elif finish_position == 2:
        base_prestige = 2.0
    elif finish_position == 3:
        base_prestige = 1.5
    elif finish_position <= 5:
        base_prestige = 1.0
    elif finish_position <= 10:
        base_prestige = 0.5
    elif finish_position <= 15:
        base_prestige = 0.2
    else:
        base_prestige = 0.0
    
    # Attendance modifier
    import math
    attendance_factor = math.log10(attendance / 10000 + 1) * 0.5 + 0.5
    attendance_factor = max(0.5, min(2.0, attendance_factor))
    
    return base_prestige * attendance_factor


# Global instance for the game to use
world_economy = WorldEconomy()
