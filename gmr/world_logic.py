# gmr/world_logic.py
import random
from gmr.data import drivers, constructors
from gmr.constants import clamp_chassis_aero, is_championship_year
from gmr.calendar import is_transatlantic_race


DRIVER_FIRST_NAMES = [
    # Italian
    "Carlo", "Alberto", "Marco", "Antonio", "Paolo", "Giancarlo",
    "Franco", "Sergio", "Mario", "Giuseppe", "Vittorio", "Enrico",
    "Umberto", "Luigi", "Gino", "Bruno", "Renato", "Piero", "Aldo",
    # French
    "Emmanuel", "Jean", "Pierre", "Henri", "Jacques", "Michel",
    "Claude", "Lucien", "Marcel", "Émile", "Roger", "Louis",
    "Georges", "André", "Armand", "Yves", "Alain", "Raymond",
    # Germanic
    "Hans", "Wolfgang", "Helmut", "Klaus", "Dieter", "Rolf",
    "Horst", "Karl", "Ernst", "Wilhelm", "Otto", "Friedrich",
    "Rudolf", "Heinz", "Kurt", "Franz", "Manfred", "Gerhard",
    # British
    "George", "Dennis", "Peter", "Colin", "John", "Graham",
    "Ian", "Jack", "Arthur", "Edward", "Henry", "Ronald",
    "Stanley", "Frederick", "Albert", "Norman", "Nigel", "Mike",
    # Spanish/Portuguese
    "Pedro", "Miguel", "Diego", "Luis", "Manuel", "Rafael",
    "Ángel", "Andrés", "Javier", "Pablo", "Tomás", "Vicente",
    # Brazilian
    "João", "Paulo", "Rubens", "Chico", "Sérgio", "Wilson",
    "Nelson", "Emerson", "Roberto", "Maurício", "Raul", "Clovis",
    # Argentinian
    "Juan", "Carlos", "Fernando", "Héctor", "Raúl", "Oscar",
    "José", "Froilán", "Onofre", "Clemar", "Norberto", "Benedicto",
]

DRIVER_LAST_NAMES = [
    # Italian
    "Ricci", "Verdi", "Neri", "Esposito", "Gallo", "Colombo",
    "Romano", "Conti", "De Luca", "Moretti", "Marini", "Serafini",
    "Barbieri", "Valenti", "Benedetti", "Santini", "Pellegrini",
    # French
    "Dubois", "Dupont", "Bernard", "Martin", "Laurent", "Leclerc",
    "Arnoux", "Morel", "Lefèvre", "Lambert", "Renaud", "Girard",
    "Faure", "Perrin", "Marchand", "Chevalier", "Delattre", "Beaumont",
    # Germanic
    "Keller", "Mueller", "Schmidt", "Weber", "Hoffmann", "Fischer",
    "Richter", "Schneider", "Weiss", "Bauer", "Klein", "Vogel",
    "Hartmann", "Neumann", "Hoffner", "Brandt", "Steiner", "Lorenz",
    # British
    "McCallister", "Hill", "Watson", "Whitmore", "Crawford", "Hawkins",
    "Turner", "Collins", "Bennett", "Walker", "Thompson", "Mitchell",
    "Baker", "Ellis", "Harrison", "Caldwell", "Broome", "Pemberton",
    # Spanish/Portuguese
    "Navarro", "Garcia", "Lopez", "Martinez", "Ramirez", "Fernandez",
    "Morales", "Serrano", "Domínguez", "Carrasco", "Iglesias", "Velasco",
    # Brazilian
    "Figueiredo", "Mendonça", "Almeida", "Ribeiro", "Silveira", "Cardoso",
    "Teixeira", "Ferreira", "Machado", "Bueno", "Leme", "Guimarães",
    # Argentinian
    "Ortega", "Ramos", "Sánchez", "Vidal", "González", "Gálvez",
    "Quiroga", "Acosta", "Perdomo", "Bordeu", "Leguizamón", "Medina",
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

def calculate_car_speed(engine, chassis, gearbox=None, brakes=None):
    if engine is None or chassis is None:
        return 0
    lightness = 11 - chassis["weight"]
    gearbox_bonus = 0.0
    if gearbox:
        gearbox_bonus = (gearbox.get("shift_quality", 5) - 5) * 0.3
    engine_component = engine["speed"] * 0.7 + (engine["acceleration"] + gearbox_bonus) * 0.3

    brake_bonus = 0.0
    if brakes:
        brake_bonus = (brakes.get("braking", 5) - 5) * 0.2
    chassis_component = (chassis["aero"] + brake_bonus) * 0.7 + lightness * 0.3
    car_speed = engine_component * 0.6 + chassis_component * 0.4
    return round(car_speed, 1)


def calculate_car_reliability(engine, gearbox=None):
    """Combine engine reliability with gearbox durability bonuses."""
    if not engine:
        return 0
    reliability = float(engine.get("reliability", 5))
    if gearbox:
        reliability += float(gearbox.get("reliability_bonus", 0))
    return max(1.0, min(10.0, reliability))

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
    gearbox = getattr(state, "current_gearbox", None)
    brakes = getattr(state, "current_brakes", None)

    gearbox_bonus = 0.0
    if gearbox:
        gearbox_bonus = (gearbox.get("shift_quality", 5) - 5) * 0.3

    engine_component = (
        engine["speed"] * top_speed_weight +
        (engine["acceleration"] + gearbox_bonus) * accel_weight
    )

    # Chassis contribution as before
    lightness = 11 - chassis["weight"]
    brake_bonus = 0.0
    if brakes:
        brake_bonus = (brakes.get("braking", 5) - 5) * 0.2
    chassis_component = (chassis["aero"] + brake_bonus) * 0.7 + lightness * 0.3

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

    CHAMPIONSHIP RULES (from 1951):
    - All constructors attend every championship race (except transatlantic)
    - Only fame 1+ Americans join European championship events
    - Transatlantic races have special restrictions
    
    LOCAL AMERICAN RACES:
    - Copper State Circuit: Small desert track, American drivers only
    
    Patch C: Enzoni only do Italian races + Vallone + Ardennes (demo logic).
    Patch F: 'Test' drivers are debug-only and do not enter real races unless enabled.
    Patch G: Gentleman drivers have selective entries (big races + random medium ones).
    """
    from gmr.calendar import BIG_RACES, MEDIUM_RACES, is_championship_race, is_transatlantic_race
    from gmr.constants import is_championship_year

    ctor = driver.get("constructor")
    year = time.year if time else 1948

    # Patch F: test archetypes are for dev only
    if ctor == "Test":
        return TEST_DRIVERS_ENABLED

    # Check appears_from_year for drivers who enter later
    appears_from = driver.get("appears_from_year")
    if appears_from and time:
        if time.year < appears_from:
            return False

    # ─────────────────────────────────────────────────────────────────
    # LOCAL AMERICAN RACES - Americans only
    # Copper State Circuit is a small dusty desert track where local
    # American racers compete. Europeans don't bother with the trip.
    # ─────────────────────────────────────────────────────────────────
    if race_name == "Copper State Circuit":
        driver_nat = driver.get("country", "UK")
        if driver_nat != "USA":
            return False
        # American drivers enter normally (continue to other checks)

    # ─────────────────────────────────────────────────────────────────
    # WORLD CHAMPIONSHIP RACE LOGIC (from 1951)
    # All constructors attend championship races - it's mandatory!
    # ─────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────
    if is_championship_year(year) and is_championship_race(race_name, year):
        driver_nat = driver.get("country", "UK")
        fame = driver.get("fame", 0)
        
        # Handle transatlantic races (Union Speedway)
        if is_transatlantic_race(race_name, year):
            # Americans always attend US championship races
            if driver_nat == "USA":
                return True
            
            # Europeans: Only well-funded operations make the crossing
            # Independents almost never go
            if ctor == "Independent":
                if fame < 4:
                    return False
                # Even famous independents only 20% chance
                seed = hash((driver.get("name", ""), race_name, year))
                rng = random.Random(seed)
                return rng.random() < 0.2
            
            # Works teams send their star driver only
            team_prestige = constructors.get(ctor, {}).get("prestige", 5)
            if team_prestige < 8:
                return False
            
            # Only the most famous driver from each top team
            team_drivers = [d for d in drivers if d.get("constructor") == ctor]
            max_fame_in_team = max((d.get("fame", 0) for d in team_drivers), default=0)
            if fame < max_fame_in_team:
                return False
            
            # 60% chance even for stars
            seed = hash((ctor, driver.get("name", ""), race_name, year))
            rng = random.Random(seed)
            return rng.random() < 0.6
        
        # European championship races - mandatory for all constructors!
        # But Americans need fame 1+ to make the trip to Europe
        if driver_nat == "USA":
            if fame < 1:
                return False
        
        # All constructors MUST attend European championship races
        # This is the World Championship - everyone wants to be there!
        return True

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
        # Check if Valdieri is a proper constructor (spawned and active)
        valdieri_active = state and getattr(state, "valdieri_active", False)
        
        if valdieri_active:
            # ─────────────────────────────────────────────────────────────
            # RIVALRY MODE: Valdieri enters all European races Enzoni does
            # They're fierce competitors and match each other's schedule
            # ─────────────────────────────────────────────────────────────
            
            # Skip tiny club circuits - beneath factory teams
            if race_name == "Bradley Fields":
                return False
            
            # Skip Americas races (too far, not worth it for European rivalry)
            country = track_profile.get("country", "")
            if country in ("USA", "Brazil", "Argentina", "Mexico"):
                # Exception: Send 1 car to big Americas races (prestige)
                # This is handled at grid-building level (only 1 driver)
                if race_name in ("Union Speedway", "Autódromo General San Martín"):
                    # Only the team's top driver goes
                    team_drivers = [d for d in drivers if d.get("constructor") == ctor]
                    if team_drivers:
                        top_driver = max(team_drivers, 
                                        key=lambda x: x.get("fame", 0) * 2 + x.get("pace", 0))
                        if driver == top_driver:
                            return True
                    return False
                return False
            
            # Enter all European races (matching Enzoni)
            return True
        else:
            # Pre-spawn: Scuderia Valdieri not yet active as full constructor
            allowed_races = {
                "Vallone GP",
                "Little Autodromo",
                "Ardennes Endurance GP",
                "Château-des-Prés GP",
                "Marblethorpe GP",
            }

            if race_name in allowed_races:
                return True

            # Allow Italian races
            country = track_profile.get("country", "")
            if country == "Italy":
                return True

            return False



    # ─────────────────────────────────────────────────────────────────
    # NON-CHAMPIONSHIP TRANSATLANTIC TRAVEL (pre-1951 or non-champ races)
    # European drivers rarely travel to USA races due to shipping costs.
    # ─────────────────────────────────────────────────────────────────
    from gmr.calendar import is_transatlantic_race
    if race_name == "Union Speedway":  # Check for any USA race
        driver_nat = driver.get("country", "UK")
        fame = driver.get("fame", 0)
        
        # Americans always enter US races
        if driver_nat == "USA":
            pass  # Always enters
        else:
            # Pre-championship or non-champ USA races - very few Europeans go
            if ctor == "Independent":
                if fame < 4:
                    return False
                seed = hash((driver.get("name", ""), race_name, year))
                rng = random.Random(seed)
                if rng.random() > 0.2:
                    return False
            else:
                team_prestige = constructors.get(ctor, {}).get("prestige", 5)
                if team_prestige < 8:
                    return False
                team_drivers = [d for d in drivers if d.get("constructor") == ctor]
                max_fame_in_team = max((d.get("fame", 0) for d in team_drivers), default=0)
                if fame < max_fame_in_team:
                    return False
                seed = hash((ctor, driver.get("name", ""), race_name, year))
                rng = random.Random(seed)
                if rng.random() > 0.6:
                    return False

    # Everyone else: always enters for now (subject to Enzoni rules below)
    if ctor != "Enzoni":
        return True

    # ─────────────────────────────────────────────────────────────────
    # ENZONI SCHEDULE RULES
    # Once Valdieri is active, Enzoni expands to match their rival
    # ─────────────────────────────────────────────────────────────────
    valdieri_active = state and getattr(state, "valdieri_active", False)
    
    if valdieri_active:
        # RIVALRY MODE: Enzoni enters all European races to match Valdieri
        
        # Skip tiny club circuits - beneath factory teams
        if race_name == "Bradley Fields":
            return False
        
        # Skip Americas races (too far, rivalry is in Europe)
        country = track_profile.get("country", "")
        if country in ("USA", "Brazil", "Argentina", "Mexico"):
            # Exception: Send 1 car to big Americas races (prestige)
            if race_name in ("Union Speedway", "Autódromo General San Martín"):
                # Only the team's top driver goes
                team_drivers = [d for d in drivers if d.get("constructor") == ctor]
                if team_drivers:
                    top_driver = max(team_drivers, 
                                    key=lambda x: x.get("fame", 0) * 2 + x.get("pace", 0))
                    if driver == top_driver:
                        return True
                return False
            return False
        
        # Enter all European races
        return True
    else:
        # Pre-rivalry: Enzoni's original limited schedule
        allowed_races = {
            "Vallone GP",
            "Little Autodromo",
            "Ardennes Endurance GP",
        }

        if race_name in allowed_races:
            return True

        # Allow ANY Italian event
        country = track_profile.get("country", "")
        if country == "Italy":
            return True

        return False

def can_team_sign_driver(state, driver):
    """
    Check whether your team has enough prestige to realistically
    sign this driver based on their fame AND their current team's prestige.

    Two checks:
    1. Fame gate: driver fame * 2.5 <= your prestige
       - Fame 0–1  -> basically anyone will talk to you
       - Fame 2    -> want prestige ~5+
       - Fame 3    -> want prestige ~7.5+
       - Fame 4    -> want prestige ~10+

    2. Team prestige gate: if driver is at a bigger team, you need to
       significantly out-prestige them to poach (prestige gap of 3+).
       Drivers at smaller teams or Independents can be signed if you pass fame check.

    Returns (can_sign: bool, required_prestige: float, rejection_reason: str or None)
    """
    from gmr.data import constructors
    
    fame = driver.get("fame", 0)
    prestige = getattr(state, "prestige", 0.0)

    # 1. Fame-based requirement
    required_prestige = float(fame) * 2.5
    
    if prestige < required_prestige:
        return False, required_prestige, "fame"
    
    # 2. Team prestige gate - can't easily poach from bigger/equal teams
    current_team = driver.get("constructor", "Independent")
    team_data = constructors.get(current_team, {})
    team_prestige = team_data.get("prestige", 0.0)
    
    # If driver is at a real team (not Independent), check team prestige
    if current_team not in ("Independent", "Test") and not driver.get("hirable"):
        # Need to be significantly more prestigious to poach (gap of 3+)
        # This prevents small teams from easily poaching big team drivers
        prestige_gap_needed = 3.0
        
        if prestige < team_prestige + prestige_gap_needed:
            # You're not prestigious enough to lure them away
            return False, team_prestige + prestige_gap_needed, "team"
    
    return True, required_prestige, None


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


    def _rivalry_key(prefix: str, a: str, b: str) -> str:
        left, right = sorted([a, b])
        return f"{prefix}:{left}|{right}"


    def _bump_rivalry(state, key: str, amount: int, rivalry_type: str, headline: str, year: int):
        entry = state.rivalries.get(key, {"score": 0, "last_level": 0, "type": rivalry_type})
        entry["score"] += amount
        state.rivalries[key] = entry

        # Escalation thresholds
        level = 0
        if entry["score"] >= 3:
            level = 1
        if entry["score"] >= 6:
            level = 2
        if entry["score"] >= 10:
            level = 3

        if level > entry["last_level"]:
            entry["last_level"] = level
            state.rivalries[key] = entry
            state.news.append(headline)

        # Occasional cheating accusations once rivalry is hot
        if entry["score"] >= 6 and random.random() < 0.2:
            state.news.append("📰 Accusations fly in the paddock as tensions boil over between rivals.")


    def update_rivalries_after_race(state, finishers, dnf_drivers, retire_reasons, race_name, year):
        """
        Simple rivalry system:
        - Close finishes between drivers from different constructors
        - Crash DNFs can trigger blame
        - Constructor rivalries when P1/P2 are different teams
        """
        if not hasattr(state, "rivalries"):
            state.rivalries = {}

        # Constructor rivalry: P1 vs P2
        if len(finishers) >= 2:
            p1_driver, _ = finishers[0]
            p2_driver, _ = finishers[1]
            c1 = p1_driver.get("constructor", "Independent")
            c2 = p2_driver.get("constructor", "Independent")
            if c1 != c2 and c1 != "Independent" and c2 != "Independent":
                key = _rivalry_key("ctor", c1, c2)
                headline = f"🔥 Rivalry flares: {c1} and {c2} trade blows at {race_name}."
                _bump_rivalry(state, key, 2, "constructor", headline, year)

        # Driver rivalry: close finishers (positions 1–6)
        top_finishers = finishers[:6]
        for i in range(len(top_finishers) - 1):
            d1, _ = top_finishers[i]
            d2, _ = top_finishers[i + 1]
            if d1.get("constructor") != d2.get("constructor"):
                key = _rivalry_key("driver", d1.get("name", ""), d2.get("name", ""))
                headline = (
                    f"🔥 Driver rivalry brewing: {d1.get('name')} and {d2.get('name')} clash on track at {race_name}."
                )
                _bump_rivalry(state, key, 1, "driver", headline, year)

        # Crash blame: if a crash DNF happened, stir a rival
        crash_dnfs = [d for d in dnf_drivers if retire_reasons.get(d.get("name")) == "crash"]
        if crash_dnfs and finishers:
            blamed = random.choice(finishers)[0]
            victim = random.choice(crash_dnfs)
            if victim.get("constructor") != blamed.get("constructor"):
                key = _rivalry_key("driver", victim.get("name", ""), blamed.get("name", ""))
                headline = (
                    f"🗞️ Tensions rise: {victim.get('name')} accuses {blamed.get('name')} after a crash at {race_name}."
                )
                _bump_rivalry(state, key, 2, "driver", headline, year)
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

    # Get allowed nationalities from constructor definition
    team_data = constructors.get(team, {})
    allowed_nats = team_data.get("allowed_nationalities", None)

    # Build candidate pool (Independent drivers only)
    candidates = []
    for d in drivers:
        if d.get("constructor") != "Independent":
            continue
        if state.player_driver is d:
            continue
        
        # Check nationality restrictions
        if allowed_nats:
            driver_nat = d.get("country", "")
            if driver_nat not in allowed_nats:
                continue
        
        # Check if driver is available yet (e.g., German drivers from 1950)
        appears_from = d.get("appears_from_year", 1947)
        if time.year < appears_from:
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


def maybe_spawn_silberkern_stahl(state, time, season_week, race_calendar):
    """
    World event:
    - In 1952, at the start of the season, Silberkern-Stahl enters with German drivers.
    - They only sign German (or Swiss) drivers.
    Fires once per save.
    """
    if time.year < 1952:
        return

    if getattr(state, "silberkern_spawned", False):
        return

    # Trigger early in 1952 season (before first race typically at week 9)
    # This gives some flexibility if week 1 is somehow skipped
    if season_week > 8:
        return

    team = "Silberkern-Stahl"

    # Safety: ensure constructor exists in data.py
    if team not in constructors:
        state.news.append(f"DEBUG: {team} could not spawn (missing from constructors).")
        state.silberkern_spawned = True
        state.silberkern_active = False
        return

    # Get allowed nationalities from constructor definition
    team_data = constructors.get(team, {})
    allowed_nats = team_data.get("allowed_nationalities", ["Germany", "Switzerland"])

    # Build candidate pool - Germanic drivers only
    candidates = []
    for d in drivers:
        if d.get("constructor") != "Independent":
            continue
        if state.player_driver is d:
            continue

        # Must be German or Swiss
        nat = d.get("country", "")
        if nat not in allowed_nats:
            continue
        
        # Check if driver is available yet
        appears_from = d.get("appears_from_year", 1947)
        if time.year < appears_from:
            continue

        age = d.get("age", 40)

        # Silberkern values consistency and mechanical sympathy (engineering mindset)
        score = (
            d.get("pace", 0) * 1.0 +
            d.get("consistency", 0) * 1.2 +  # Value consistency highly
            d.get("mechanical_sympathy", 0) * 0.5 +
            max(0, 35 - age) * 0.1  # Slight youth preference
        )
        candidates.append((score, d))

    candidates.sort(key=lambda x: x[0], reverse=True)

    if len(candidates) < 2:
        state.news.append(f"{team} cannot find enough German drivers to field a team.")
        state.silberkern_spawned = True
        state.silberkern_active = False
        return

    signed = [candidates[0][1], candidates[1][1]]

    for d in signed:
        d["constructor"] = team

    # Flags other systems can use
    state.silberkern_spawned = True
    state.silberkern_active = True

    state.news.append(
        f"🇩🇪 {team} field their first Grand Prix cars! "
        f"{signed[0]['name']} and {signed[1]['name']} take the seats."
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
        # All modifications use immediate clamping to prevent invalid intermediate values
        if roll < 0.15:
            ch["aero"] = clamp_chassis_aero(ch["aero"] - 1)
            outcome = "suffer a development setback"
        elif roll < 0.70:
            ch["aero"] = clamp_chassis_aero(ch["aero"] + 1)
            outcome = "find modest gains"
        else:
            ch["aero"] = clamp_chassis_aero(ch["aero"] + 2)
            outcome = "unlock a major aerodynamic improvement"

        ch["dev_runs_done"] += 1

        state.news.append(
            f"{team} engineers {outcome} over the winter "
            f"(chassis development {ch['dev_runs_done']}/{ch['dev_slots']})."
        )
