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
    return round(car_speed, 1)

def driver_enters_event(driver, race_name, track_profile, state=None):
    """
    Decide if a driver enters an event.

    Patch C: Enzoni only do Italian races + Vallone + Ardennes (demo logic).
    Patch F: 'Test' drivers are debug-only and do not enter real races unless enabled.
    """
    ctor = driver.get("constructor")

    # Patch F: test archetypes are for dev only
    if ctor == "Test":
        return TEST_DRIVERS_ENABLED

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
      - Fame 2    -> want prestige ~1+
      - Fame 3    -> want prestige ~2+
      - Fame 4    -> want prestige ~3+
      - etc.

    Returns (can_sign: bool, required_prestige: float)
    """
    fame = driver.get("fame", 0)
    prestige = getattr(state, "prestige", 0.0)

    # Simple first-pass formula: prestige must be at least (fame - 1)
    required_prestige = max(0.0, float(fame) - 1.0)

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
    Occasionally inject a bit of 'paddock gossip' into the news.
    Pure flavour – no mechanics hooked up (yet).
    """
    # Roughly 30% chance per week
    if random.random() > 0.30:
        return

    rumours = []

    team_name = state.player_constructor or "Your team"

    # Generic flavour
    rumours.append("Enzoni mechanics are rumoured to be testing a new chassis away from prying eyes.")
    rumours.append("A small outfit from Sardinia is said to be building a strange low-slung special.")
    rumours.append("Whispers in the paddock say prize money will be tightened next year.")
    rumours.append("Old hands mutter that the post-war boom won't last forever.")
    rumours.append(
        f"Some wonder why {team_name} skipped a recent race — whispers of budget trouble."
    )



    # Money-related
    if state.money < 500:
        rumours.append(
            f"{team_name} are rumoured to be behind on paying suppliers – "
            "some mechanics are said to be working on IOUs."
        )
    elif state.money > 4000:
        rumours.append(
            f"Other privateers grumble that {team_name} are 'rolling in it' compared to most outfits."
        )

    # Sponsor-related
    if state.sponsor_active and state.sponsor_name == "Gallant Leaf Tobacco":
        if state.sponsor_podiums > 0:
            rumours.append(
                "Gallant Leaf executives are reportedly delighted with how often their logo appears on the podium."
            )
        else:
            rumours.append(
                "Some in the paddock say Gallant Leaf expected more results for their money."
            )

    # Prestige-related
    if state.prestige >= 6.0:
        rumours.append(
            f"Word is that a few talented drivers have quietly asked about a seat with {team_name}."
        )
    elif state.prestige <= 1.0:
        rumours.append(
            f"Most teams still treat {team_name} as just another backmarker shed outfit."
        )

    if not rumours:
        return

    state.news.append("Paddock rumour: " + random.choice(rumours))

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
