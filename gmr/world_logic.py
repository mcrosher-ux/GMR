# gmr/world_logic.py
import random
from gmr.data import drivers, constructors


DRIVER_FIRST_NAMES = [
    "Carlo", "Alberto", "Emmanuel", "George", "Hans", "Luis",
    "Marco", "Antonio", "Paolo", "Giancarlo", "Franco", "Sergio",
    "Jean", "Pierre", "Henri", "Jacques", "Michel", "Claude",
    "Wolfgang", "Helmut", "Klaus", "Dieter", "Rolf", "Horst",
    "Mario", "Giuseppe", "Vittorio", "Enrico", "Umberto",
    "Pedro", "Miguel", "Diego", "Juan", "Carlos", "Fernando",
    "Dennis", "Peter", "Colin", "John", "Graham", "Ian",
]

DRIVER_LAST_NAMES = [
    "Bianci", "Rossi", "Dubois", "McCallister", "Keller", "Navarro",
    "Ferrari", "Bianchi", "Ricci", "Rossi", "Verdi", "Neri",
    "Dupont", "Bernard", "Martin", "Laurent", "Leclerc", "Arnoux",
    "Mueller", "Schmidt", "Weber", "Hoffmann", "Fischer", "Richter",
    "Esposito", "Gallo", "Colombo", "Romano",
    "Garcia", "Lopez", "Martinez", "Ramirez", "Fernandez",
    "Hill", "Watson", "Senna", "Villeneuve", "Hunt", "Stewart",
]

ENZONI = "Enzoni"
VALDIERI = "Scuderia Valdieri"


def generate_random_driver_name():
    """Generate a random driver name from name pools."""
    first = random.choice(DRIVER_FIRST_NAMES)
    last = random.choice(DRIVER_LAST_NAMES)
    return f"{first} {last}"


# Debug toggle: if True, allow test drivers / simplify event entry rules
TEST_DRIVERS_ENABLED = False


def initialise_driver_age_profiles():
    """
    For each driver, roll hidden peak/decline ages so every save file
    has different career curves.

    We only store 'age' in the data.
    Here we add:
      - peak_age: where they're roughly at their best
      - decline_age: where decline starts
    These are *not* shown in the UI.
    """
    for d in drivers:
        # Make sure they at least have an age
        age = d.get("age", 38)
        d["age"] = age

        # Bias rules:
        # - Older drivers: peak right now or very soon, decline quickly.
        # - Mid-30s: peak over the next couple of years.
        # - Under 32: peak a bit later.
        if age >= 40:
            peak_min = max(age - 1, 32)
            peak_max = age
        elif age <= 32:
            peak_min = age + 1
            peak_max = age + 4
        else:
            peak_min = age
            peak_max = age + 2

        # Roll peak age
        peak_age = random.randint(peak_min, peak_max)

        # Decline starts 3–7 years after peak (random per save)
        decline_age = peak_age + random.randint(3, 7)

        d["peak_age"] = peak_age
        d["decline_age"] = decline_age

def calculate_car_speed(engine, chassis):
    if engine is None or chassis is None:
        return 0
    lightness = 11 - chassis["weight"]
    engine_component = engine["speed"] * 0.7 + engine["acceleration"] * 0.3
    chassis_component = chassis["aero"] * 0.7 + lightness * 0.3
    car_speed = engine_component * 0.6 + chassis_component * 0.4
    return round(car_speed, 1)

def get_car_speed_for_track(state, track_profile):
    """
    Calculate the player's car 'speed number' for a specific track,
    blending engine speed vs acceleration differently depending on
    how flat-out vs technical the circuit is.
    """
    engine = state.current_engine
    chassis = state.current_chassis

    if engine is None or chassis is None:
        # Fall back to whatever we already calculated
        return state.car_speed

    # Use existing track character: pace vs consistency
    pace_w = track_profile.get("pace_weight", 1.0)
    cons_w = track_profile.get("consistency_weight", 1.0)

    # Default blend: slightly biased to top speed
    top_speed_weight = 0.7
    accel_weight = 0.3

    # Very high-pace circuit: flat-out speed matters more
    if pace_w >= cons_w * 1.15:
        top_speed_weight = 0.8
        accel_weight = 0.2

    # Very consistency-biased circuit: more stop–start, acceleration matters a bit more
    elif cons_w >= pace_w * 1.15:
        top_speed_weight = 0.55
        accel_weight = 0.45

    # Engine contribution, now track-sensitive
    engine_component = (
        engine["speed"] * top_speed_weight +
        engine["acceleration"] * accel_weight
    )

    # Chassis contribution as before
    lightness = 11 - chassis["weight"]
    chassis_component = chassis["aero"] * 0.7 + lightness * 0.3

    car_speed = engine_component * 0.6 + chassis_component * 0.4

    # Apply temporary bonuses from weekly events
    if hasattr(state, 'temp_performance_bonus') and state.temp_performance_bonus != 0:
        car_speed += state.temp_performance_bonus
        # Clear the bonus after use
        state.temp_performance_bonus = 0

    # Apply weather preparation bonuses
    if hasattr(state, 'weather_preparation'):
        # Check current weather conditions (simplified - we'd need to pass this in)
        # For now, just give a small bonus for any preparation
        car_speed += 0.2
        # Clear preparation after use
        delattr(state, 'weather_preparation')

    return round(car_speed, 1)

def driver_enters_event(driver, race_name, track_profile, state=None, time=None):
    """
    Decide if a driver enters an event.

    Patch C: Enzoni only do Italian races + Vallone + Ardennes (demo logic).
    Patch F: 'Test' drivers are debug-only and do not enter real races unless enabled.
    Patch G: Gentleman drivers have selective entries (big races + random medium ones).
    """
    from gmr.calendar import BIG_RACES, MEDIUM_RACES

    ctor = driver.get("constructor")

    # Patch F: test archetypes are for dev only
    if ctor == "Test":
        return TEST_DRIVERS_ENABLED

    # Check appears_from_year for drivers who enter later
    appears_from = driver.get("appears_from_year")
    if appears_from and time:
        if time.year < appears_from:
            return False

    # Gentleman drivers with selective entries (e.g., Prince Sagat)
    if driver.get("selective_entries") and driver.get("gentleman_driver"):
        # Always appear at big races
        if race_name in BIG_RACES:
            return True
        
        # 40% chance to appear at medium races (the prince is choosy)
        if race_name in MEDIUM_RACES:
            # Use driver name + race for deterministic but varied entries
            seed = hash((driver.get("name", ""), race_name, time.year if time else 0))
            rng = random.Random(seed)
            return rng.random() < 0.4
        
        # Skip small races - beneath royalty
        return False

    # Allow player driver if transport paid
    if state and driver == state.player_driver and race_name in getattr(state, 'transport_paid_races', set()):
        return True

    # Nationality restrictions
    allowed_nats = track_profile.get("allowed_nationalities")
    if allowed_nats:
        driver_nat = driver.get("country", "UK")
        if driver_nat not in allowed_nats:
            return False

    # Valdieri schedule rules (demo)
    if ctor == "Scuderia Valdieri":
        allowed_races = {
            "Vallone GP",
            "Little Autodromo",
            "Ardennes Endurance GP",
            "Château-des-Prés GP",
            "Marblethorpe GP",
        }

        if race_name in allowed_races:
            return True

        # Optional: allow Italian races generally (same vibe as Enzoni)
        country = track_profile.get("country", "")
        if country == "Italy":
            return True

        return False



    # Special rule for Union Speedway: only famous/well-backed internationals can afford the trip
    if race_name == "Union Speedway":
        driver_nat = driver.get("country", "UK")
        if driver_nat != "USA":
            fame = driver.get("fame", 0)
            # Only enter if fame 2+ (well-known) or backed by major teams
            if fame < 2 and ctor == "Independent":
                return False

    # Everyone else: always enters for now (subject to Enzoni rules below)
    if ctor != "Enzoni":
        return True

    # Enzoni schedule rules (demo)
    allowed_races = {
        "Vallone GP",
        "Little Autodromo",
        "Ardennes Endurance GP",
    }

    if race_name in allowed_races:
        return True

    # Optional: allow ANY Italian event if you add more Italy tracks later
    country = track_profile.get("country", "")
    if country == "Italy":
        return True

    return False

def can_team_sign_driver(state, driver):
    """
    Check whether your team has enough prestige to realistically
    sign this driver based on their fame.

    For now:
      - Fame 0–1  -> basically anyone will talk to you
      - Fame 2    -> want prestige ~5+
      - Fame 3    -> want prestige ~7.5+
      - Fame 4    -> want prestige ~10+
      - etc.

    Returns (can_sign: bool, required_prestige: float)
    """
    fame = driver.get("fame", 0)
    prestige = getattr(state, "prestige", 0.0)

    # Updated formula: prestige must be at least fame * 2.5
    required_prestige = float(fame) * 2.5

    return prestige >= required_prestige, required_prestige


def get_regen_age_for_year(year: int) -> int:
    """
    Era-based age brackets for new/regen drivers.

    1947–1950: mostly older gentlemen / veterans
    Early 50s: they get a bit younger
    Late 50s+: young pros start to appear
    60s+: modern-style younger entries
    """
    if year <= 1950:
        # Early post-war: older guys coming in late
        return random.randint(33, 48)
    elif year <= 1953:
        # Still mostly late entrants, but a bit younger creeping in
        return random.randint(30, 42)
    elif year <= 1956:
        # Mix of mid-20s to late 30s
        return random.randint(26, 38)
    elif year <= 1960:
        # Younger talent showing up more regularly
        return random.randint(22, 35)
    else:
        # Proper modern era – young hotshoes
        return random.randint(18, 30)

def get_retirement_ages_for_year(year: int):
    """
    Returns (soft_retire_age, hard_retire_age) for that era.

    soft_retire_age  = age where decline starts to accelerate
    hard_retire_age  = age where decline is steep and retirement is looming

    For now this is VERY rough and only era-based by year.
    """
    if year < 1960:
        # Early days: lots of old boys still hanging around
        return (48, 52)
    elif year < 1980:
        # Mid-century: drivers start bowing out earlier
        return (45, 49)
    else:
        # Modern-ish: shorter careers at the top
        return (40, 45)



def create_regen_driver(time):
    """
    Create a new AI driver based on the current year.
    Used when older drivers retire or when the market expands.
    """

    # Use the year-based age logic
    age = get_regen_age_for_year(time.year)

    # Random stats, but era-appropriate (early post-war: low avg skill)
    pace = random.randint(2, 6)
    consistency = random.randint(2, 6)
    aggression = random.randint(2, 6)
    mech = random.randint(1, 4)
    wet = random.randint(1, 4)

    # Dynamic fame (rare stars early on)
    if time.year <= 1950:
        fame = random.choices([0,1], weights=[80,20])[0]
    else:
        fame = random.choices([0,1,2], weights=[60,30,10])[0]

    # Career arc: peak and decline vary by generation
    peak_age = random.randint(age + 1, age + 6)
    decline_age = peak_age + random.randint(3, 6)

    new_d = {
        "name": generate_random_driver_name(),
        "constructor": "Independent",
        "pace": pace,
        "consistency": consistency,
        "aggression": aggression,
        "mechanical_sympathy": mech,
        "wet_skill": wet,
        "fame": fame,
        "age": age,
        "peak_age": peak_age,
        "decline_age": decline_age,
    }

    # Car comfort / familiarity starts at zero for new drivers
    new_d["car_xp"] = 0.0

    return new_d




def describe_career_phase(d: dict) -> str:
    """
    Use age vs peak/decline ages to describe where they are
    in their career WITHOUT exposing the exact numbers.
    """
    age = d.get("age")
    peak = d.get("peak_age")
    decline = d.get("decline_age")

    if age is None or peak is None or decline is None:
        return "Career stage unknown"

    # A bit before peak: they're still climbing
    if age < peak - 1:
        return "Rising talent"

    # Within ~1 year either side of peak: prime years
    if peak - 1 <= age <= peak + 1:
        return "At or near their peak"

    # After peak but before full decline age
    if peak + 1 < age < decline:
        return "Experienced, starting to plateau"

    # Just past decline age: gentle fade
    if decline <= age < decline + 3:
        return "Veteran, gentle decline"

    # Well past decline + soft retirement window
    return "Late-career veteran – not as sharp as they were"

def maybe_spawn_scuderia_valdieri(state, time, season_week, race_calendar):
    """
    World event:
    - In 1948, two weeks before Ardennes Endurance GP,
      Scuderia Valdieri enters the sport and signs 2 drivers.
    Fires once per save.
    """

    if time.year != 1948:
        return

    if getattr(state, "valdieri_spawned", False):
        return

    # Find the week Ardennes happens this year
    ardennes_week = None
    for wk, race in race_calendar.items():
        if race == "Ardennes Endurance GP":
            ardennes_week = wk
            break

    if ardennes_week is None:
        return

    # Trigger exactly 2 weeks before Ardennes
    if season_week != (ardennes_week - 2):
        return

    team = "Scuderia Valdieri"

    # Safety: ensure constructor exists in data.py
    if team not in constructors:
        state.news.append(f"DEBUG: {team} could not spawn (missing from constructors).")
        state.valdieri_spawned = True
        state.valdieri_active = False
        return

    # Build candidate pool (Independent drivers only)
    candidates = []
    for d in drivers:
        if d.get("constructor") != "Independent":
            continue
        if state.player_driver is d:
            continue

        age = d.get("age", 40)

        # Valdieri mentality: pace + consistency with slight youth bias
        score = (
            d.get("pace", 0) * 1.2 +
            d.get("consistency", 0) * 0.9 +
            max(0, 38 - age) * 0.15
        )
        candidates.append((score, d))

    candidates.sort(key=lambda x: x[0], reverse=True)

    if len(candidates) < 2:
        state.news.append(f"{team} rumoured, but fail to secure enough drivers.")
        state.valdieri_spawned = True
        state.valdieri_active = False
        return

    signed = [candidates[0][1], candidates[1][1]]

    for d in signed:
        d["constructor"] = team

    # ✅ flags other systems can use
    state.valdieri_spawned = True
    state.valdieri_active = True

    state.news.append(
        f"New challenger arrives: {team} announce their debut, "
        f"signing {signed[0]['name']} and {signed[1]['name']} ahead of Ardennes."
    )


def maybe_add_weekly_rumour(state, time):
    """
    Inject contextual paddock gossip that reflects actual game events.
    Rumors are now based on real happenings: upcoming races, weather, 
    driver performance, stat changes, championship standings, etc.
    """
    # ~35% chance per week
    if random.random() > 0.35:
        return

    from gmr.data import drivers, tracks
    from gmr.core_time import get_season_week
    from gmr.calendar import generate_calendar_for_year
    
    rumours = []
    team_name = state.player_constructor or "Your team"
    season_week = get_season_week(time)
    race_calendar = generate_calendar_for_year(time.year)
    
    # =========================================================================
    # UPCOMING RACE RUMORS
    # =========================================================================
    upcoming_races = []
    for week in range(season_week, min(season_week + 4, 49)):
        if week in race_calendar and week not in state.completed_races:
            upcoming_races.append((week, race_calendar[week]))
    
    if upcoming_races:
        next_week, next_race = upcoming_races[0]
        track_profile = tracks.get(next_race, {})
        
        # Weather predictions
        wet_chance = track_profile.get("wet_chance", 0.2)
        hot_chance = track_profile.get("base_hot_chance", 0.2)
        
        if wet_chance > 0.5:
            rumours.append(f"📰 Weather report: Heavy rain expected at {next_race}. Teams scrambling for wet setups.")
            rumours.append(f"📰 Meteorologists warn of challenging conditions for {next_race} this weekend.")
        elif wet_chance > 0.3:
            rumours.append(f"📰 Mixed forecast for {next_race} — teams preparing for all conditions.")
        
        if hot_chance > 0.5:
            rumours.append(f"📰 Heatwave warning for {next_race}! Cooling systems will be tested to the limit.")
            rumours.append(f"📰 Mechanics checking radiators ahead of scorching conditions at {next_race}.")
        
        # Track characteristics
        engine_danger = track_profile.get("engine_danger", 1.0)
        crash_danger = track_profile.get("crash_danger", 1.0)
        
        if engine_danger > 1.2:
            rumours.append(f"📰 {next_race} is notoriously hard on engines. Teams reinforcing their mechanics crews.")
        if crash_danger > 1.2:
            rumours.append(f"📰 {next_race} demands respect — it's claimed many careers over the years.")
        
        # Home race check
        if state.player_driver:
            player_country = state.player_driver.get("country", "")
            track_country = track_profile.get("country", "")
            if player_country and player_country == track_country:
                driver_name = state.player_driver.get("name", "Your driver")
                rumours.append(f"📰 Home race excitement! {driver_name} will have local crowd support at {next_race}.")
        
        # Prize money rumors
        from gmr.constants import PRIZE_RULES, DEFAULT_PRIZE_TOP3
        prize_rule = PRIZE_RULES.get(next_race)
        if prize_rule:
            top_prize = prize_rule.get("top3", DEFAULT_PRIZE_TOP3)[0]
            if top_prize >= 500:
                rumours.append(f"📰 Big money on offer at {next_race}! Winner takes home £{top_prize}.")
    
    # =========================================================================
    # CHAMPIONSHIP STANDINGS RUMORS
    # =========================================================================
    if state.points:
        sorted_standings = sorted(state.points.items(), key=lambda x: x[1], reverse=True)
        top_drivers = [(name, pts) for name, pts in sorted_standings if pts > 0][:5]
        
        if len(top_drivers) >= 2:
            leader_name, leader_pts = top_drivers[0]
            second_name, second_pts = top_drivers[1]
            gap = leader_pts - second_pts
            
            if gap == 0:
                rumours.append(f"📰 TITLE BATTLE! {leader_name} and {second_name} tied on {leader_pts} points!")
            elif gap <= 3:
                rumours.append(f"📰 Championship fight heating up: {leader_name} leads {second_name} by just {gap} points.")
            elif gap >= 15:
                rumours.append(f"📰 {leader_name} running away with it — {gap} point advantage looks unassailable.")
            
            # Check if player's driver is in contention
            if state.player_driver:
                player_name = state.player_driver.get("name")
                player_pts = state.points.get(player_name, 0)
                if player_pts > 0:
                    player_rank = next((i+1 for i, (n, p) in enumerate(top_drivers) if n == player_name), None)
                    if player_rank == 1:
                        rumours.append(f"📰 {team_name} at the top! Everyone's chasing {player_name}.")
                    elif player_rank and player_rank <= 3:
                        rumours.append(f"📰 {player_name} in the title hunt — {team_name} proving they belong.")
    
    # =========================================================================
    # DRIVER PERFORMANCE / STAT CHANGE RUMORS
    # =========================================================================
    # Find drivers on hot streaks (multiple recent wins/podiums)
    if state.race_history and len(state.race_history) >= 2:
        recent_races = state.race_history[-3:]  # Last 3 races
        
        win_counts = {}
        podium_counts = {}
        dnf_counts = {}
        
        for race in recent_races:
            if race.get("finishers"):
                winner = race["finishers"][0]
                win_counts[winner["name"]] = win_counts.get(winner["name"], 0) + 1
                
                for pos, finisher in enumerate(race["finishers"][:3]):
                    podium_counts[finisher["name"]] = podium_counts.get(finisher["name"], 0) + 1
            
            for dnf in race.get("dnfs", []):
                dnf_counts[dnf["name"]] = dnf_counts.get(dnf["name"], 0) + 1
        
        # Hot streak drivers
        for driver_name, wins in win_counts.items():
            if wins >= 2:
                rumours.append(f"📰 {driver_name} is ON FIRE! {wins} wins from the last 3 races.")
                rumours.append(f"📰 Who can stop {driver_name}? The paddock is buzzing about their dominant form.")
        
        # Consistent podium finishers
        for driver_name, podiums in podium_counts.items():
            if podiums >= 3 and driver_name not in win_counts:
                rumours.append(f"📰 {driver_name} quietly delivering — 3 consecutive podiums. A title dark horse?")
        
        # Reliability concerns
        for driver_name, dnfs in dnf_counts.items():
            if dnfs >= 2:
                rumours.append(f"📰 {driver_name} plagued by reliability issues — {dnfs} retirements in recent races.")
    
    # Look for drivers with recent XP gains (stat improvements)
    high_xp_drivers = []
    declining_drivers = []
    for d in drivers:
        xp = d.get("xp", 0)
        age = d.get("age", 25)
        peak_age = d.get("peak_age", 28)
        decline_age = d.get("decline_age", 34)
        
        # Rising stars with banked XP
        if xp >= 4.0 and age < peak_age:
            high_xp_drivers.append(d)
        
        # Veterans past decline
        if age > decline_age + 3:
            declining_drivers.append(d)
    
    if high_xp_drivers:
        driver = random.choice(high_xp_drivers)
        rumours.append(f"📰 {driver['name']} showing rapid improvement — scouts say they're close to a breakthrough.")
        rumours.append(f"📰 Insiders tip {driver['name']} for great things. Experience is paying off.")
    
    if declining_drivers:
        driver = random.choice(declining_drivers)
        rumours.append(f"📰 Is {driver['name']} past their prime? Some say the veteran should consider retirement.")
    
    # =========================================================================
    # PLAYER-SPECIFIC RUMORS
    # =========================================================================
    if state.player_driver:
        player = state.player_driver
        player_name = player.get("name")
        
        # Contract status
        if state.driver_contract_races <= 2 and state.driver_contract_races > 0:
            rumours.append(f"📰 Contract watch: {player_name}'s deal with {team_name} expires soon. Will they re-sign?")
        
        # Recent form
        if state.race_history:
            last_race = state.race_history[-1]
            player_finish = next((f["pos"] for f in last_race.get("finishers", []) if f["name"] == player_name), None)
            
            if player_finish == 1:
                rumours.append(f"📰 {team_name} riding high after victory! {player_name} is the talk of the paddock.")
            elif player_finish and player_finish <= 3:
                rumours.append(f"📰 {player_name} keeping {team_name} in the headlines with another podium.")
            elif player_finish and player_finish > 15:
                rumours.append(f"📰 Questions being asked at {team_name} after disappointing result.")
        
        # Fame/reputation
        fame = player.get("fame", 0)
        if fame >= 7:
            rumours.append(f"📰 {player_name} is a household name now. Autograph hunters mob the paddock.")
        elif fame >= 4:
            rumours.append(f"📰 {player_name} building a solid reputation. Respected in the paddock.")
        elif fame <= 1:
            rumours.append(f"📰 {player_name}? Who? The press still don't know {team_name}'s driver.")
    
    # =========================================================================
    # FINANCIAL / SPONSOR RUMORS  
    # =========================================================================
    if state.money < 300:
        rumours.append(f"📰 Creditors circling {team_name}? Rumours of unpaid bills and worried suppliers.")
    elif state.money < 800:
        rumours.append(f"📰 {team_name} tightening belts — catering downgraded to sandwiches and cold tea.")
    elif state.money > 8000:
        rumours.append(f"📰 {team_name} flush with cash! Rivals envious of the team's healthy budget.")
    
    if state.sponsor_active:
        if state.sponsor_podiums >= 3:
            rumours.append(f"📰 {state.sponsor_name} executives thrilled — their investment is paying dividends.")
        elif state.sponsor_races_started > 5 and state.sponsor_podiums == 0:
            rumours.append(f"📰 Whispers that {state.sponsor_name} are disappointed with {team_name}'s results.")
    else:
        if state.prestige >= 5:
            rumours.append(f"📰 Several sponsors reportedly interested in {team_name}. Expect announcements soon.")
    
    # Tyre sponsor
    if getattr(state, 'tyre_sponsor_active', False):
        tyre_sponsor = getattr(state, 'tyre_sponsor_name', 'Unknown')
        rumours.append(f"📰 {tyre_sponsor} truck spotted at {team_name}'s garage — the tyre deal is working well.")
    
    # =========================================================================
    # PRESTIGE / REPUTATION RUMORS
    # =========================================================================
    if state.prestige >= 20:
        rumours.append(f"📰 {team_name} has established themselves as a serious outfit. Works teams taking notice.")
    elif state.prestige >= 10:
        rumours.append(f"📰 {team_name} earning respect in the paddock. No longer dismissed as backmarkers.")
    elif state.prestige <= 2:
        rumours.append(f"📰 {team_name} still considered rank outsiders. The big teams barely acknowledge them.")
    
    # =========================================================================
    # WORKS TEAM RUMORS
    # =========================================================================
    if getattr(state, 'valdieri_active', False):
        rumours.append("📰 Scuderia Valdieri mechanics working late into the night. A new development coming?")
    
    rumours.append("📰 Enzoni testing revolutionary suspension geometry at their private test track.")
    
    # =========================================================================
    # ERA-SPECIFIC / SEASONAL RUMORS
    # =========================================================================
    from gmr.constants import get_era_name
    era = get_era_name(time.year)
    
    if time.year < 1950:
        rumours.append("📰 Talk of formalizing a proper world championship — the FIA is deliberating.")
        rumours.append("📰 Pre-war drivers returning to the circuits. The old guard still has pace.")
    elif time.year < 1960:
        rumours.append("📰 Rear-engine experiments causing controversy. Purists call it 'ungentlemanly'.")
        rumours.append("📰 Commercial sponsorship creeping in. Some say it cheapens the sport.")
    elif time.year < 1970:
        rumours.append("📰 Aerodynamics becoming crucial. Wind tunnel time is the new arms race.")
    elif time.year < 1980:
        rumours.append("📰 Ground effect technology is reshaping car design. Dangerous speeds worry officials.")
    elif time.year < 1990:
        rumours.append("📰 Turbo engines delivering insane power. Reliability is the only question.")
    elif time.year < 2000:
        rumours.append("📰 Electronics revolution changing racing. Some call it the 'gadget era'.")
    elif time.year < 2010:
        rumours.append("📰 Aerodynamic downforce at record levels. Overtaking becoming nearly impossible.")
    elif time.year < 2020:
        rumours.append("📰 Hybrid power units bringing new complexity. Manufacturers love the tech showcase.")
    else:
        rumours.append("📰 Sustainable fuels and electric hybrids — racing adapts to a changing world.")
        rumours.append("📰 Autonomous assistance systems being tested. The future is here.")
    
    # End of season rumors
    if season_week >= 40:
        rumours.append("📰 Silly season heating up! Driver moves and team changes expected over winter.")
        rumours.append("📰 Contract negotiations intensifying as the season draws to a close.")
    
    # Start of season
    if season_week <= 4:
        rumours.append("📰 Fresh season, fresh hopes! Teams optimistic after winter preparation.")
        rumours.append("📰 Pre-season testing gave little away — the real pecking order remains unclear.")
    
    # =========================================================================
    # OUTPUT A RANDOM RUMOR
    # =========================================================================
    if rumours:
        state.news.append("PADDOCK TALK: " + random.choice(rumours).replace("📰 ", ""))

def apply_ai_works_chassis_development(state, time):
    """
    Offseason-only development for works teams.
    Uses dev_slots / dev_runs_done on their works chassis.
    """

    from gmr.data import chassis_list, constructors

    # Which works teams exist right now
    works_teams = ["Enzoni"]
    if getattr(state, "valdieri_active", False):
        works_teams.append("Scuderia Valdieri")

    for team in works_teams:
        ctor = constructors.get(team)
        if not ctor:
            continue

        chassis_id = ctor.get("chassis_id")
        if not chassis_id:
            continue

        # Find the chassis object
        ch = None
        for c in chassis_list:
            if c.get("id") == chassis_id:
                ch = c
                break

        if not ch:
            continue

        # Ensure slot fields exist
        ch.setdefault("dev_slots", 1)
        ch.setdefault("dev_runs_done", 0)

        # No slots left → nothing happens
        if ch["dev_runs_done"] >= ch["dev_slots"]:
            continue

        # Works teams have better mechanics baked in
        dev_bonus = ctor.get("dev_bonus", 0.15)

        # One dev roll per offseason
        base_quality = 0.9          # works baseline
        quality = base_quality + dev_bonus
        quality = min(1.4, quality)

        roll = random.random()

        # Same structure as player dev, but simplified
        if roll < 0.15:
            ch["aero"] = max(1, ch["aero"] - 1)
            outcome = "suffer a development setback"
        elif roll < 0.70:
            ch["aero"] += 1
            outcome = "find modest gains"
        else:
            ch["aero"] += 2
            outcome = "unlock a major aerodynamic improvement"

        ch["aero"] = max(1, min(ch["aero"], 12))
        ch["dev_runs_done"] += 1

        state.news.append(
            f"{team} engineers {outcome} over the winter "
            f"(chassis development {ch['dev_runs_done']}/{ch['dev_slots']})."
        )
