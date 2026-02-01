# gmr/careers.py
import random
from copy import deepcopy


from gmr.data import drivers
from gmr.world_logic import (
    describe_career_phase,
    can_team_sign_driver,
    get_regen_age_for_year,
    get_retirement_ages_for_year,
)
# Snapshot the initial driver list so we can restore it later
STARTING_DRIVERS = deepcopy(drivers)


def reset_driver_pool():
    """
    Reset the driver pool to its initial starting state.
    Used when starting a brand-new career after bankruptcy or from menu.
    """
    drivers.clear()
    drivers.extend(deepcopy(STARTING_DRIVERS))



def era_fame_scale(year: int) -> float:
    if year <= 1951:
        return 0.35
    if year <= 1960:
        return 0.55
    if year <= 1975:
        return 0.75
    return 1.0


def tick_driver_contract_after_race_end(state, time, started_race: bool):
    """
    Decrement contract length by 1 ONLY after the race weekend is complete,
    and ONLY if the player actually started the race.

    If it expires, offer extension; if refused, release driver AFTER the race.
    
    Guards against being called multiple times in the same race week.
    """
    if not state.player_driver:
        return

    if not started_race:
        return

    if getattr(state, "driver_contract_races", 0) <= 0:
        return
    
    # Guard: Track which race week we last decremented to prevent double-decrement
    current_week = getattr(time, "week", 0)
    current_year = getattr(time, "year", 0)
    last_decrement_week = getattr(state, "_contract_last_decrement_week", -1)
    last_decrement_year = getattr(state, "_contract_last_decrement_year", -1)
    
    if current_year == last_decrement_year and current_week == last_decrement_week:
        # Already decremented this race week - skip to prevent double-decrement
        return
    
    # Record that we're decrementing this week
    state._contract_last_decrement_week = current_week
    state._contract_last_decrement_year = current_year

    # decrement once per race started
    state.driver_contract_races -= 1

    # expired -> offer extension
    if state.driver_contract_races <= 0:
        extended = maybe_offer_driver_extension(state, time)
        if not extended:
            # maybe_offer_driver_extension() handles cleanup + setting to Independent
            return



def maybe_refill_ai_teams(state, time):
    """
    Check all AI teams that have 'replenishes': True in their constructor data.
    If they have fewer drivers than 'max_drivers', they sign from Independents.
    
    This handles Valdieri, Enzoni (after tragedy), and any future teams.
    """
    from gmr.data import constructors
    
    for team_name, team_data in constructors.items():
        # Skip non-replenishing teams
        if not team_data.get("replenishes", False):
            continue
        
        # Skip teams that aren't active yet (special case: Valdieri)
        if team_name == "Scuderia Valdieri" and not getattr(state, "valdieri_active", False):
            continue
        
        # Skip Enzoni if they've withdrawn (post-1950 tragedy)
        if team_name == "Enzoni" and getattr(state, "enzoni_withdrawn", False):
            continue
        
        # Current roster
        current_drivers = [d for d in drivers if d.get("constructor") == team_name]
        max_drivers = team_data.get("max_drivers", 2)
        needed = max_drivers - len(current_drivers)
        
        if needed <= 0:
            continue
        
        # Build candidate pool from Independents
        team_prestige = team_data.get("prestige", 0.0)
        candidates = []
        
        for d in drivers:
            if d.get("constructor") != "Independent":
                continue
            if state.player_driver is d:
                continue
            
            pace = d.get("pace", 0)
            cons = d.get("consistency", 0)
            fame = float(d.get("fame", 0))
            age = d.get("age", 40)
            
            # Scoring: pace + consistency primary, with some fame/youth interest
            # Higher prestige teams are pickier about pace
            youth_bonus = max(0, 38 - age) * 0.12
            prestige_factor = 1.0 + (team_prestige / 20.0)  # higher prestige = higher standards
            
            score = (
                pace * 1.25 * prestige_factor +
                cons * 1.00 +
                fame * 0.45 +
                youth_bonus
            )
            
            candidates.append((score, d))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        if not candidates:
            state.news.append(f"{team_name} search for replacements, but cannot secure a driver.")
            continue
        
        signed_names = []
        for _ in range(needed):
            if not candidates:
                break
            
            pick = candidates.pop(0)[1]
            pick["constructor"] = team_name
            signed_names.append(pick["name"])
            
            # Remove from candidate list
            candidates = [(s, drv) for (s, drv) in candidates if drv is not pick]
        
        if signed_names:
            if len(signed_names) == 1:
                state.news.append(
                    f"{team_name} respond to the market: they sign {signed_names[0]} to fill an empty seat."
                )
            else:
                names_str = " and ".join(signed_names) if len(signed_names) == 2 else ", ".join(signed_names)
                state.news.append(
                    f"{team_name} rebuild their lineup: they sign {names_str}."
                )


def maybe_refill_valdieri_drivers(state, time):
    """
    Legacy wrapper - now handled by maybe_refill_ai_teams.
    Kept for backward compatibility with existing calls.
    """
    maybe_refill_ai_teams(state, time)



def update_fame_after_race(finishers, fame_mult=1.0, race_name=None, season_week=None, year=None):
    """
    Fame:
      - NEW: all classified finishers gain a tiny amount (era-scaled)
      - podiums still matter most
      - era scaling dampens early decades
      - soft cap slows growth as fame rises
      - track fame_cap stops small events boosting already-known drivers
    """
    if year is None:
        year = 1947

    scale = era_fame_scale(year)

    # Track-specific fame cap (None = normal 0–5 behaviour)
    track_cap = None
    if race_name:
        from gmr.data import tracks  # local import to avoid circulars
        track_cap = tracks.get(race_name, {}).get("fame_cap", None)

    for pos, (d, _) in enumerate(finishers):
        # Prince Sagat's fame is fixed at 2 (royal celebrity status)
        if d.get("name") == "Prince Sagat":
            d["fame"] = 2.0
            continue
        
        old_fame = float(d.get("fame", 0.0))

        # If the event is capped and you're already "too known", it stops moving the needle
        if track_cap is not None and old_fame >= float(track_cap):
            continue

        # ------------------------------
        # NEW: baseline fame for finishing
        # ------------------------------
        # Small in 1947–51 because scale=0.35:
        # base_finish_gain becomes ~0.02ish per race before softcap.
        base_finish_gain = 0.08 * fame_mult  # tune: 0.04–0.08
        gain = base_finish_gain

        # ------------------------------
        # Podium bonuses (still the main fame driver)
        # ------------------------------
        if pos == 0:
            gain += 1.2 * fame_mult
        elif pos in (1, 2):
            gain += 0.75 * fame_mult

        # Era dampener
        gain *= scale

        # Soft cap (slows growth as fame rises)
        gain *= max(0.15, 1.0 - old_fame * 0.18)

        new_fame = old_fame + gain

        # Clamp globally
        new_fame = max(0.0, min(5.0, new_fame))

        # Clamp to track cap too, if present
        if track_cap is not None:
            new_fame = min(float(track_cap), new_fame)

        d["fame"] = round(new_fame, 2)



def update_driver_progress(state, finishers, time, xp_mult=1.0):
    """
    Handle XP gains and occasional stat increases for drivers.
    Returns: player_xp_gain (float)
    """
    player_xp_gain = 0.0

    for pos, (d, _) in enumerate(finishers):
        place = pos + 1

        # ------------------------------
        # NEW XP MODEL (finishers only)
        # ------------------------------
        # Baseline: seeing the flag matters (even P12)
        base_xp = 0.4

        # Position bonus: rewards better finishes, but still gives something downfield
        # P1: +0.50, P2: +0.45 ... P10: +0.05, P11+: +0.00
        pos_bonus = max(0.0, (11 - place) * 0.05)

        # Small extra sparkle for podiums/win (optional but feels good)
        podium_bonus = 0.0
        if place == 1:
            podium_bonus = 0.25
        elif place <= 3:
            podium_bonus = 0.15

        base_xp = base_xp + pos_bonus + podium_bonus

        dev_rate = float(d.get("development_rate", 1.0))
        xp_gain = base_xp * dev_rate * float(xp_mult)

        d["xp"] = d.get("xp", 0.0) + xp_gain

        # Track player gain for the debrief
        if state.player_driver is d:
            player_xp_gain += xp_gain

        # Try to convert XP into stat gains, but only before peak_age
        while d["xp"] >= 5.0:
            age = d.get("age")
            peak = d.get("peak_age")

            if age is None or peak is None:
                break

            # No further growth once you're at/over peak age
            if age >= peak:
                # Don't burn XP invisibly; keep it banked so it feels fair/clear
                if state.player_driver is d:
                    state.news.append(
                        f"{d['name']} is past their peak ({age} ≥ {peak}) — experience is banked but won’t convert into stat gains."
                    )
                break

            growth_stats = ["pace", "consistency", "wet_skill", "mechanical_sympathy"]
            candidates = [s for s in growth_stats if d.get(s, 0) < 10]

            if not candidates:
                if state.player_driver is d:
                    state.news.append(
                        f"{d['name']} can’t develop further — key skills are already maxed."
                    )
                break

            # NOW spend XP because we know we can improve something
            d["xp"] -= 5.0

            stat = random.choice(candidates)
            old_val = d.get(stat, 0)
            d[stat] = old_val + 1

            # If this is the player's driver, log a news item
            if state.player_driver is d:
                pretty_name = stat.replace("_", " ")
                state.news.append(
                    f"Over recent outings, {d['name']} seems sharper – "
                    f"{pretty_name} improves ({old_val} → {d[stat]})."
                )

    return player_xp_gain

def grant_participation_xp_for_dnfs(state, dnf_drivers, time, xp_mult=1.0):
    """
    Rule B: DNFs get participation XP only (no fame).
    Returns: player_xp_gain_extra (float)
    """
    player_xp_gain_extra = 0.0

    for d in dnf_drivers:
        base_xp = 0.1  # participation only
        dev_rate = d.get("development_rate", 1.0)
        xp_gain = base_xp * dev_rate * xp_mult

        d["xp"] = d.get("xp", 0.0) + xp_gain

        if state.player_driver is d:
            player_xp_gain_extra += xp_gain

        # Same conversion rules as update_driver_progress (but no result bonuses)
        while d["xp"] >= 5.0:
            d["xp"] -= 5.0

            age = d.get("age")
            peak = d.get("peak_age")
            if age is None or peak is None:
                break
            if age >= peak:
                break

            growth_stats = ["pace", "consistency", "wet_skill", "mechanical_sympathy"]
            candidates = [s for s in growth_stats if d.get(s, 0) < 10]
            if not candidates:
                break

            stat = random.choice(candidates)
            old_val = d.get(stat, 0)
            d[stat] = old_val + 1

            if state.player_driver is d:
                pretty_name = stat.replace("_", " ")
                state.news.append(
                    f"Despite the retirement, {d['name']} learns from the weekend – "
                    f"{pretty_name} improves ({old_val} → {d[stat]})."
                )

    return player_xp_gain_extra

def init_driver_careers():
    """
    Initialise hidden career fields for each driver:
      - age (from data, or a fallback)
      - peak_age (random per save)
      - decline_age (random per save)
      - xp / form scaffolding for future use

    This makes each save have different driver career curves.
    """
    for d in drivers:
        # Make sure we have an age – if missing, default to a late-30s old boy
        age = d.get("age")
        if age is None:
            age = random.randint(34, 42)
        d["age"] = age

        # ----- Roll peak_age / decline_age PER SAVE -----
        # Older drivers: peak now or very soon, decline quickly
        if age >= 40:
            peak_min = max(age - 1, 32)
            peak_max = age

        # Younger drivers: peak a bit later
        elif age <= 32:
            peak_min = age + 1
            peak_max = age + 4
   


        # Mid-30s: peak over the next couple of years
        else:
            peak_min = age
            peak_max = age + 2

        peak_age = random.randint(peak_min, peak_max)

        # Decline starts 3–7 years after peak (random per save)
        decline_age = peak_age + random.randint(3, 7)

        d["peak_age"] = peak_age
        d["decline_age"] = decline_age

        # ----- Future-proof fields (we'll use these in the yearly update) -----
        # XP: how much "career learning" they’ve banked
        if "xp" not in d:
            d["xp"] = 0.0

        # Form: short-term confidence streaks, etc. (hook for later)
        if "form" not in d:
            d["form"] = 0.0

        # Comfort in THIS car (player-facing). 0.0–10.0
        if "car_xp" not in d:
            d["car_xp"] = 0.0

def spawn_new_rookies(state, time):
    """
    At the end of each season, introduce new independent drivers
    into the global driver pool so the grid stays fresh.
    
    The number of rookies is based on:
    - Base number that increases slightly each year
    - Regional economic health (wealthy regions produce more drivers)
    - Motorsport culture (regions that love racing produce more talent)
    """
    year = time.year

    # Base number increases as sport grows
    if year <= 1948:
        base_rookies = 4
    elif year <= 1950:
        base_rookies = 5
    else:
        base_rookies = 6

    # Calculate bonus rookies based on regional economic and motorsport health
    bonus_rookies = 0
    
    # Import world economy data
    from gmr.world_economy import COUNTRIES
    
    # Group countries by their name pool region for rookie spawning
    region_pools = {
        "italian": ["Italy"],
        "french": ["France"],
        "germanic": ["Germany", "Switzerland"],
        "british": ["UK"],
        "iberian": ["Spain"],
        "brazilian": ["Brazil"],
        "argentinian": ["Argentina"],
    }
    
    # Calculate regional contribution to rookie pool
    regional_scores = {}
    for pool_name, countries in region_pools.items():
        total_score = 0
        for country_name in countries:
            country_data = COUNTRIES.get(country_name, {})
            
            # Get current economy (check if world_economy exists on state)
            if hasattr(state, 'world_economy'):
                economy = state.world_economy.get_current_economy(country_name)
            else:
                economy = country_data.get("base_economy", 5)
            
            motorsport = country_data.get("motorsport_culture", 5)
            
            # Score: economy * motorsport culture (wealthy racing-mad nations produce drivers)
            # Scale: economy 1-10, motorsport 1-10, so max 100 per country
            score = (economy * motorsport) / 10  # Normalize to 0-10 range
            total_score += score
        
        regional_scores[pool_name] = total_score
    
    # Add bonus rookies from high-performing regions
    # Threshold: score > 5 adds a chance for bonus rookie from that region
    for pool_name, score in regional_scores.items():
        if score > 5:
            # Higher score = higher chance of bonus rookie
            chance = (score - 5) * 0.15  # 6 score = 15%, 10 score = 75%
            if random.random() < chance:
                bonus_rookies += 1

    num_new = base_rookies + bonus_rookies

    if num_new <= 0:
        return

    # ------------------------------
    # ERA-APPROPRIATE NAME POOLS
    # ------------------------------
    NAME_POOLS = {
        "italian": {
            "first": [
                "Carlo", "Giuseppe", "Alberto", "Vittorio", "Enrico", "Luigi",
                "Gino", "Franco", "Sergio", "Paolo", "Bruno", "Antonio",
                "Mario", "Renato", "Piero", "Aldo", "Giancarlo", "Umberto",
                "Eugenio", "Nino", "Dorino", "Felice", "Consalvo", "Clemente",
                "Tazio", "Achille", "Silvio", "Gastone", "Onofre", "Ludovico",
            ],
            "last": [
                "Bianchi", "Conti", "De Luca", "Moretti", "Galli", "Marini",
                "Esposito", "Romano", "Colombo", "Serafini", "Barbieri",
                "Valenti", "Bernardi", "Ricci", "Ferretti", "Marchetti", "Venturi",
                "Mantovani", "Rossetti", "Benedetti", "Santini", "Carbone",
                "Pellegrini", "Lombardi", "Grasso", "De Angelis", "Morandi",
            ],
        },

        "french": {
            "first": [
                "Jean", "Pierre", "Henri", "Lucien", "Marcel", "Jacques",
                "Émile", "Roger", "Louis", "Georges", "André",
                "Armand", "Claude", "Yves", "Alain", "Raymond", "Maurice",
                "Robert", "Guy", "François", "Patrick", "Didier", "René",
                "Jean-Pierre", "Olivier", "Étienne",
            ],
            "last": [
                "Dubois", "Morel", "Lefèvre", "Lambert", "Renaud", "Girard",
                "Faure", "Perrin", "Marchand", "Chevalier",
                "Delattre", "Vandermonde", "Beaumont", "Moreau", "Fontaine",
                "Reynard", "Blanchard", "Garnier", "Rousseau", "Clement",
                "Beauchamp", "Lavigne", "Desmond", "Vaillant",
            ],
        },

        "germanic": {
            "first": [
                "Hans", "Karl", "Ernst", "Wilhelm", "Otto", "Friedrich",
                "Rudolf", "Heinz", "Kurt", "Franz", "Wolfgang", "Helmut",
                "Klaus", "Dieter", "Rolf", "Horst", "Manfred", "Gerhard",
                "Bernd", "Jochen", "Hubert", "Hermann",
            ],
            "last": [
                "Keller", "Schneider", "Weiss", "Bauer", "Klein",
                "Vogel", "Hartmann", "Neumann", "Hoffner", "Brandt",
                "Steiner", "Lorenz", "Lang", "Krause", "Zimmermann",
                "Hahn", "Gruber", "Maier", "Berger", "Wagner",
            ],
        },

        "british": {
            "first": [
                "John", "Jack", "Arthur", "Edward", "George", "Henry",
                "Ronald", "Stanley", "Frederick", "Albert",
                "Dennis", "Peter", "Norman", "Reginald", "Mike", "Graham",
                "Colin", "James", "Richard", "Nigel", "Derek",
                "Tony", "Bruce", "David", "William",
            ],
            "last": [
                "Hawkins", "Turner", "Collins", "Bennett", "Walker",
                "Thompson", "Mitchell", "Baker", "Ellis",
                "Harrison", "Caldwell", "Broome", "Pemberton", "Whitmore",
                "Crawford", "Ashby", "Barrington", "Thornton", "Weston", "Hartley",
                "Kingsley", "Marlowe", "Fairfax", "Chambers",
            ],
        },

        "iberian": {
            "first": [
                "Juan", "Miguel", "Carlos", "Luis", "Manuel", "Rafael",
                "Ángel", "Andrés", "Javier", "Pablo", "Tomás", "Vicente",
                "Alfonso", "Paco", "Pedro", "Antonio",
            ],
            "last": [
                "Navarro", "Morales", "Serrano", "Domínguez",
                "Carrasco", "Iglesias", "Velasco", "Cordero", "Aguilar",
                "Cabral", "Montero", "Herrera", "Sala", "Campos",
            ],
        },

        "brazilian": {
            "first": [
                "João", "Paulo", "Rubens", "Chico", "Sérgio", "Wilson",
                "Nelson", "Emerson", "Roberto", "Maurício", "Raul", "Clovis",
                "Carlos", "Luiz", "Pedro", "Antônio", "Ingo", "Cristiano",
            ],
            "last": [
                "Figueiredo", "Mendonça", "Almeida", "Ribeiro", "Silveira", "Cardoso",
                "Teixeira", "Ferreira", "Machado", "Bueno", "Leme", "Guimarães",
                "Nogueira", "Tavares", "Moreira", "Coutinho", "Meira", "Pinheiro",
            ],
        },

        "argentinian": {
            "first": [
                "Juan", "Carlos", "Fernando", "Héctor", "Raúl", "Oscar",
                "José", "Froilán", "Onofre", "Clemar", "Norberto", "Benedicto",
                "Roberto", "Ricardo", "Alejandro", "Gastón",
            ],
            "last": [
                "Ortega", "Ramos", "Sánchez", "Vidal", "González", "Gálvez",
                "Quiroga", "Acosta", "Perdomo", "Bordeu", "Leguizamón", "Medina",
                "Aguirre", "Romero", "Peralta", "Villanueva",
            ],
        },
    }

    existing = {d["name"] for d in drivers}
    created = []

    for i in range(num_new):
        # ------------------------------
        # Name generation (paired pools)
        # Weight pool selection by regional motorsport/economic score
        # ------------------------------
        # Build weighted pool selection
        pool_weights = []
        for pool_name in NAME_POOLS.keys():
            weight = regional_scores.get(pool_name, 5.0)
            pool_weights.append((pool_name, weight))
        
        # Weighted random selection
        total_weight = sum(w for _, w in pool_weights)
        roll = random.uniform(0, total_weight)
        cumulative = 0
        pool_key = list(NAME_POOLS.keys())[0]  # fallback
        for name, weight in pool_weights:
            cumulative += weight
            if roll <= cumulative:
                pool_key = name
                break
        
        pool = NAME_POOLS[pool_key]
        for _ in range(10):
            first = random.choice(pool["first"])
            last = random.choice(pool["last"])
            name = f"{first} {last}"
            if name not in existing:
                existing.add(name)
                break
        else:
            name = f"Rookie {year}-{i+1}"

        # Assign country based on pool
        country_map = {
            "italian": "Italy",
            "french": "France",
            "germanic": "Switzerland",  # or Germany, but Switzerland fits
            "british": "UK",
            "iberian": "Spain",  # or Portugal, but Spain fits
            "brazilian": "Brazil",
            "argentinian": "Argentina",
        }
        country = country_map.get(pool_key, "UK")  # default to UK

        # Era-appropriate regen age
        age = get_regen_age_for_year(year)

        # ------------------------------
        # Stat generation (nerfed rookies)
        # ------------------------------
        pace = random.randint(2, 6)
        consistency = random.randint(2, 5)
        aggression = random.randint(2, 6)
        mech = random.randint(2, 4)
        wet = random.randint(2, 4)

        # Fame: mostly nobodies in the 40s
        if year <= 1950:
            fame = random.choice([0, 0, 0, 1])
        else:
            fame = random.choice([0, 0, 1, 1, 2])

        rookie = {
            "name": name,
            "constructor": "Independent",
            "pace": pace,
            "consistency": consistency,
            "aggression": aggression,
            "mechanical_sympathy": mech,
            "wet_skill": wet,
            "fame": fame,
            "age": age,
            "country": country,
            "car_xp": 0.0
        }

        # ------------------------------
        # Career curve (peak / decline)
        # ------------------------------
        if age >= 40:
            peak_min = max(age - 1, 32)
            peak_max = age
        elif age <= 32:
            peak_min = age + 1
            peak_max = age + 4
        else:
            peak_min = age
            peak_max = age + 2

        peak_age = random.randint(peak_min, peak_max)
        decline_age = peak_age + random.randint(3, 7)

        rookie["peak_age"] = peak_age
        rookie["decline_age"] = decline_age
        rookie["xp"] = 0.0
        rookie["form"] = 0.0

        drivers.append(rookie)
        created.append(rookie)

    for r in created:
        state.news.append(
            f"New face in the paddock for {time.year}: {r['name']}, "
            f"an independent hopeful."
        )


def offseason_fame_decay(time):
    for d in drivers:
        fame = float(d.get("fame", 0.0))

        # Early era: reputations are more local/fragile
        if time.year <= 1951:
            decay = 0.25
        else:
            decay = 0.15

        # Winners don’t fade as fast (optional hook if you track form/results)
        # decay *= 0.8

        d["fame"] = round(max(0.0, fame - decay), 2)


def apply_offseason_ageing_and_retirement(state, time):
    """
    End-of-season pass:
      - age all drivers by 1
      - apply stat decline after peak (gentle) and after decline_age (stronger)
      - random retirement for the oldest drivers

    Uses era-based retirement bands to keep old boys around longer in the 40s.
    """
    state.news.append("Offseason: drivers age up and the market reshuffles.")

    soft_retire, hard_retire = get_retirement_ages_for_year(time.year)
    retired = []

    for d in list(drivers):
        age = d.get("age")
        if age is None:
            continue

        # -------------------------
        # Age up
        # -------------------------
        age += 1
        d["age"] = age

        peak_age = d.get("peak_age")
        decline_age = d.get("decline_age")

        # Fallbacks if missing
        if peak_age is None:
            peak_age = age + 2
            d["peak_age"] = peak_age
        if decline_age is None:
            decline_age = peak_age + 3
            d["decline_age"] = decline_age

        # -------------------------
        # Stat decline chance
        # -------------------------
        if age > peak_age and age < decline_age:
            # Gentle “plateau fade”
            decline_chance = 0.08
        elif age >= decline_age:
            # Accelerating decline
            if age < soft_retire:
                decline_chance = 0.12
            elif age < hard_retire:
                decline_chance = 0.30
            else:
                decline_chance = 0.55
        else:
            decline_chance = 0.0

        # Actually APPLY the decline
        if decline_chance > 0:
            ageing_stats = [
                "pace",
                "consistency",
                "aggression",
                "mechanical_sympathy",
                "wet_skill",
            ]

            for key in ageing_stats:
                if key not in d:
                    continue
                if d[key] <= 1:
                    continue

                if random.random() < decline_chance:
                    old_val = d[key]
                    d[key] = max(1, d[key] - 1)

                    # If it's your driver, tell you
                    if state.player_driver is d and old_val != d[key]:
                        pretty_name = key.replace("_", " ")
                        state.news.append(
                            f"Over the winter, {d['name']} seems to lose a touch of {pretty_name} "
                            f"({old_val} → {d[key]})."
                        )

        # -------------------------
        # Retirement chance
        # -------------------------
        retire_prob = 0.0
        fame = d.get("fame", 0)

        if age >= hard_retire + 5:
            retire_prob = 0.60
        elif age >= hard_retire:
            retire_prob = 0.35
        elif age >= soft_retire:
            retire_prob = 0.12

        # Famous drivers cling on slightly longer
        if fame >= 4 and age < hard_retire + 3:
            retire_prob *= 0.5

        if retire_prob > 0 and random.random() < retire_prob:
            retired.append(d)

    # -------------------------
    # Apply retirements
    # -------------------------
    for d in retired:
        if d in drivers:
            drivers.remove(d)

        name = d["name"]
        fame = d.get("fame", 0)
        fame_label = describe_driver_fame(fame)

        if state.player_driver is d:
            team_name = state.player_constructor or "your team"
            state.player_driver = None
            state.driver_pay = 0
            state.driver_contract_races = 0
            state.news.append(
                f"After many seasons, {name} retires from racing, bringing their time with {team_name} to an end."
            )
        else:
            state.news.append(
                f"Long-time {fame_label.lower()} {name} hangs up their helmet and retires from the sport."
            )

    state.news.append(f"Offseason report: {len(retired)} retirement(s).")



def maybe_expand_enzoni_to_three_cars(state, time):
    """
    In 1950, Enzoni expands to 3 cars by signing a driver from the market.
    Enzoni are aggressive:
      - They prioritise raw pace and consistency
      - They will poach from Valdieri without hesitation
      - They can steal the player's driver if they are clearly strong
    """
    if time.year < 1950:
        return

    enzoni_drivers = [d for d in drivers if d.get("constructor") == "Enzoni"]
    if len(enzoni_drivers) >= 3:
        return

    # Enzoni hiring mentality: WIN NOW
    def score(d):
        pace = d.get("pace", 0)
        cons = d.get("consistency", 0)
        mech = d.get("mechanical_sympathy", 0)
        fame = float(d.get("fame", 0.0))

        # Heavy emphasis on speed + reliability of performance
        s = (
            pace * 1.6 +
            cons * 1.4 +
            mech * 0.3 +
            fame * 0.35
        )

        # Slight political friction if stealing YOUR driver (still very possible)
        if state.player_driver is d:
            s -= 0.8

        return s

    candidates = []
    for d in drivers:
        ctor = d.get("constructor")

        # Never steal from Test or duplicate Enzoni
        if ctor in ("Enzoni", "Test"):
            continue

        # Everyone else is fair game: Independent, Valdieri, even the player
        candidates.append(d)

    if not candidates:
        return

    pick = max(candidates, key=score)

    # Gate stealing the player driver so it feels dramatic, not constant
    if state.player_driver is pick:
        pace = pick.get("pace", 0)
        cons = pick.get("consistency", 0)
        fame = float(pick.get("fame", 0.0))

        # Lower threshold than before – Enzoni are ruthless in 1950
        if (pace + cons) < 12 and fame < 2.0:
            return  # not quite worth the fallout

    old_team = pick.get("constructor", "Independent")
    pick["constructor"] = "Enzoni"

    if old_team == "Valdieri":
        state.news.append(
            f"Power move for 1950: Enzoni poach {pick['name']} from Valdieri to complete a three-car assault."
        )
    elif state.player_driver is pick:
        team_name = state.player_constructor or "your team"
        state.player_driver = None
        state.driver_pay = 0
        state.driver_contract_races = 0
        state.news.append(
            f"Paddock bombshell: Enzoni lure {pick['name']} away from {team_name} with a lucrative 1950 offer."
        )
    else:
        state.news.append(
            f"Enzoni expand to a three-car operation for 1950, signing {pick['name']} to strengthen their ranks."
        )


def maybe_release_surviving_enzoni_driver(state, time):
    """
    At the start of 1951, if the demo finale has occurred (an Enzoni driver died),
    the surviving Enzoni driver becomes available on the driver market.
    
    They remain an Enzoni driver but are marked as 'hirable' so they appear
    in the driver market menu alongside other drivers.
    """
    if time.year != 1951:
        return
    
    # Only trigger if the demo finale has occurred
    if not getattr(state, "demo_driver_death_done", False):
        return
    
    # Only do this once
    if getattr(state, "enzoni_driver_unlocked", False):
        return
    
    # Find remaining Enzoni drivers and mark them as hirable
    enzoni_drivers = [d for d in drivers if d.get("constructor") == "Enzoni"]
    
    for driver in enzoni_drivers:
        driver["hirable"] = True
        state.news.append(
            f"After the tragedy at Ardennes, {driver['name']} has indicated he may consider "
            f"offers from other teams. Enzoni's factory program remains uncertain."
        )
    
    state.enzoni_driver_unlocked = True


def show_driver_profile(state, driver):
    """
    Show detailed career profile for a driver.
    Returns 'hire' if user wants to hire, 'back' otherwise.
    """
    name = driver.get("name", "Unknown")
    
    while True:
        print("\n" + "=" * 60)
        print(f"  DRIVER PROFILE: {name.upper()}")
        print("=" * 60)
        
        # Basic info
        age = driver.get("age", "?")
        country = driver.get("country", "Unknown")
        constructor = driver.get("constructor", "Independent")
        fame = driver.get("fame", 0)
        
        print(f"\n  Age: {age}  |  Country: {country}  |  Fame: {fame}")
        print(f"  Current Team: {constructor}")
        print(f"  Career Stage: {describe_career_phase(driver)}")
        
        # Skills
        print("\n  --- SKILLS ---")
        print(f"  Pace: {driver.get('pace', '?')}/10")
        print(f"  Consistency: {driver.get('consistency', '?')}/10")
        print(f"  Aggression: {driver.get('aggression', '?')}/10")
        print(f"  Mechanical Sympathy: {driver.get('mechanical_sympathy', '?')}/10")
        print(f"  Wet Skill: {driver.get('wet_skill', '?')}/10")
        
        # Career stats from driver_histories
        history = None
        if hasattr(state, 'driver_histories') and state.driver_histories:
            history = state.driver_histories.get(name)
        
        if history:
            summary = history.get_career_summary()
            
            print("\n  --- CAREER STATISTICS ---")
            print(f"  Seasons: {summary['years_active']}  |  Starts: {summary['starts']}")
            print(f"  Wins: {summary['wins']}  |  Podiums: {summary['podiums']}  |  DNFs: {summary['dnfs']}")
            print(f"  Total Points: {summary['points']}  |  Prize Money: £{summary['prize_money']:,}")
            
            if summary['best_finish']:
                print(f"  Best Finish: P{summary['best_finish']}")
            
            if summary['championships'] > 0:
                print(f"  🏆 CHAMPIONSHIPS: {summary['championships']}")
            elif summary['best_championship']:
                print(f"  Best Championship: P{summary['best_championship']}")
            
            # Streaks
            best_win_streak = summary.get('best_win_streak', 0)
            best_podium_streak = summary.get('best_podium_streak', 0)
            if best_win_streak > 1:
                print(f"  Best Win Streak: {best_win_streak}")
            if best_podium_streak > 2:
                print(f"  Best Podium Streak: {best_podium_streak}")
            
            # Team history
            if history.team_history:
                print("\n  --- TEAM HISTORY ---")
                for stint in history.team_history:
                    years = f"{stint['start_year']}"
                    if stint['end_year'] and stint['end_year'] != stint['start_year']:
                        years += f"-{stint['end_year']}"
                    elif stint['end_year'] is None:
                        years += "-present"
                    
                    print(f"  {stint['constructor']} ({years})")
                    print(f"    Races: {stint['races']}  |  Wins: {stint['wins']}  |  Points: {stint['points']}")
            
            # Awards
            if history.awards:
                print("\n  --- AWARDS & ACHIEVEMENTS ---")
                for award in history.awards:
                    print(f"  🏆 {award['year']}: {award['award_type']} - {award['details']}")
            
            # Season-by-season
            if history.seasons:
                print("\n  --- SEASON RESULTS ---")
                for year in sorted(history.seasons.keys(), reverse=True)[:5]:  # Last 5 seasons
                    s = history.seasons[year]
                    champ_pos = s.get('championship_position', '-')
                    print(f"  {year}: {s['wins']}W/{s['podiums']}P in {s['starts']} races | "
                          f"{s['points']} pts | Champ: P{champ_pos} | {s['constructor']}")
        else:
            # No history yet (new to racing or early game)
            print("\n  --- CAREER STATISTICS ---")
            print("  No race results recorded yet.")
            
            # Check legacy stats
            legacy = state.driver_career.get(name) if hasattr(state, 'driver_career') else None
            if legacy and legacy.get('starts', 0) > 0:
                print(f"  (Legacy data: {legacy['starts']} starts, {legacy['wins']} wins, {legacy['podiums']} podiums)")
        
        # Menu
        print("\n" + "-" * 40)
        print("  1. Hire this driver")
        print("  2. View recent race results")
        print("  3. Back to driver list")
        
        choice = input("\n> ").strip()
        
        if choice == "1":
            return "hire"
        elif choice == "2":
            show_driver_race_history(state, driver)
        elif choice == "3" or choice == "":
            return "back"
        else:
            print("Invalid choice.")


def show_driver_race_history(state, driver):
    """Show detailed race-by-race results for a driver."""
    name = driver.get("name", "Unknown")
    
    history = None
    if hasattr(state, 'driver_histories') and state.driver_histories:
        history = state.driver_histories.get(name)
    
    if not history or not history.race_results:
        print("\n  No race results recorded for this driver.")
        input("\n  Press Enter to continue...")
        return
    
    print("\n" + "=" * 60)
    print(f"  RACE HISTORY: {name.upper()}")
    print("=" * 60)
    
    # Show results grouped by year, most recent first
    results_by_year = {}
    for r in history.race_results:
        year = r['year']
        if year not in results_by_year:
            results_by_year[year] = []
        results_by_year[year].append(r)
    
    for year in sorted(results_by_year.keys(), reverse=True):
        print(f"\n  === {year} ===")
        
        # Season summary
        if year in history.seasons:
            s = history.seasons[year]
            print(f"  Season: {s['wins']}W/{s['podiums']}P from {s['starts']} starts | {s['points']} pts")
        
        for r in results_by_year[year]:
            conditions = ""
            if r['wet']:
                conditions = " 🌧️"
            elif r['hot']:
                conditions = " ☀️"
            
            if r['dnf']:
                reason_emoji = "💥" if r['dnf_reason'] == "crash" else "🔧"
                print(f"  Week {r['week']:2}: {r['race']:<30} DNF ({r['dnf_reason']}) {reason_emoji}{conditions}")
            else:
                pos = r['position']
                pos_str = f"P{pos}"
                if pos == 1:
                    pos_str = "🥇 P1"
                elif pos == 2:
                    pos_str = "🥈 P2"
                elif pos == 3:
                    pos_str = "🥉 P3"
                
                pts_str = f"+{r['points']}pts" if r['points'] > 0 else ""
                print(f"  Week {r['week']:2}: {r['race']:<30} {pos_str:8} {pts_str:8} ({r['constructor']}){conditions}")
    
    input("\n  Press Enter to continue...")


def show_driver_market(state):
    while True:
        print("\n=== Driver Market ===")

        # Show current driver
        if state.player_driver:
            d = state.player_driver
            fame = d.get("fame", 0)
            age = d.get("age", "?")

            print("Current Driver:")
            print(f"   Name: {d['name']}")
            print(f"   Age: {age}  Country: {d.get('country', 'Unknown')}")
            print(f"   Pace: {d['pace']}  Consistency: {d['consistency']}")
            print(
                f"   Aggression: {d['aggression']}  "
                f"Mech Sympathy: {d['mechanical_sympathy']}  "
                f"Wet Skill: {d['wet_skill']}"
            )
            print(f"   Fame: {fame} ({describe_driver_fame(fame)})")
            print(f"   Career stage: {describe_career_phase(d)}")
            print(f"   Racing for: {d['constructor']}")
            print(f"   Car comfort: {d.get('car_xp', 0.0):.1f}/10")
            
            # Show injury status
            if getattr(state, 'player_driver_injured', False) and getattr(state, 'player_driver_injury_weeks_remaining', 0) > 0:
                weeks_remaining = getattr(state, 'player_driver_injury_weeks_remaining', 0)
                severity = getattr(state, 'player_driver_injury_severity', 0)
                severity_desc = {1: "minor", 2: "serious", 3: "career-ending"}.get(severity, "unknown")
                print(f"   ⚠️  INJURED: {severity_desc} injury, {weeks_remaining} week{'s' if weeks_remaining != 1 else ''} remaining")

        else:
            print("Current Driver: None hired")

        # Build market list: all non-Enzoni / non-Test drivers
        # Exception: Enzoni drivers marked as "hirable" (e.g., surviving driver after 1950 tragedy)
        market_drivers = [
            d for d in drivers
            if d["constructor"] not in ("Enzoni", "Test") or d.get("hirable")
        ]

        print("\nAvailable Drivers:")
        for idx, d in enumerate(market_drivers, start=1):
            marker = ""
            if state.player_driver is d:
                marker = " [CURRENT]"

            age = d.get("age", "?")
            fame = float(d.get("fame", 0.0))
            fame_label = describe_driver_fame(fame)
            career_stage = describe_career_phase(d)

            print(f"{idx}. {d['name']}{marker}")
            print(f"   Age: {age}  Fame: {fame} ({fame_label})")
            print(f"   Career: {career_stage}")
            print(f"   Country: {d.get('country', 'Unknown')}")
            print(f"   Pace: {d['pace']}  Consistency: {d['consistency']}")
            print(
                f"   Aggression: {d['aggression']}  "
                f"Mech Sympathy: {d['mechanical_sympathy']}  "
                f"Wet Skill: {d['wet_skill']}"
            )
            print(f"   Registered constructor: {d['constructor']}")

        print("\n" + "-" * 40)
        print("Options:")
        print("  [number] - View driver profile / hire")
        print("  [Enter]  - Back to main menu")
        
        choice = input("\n> ").strip()

        if choice == "":
            return  # back to main menu

        if not choice.isdigit():
            print("Invalid input.")
            continue

        idx = int(choice)
        if idx < 1 or idx > len(market_drivers):
            print("Invalid driver selection.")
            continue

        selected_driver = market_drivers[idx - 1]
        
        # Show driver profile with options
        action = show_driver_profile(state, selected_driver)
        
        if action != "hire":
            continue  # Back to market list

        # --- Prince Sagat is unhirable (gentleman driver, races for himself) ---
        if selected_driver.get("name") == "Prince Sagat" or selected_driver.get("gentleman_driver"):
            print(f"\n{selected_driver['name']} politely declines your offer.")
            print("As a gentleman driver, he races purely for the love of the sport")
            print("and has no interest in driving for another team.")
            input("\nPress Enter to return to the Driver Market...")
            continue

        # --- Fame/team prestige gate: some drivers won't sign for small teams ---
        can_sign, required_prestige, rejection_reason = can_team_sign_driver(state, selected_driver)
        if not can_sign:
            fame = selected_driver.get("fame", 0)
            current_team = selected_driver.get("constructor", "Independent")
            
            if rejection_reason == "team":
                # Driver is at a bigger team - harder to poach
                print(f"\n{selected_driver['name']} is happy at {current_team}.")
                print(f"Why would they leave a team with prestige {required_prestige - 3:.1f} for yours?")
                print(f"  Your team prestige: {state.prestige:.1f}")
                print(f"  Required to poach: {required_prestige:.1f}+")
                print("You'll need to build a significantly more prestigious team to lure them away.")
            else:
                # Fame-based rejection
                print(f"\n{selected_driver['name']} and their backers don't believe your team is ready yet.")
                print(f"  Their fame: {fame}")
                print(f"  Your team prestige: {state.prestige:.1f}")
                print(f"  They'd expect a team with at least {required_prestige:.1f} prestige.")
                print("Put in stronger results or build more reputation before approaching them again.")
            
            input("\nPress Enter to return to the Driver Market...")
            continue

        # --- Check if you already have a driver (one-car team limit) ---
        if state.player_driver and state.player_driver != selected_driver:
            current_driver = state.player_driver
            races_remaining = getattr(state, 'driver_contract_races', 0)
            pay_per_race = getattr(state, 'driver_pay', 0)
            
            print(f"\n⚠️  You already have {current_driver['name']} under contract!")
            print(f"   Races remaining: {races_remaining}")
            print(f"   Pay per race: £{pay_per_race}")
            
            if races_remaining > 0:
                buyout_cost = races_remaining * pay_per_race
                print(f"\nTo sign {selected_driver['name']}, you must buy out {current_driver['name']}'s contract.")
                print(f"Buyout cost: £{buyout_cost} (remaining contract value)")
                print(f"Your funds: £{state.money}")
                
                if state.money < buyout_cost:
                    print("\n❌ You cannot afford the buyout!")
                    input("\nPress Enter to return to the Driver Market...")
                    continue
                
                confirm_buyout = input(f"\nPay £{buyout_cost} to release {current_driver['name']}? (y/n): ").strip().lower()
                if confirm_buyout != "y":
                    print("You decide to keep your current driver.")
                    input("\nPress Enter to return to the Driver Market...")
                    continue
                
                # Process buyout
                state.money -= buyout_cost
                state.last_week_outgoings += buyout_cost
                state.last_week_purchases += buyout_cost
                print(f"\n✓ {current_driver['name']} has been released from their contract.")
                print(f"   Buyout paid: £{buyout_cost}")
                
                # Release driver back to independent
                current_driver["constructor"] = "Independent"
                state.player_driver = None
                state.driver_contract_races = 0
                state.driver_pay = 0
            else:
                # Contract expired, just release them
                print(f"\n{current_driver['name']}'s contract has expired.")
                current_driver["constructor"] = "Independent"
                state.player_driver = None
                state.driver_contract_races = 0
                state.driver_pay = 0

        # Ask how many races you want to hire them for
        while True:
            races_str = input(
                f"\nHow many races do you want to hire {selected_driver['name']} for? "
                "(enter a number, e.g. 2–8): "
            ).strip()

            if not races_str.isdigit():
                print("Please enter a valid number.")
                continue

            races = int(races_str)
            if races <= 0:
                print("Contract must be at least 1 race.")
                continue

            # Clamp to something sensible for the early era / demo
            if races > 12:
                print("That's a bit long for this era. Let's keep it to 12 races or fewer.")
                continue

            break

        # Calculate pay-per-race based on stats + fame
        stat_sum = (
            selected_driver["pace"]
            + selected_driver["consistency"]
            + selected_driver["aggression"]
            + selected_driver["mechanical_sympathy"]
            + selected_driver["wet_skill"]
        )
        fame = selected_driver.get("fame", 0)

        base_pay = stat_sum * 2  # skill-based base
        fame_factor = 1 + fame * 0.10  # each fame point makes them ~10% pricier
        pay_per_race = int(base_pay * fame_factor)

        total_contract_cost = pay_per_race * races

        print(f"\nProposed contract for {selected_driver['name']}:")
        print(f"  Length: {races} race(s)")
        print(f"  Pay per race: £{pay_per_race}")
        print(f"  Total over contract: £{total_contract_cost}")
        confirm = input("Confirm this contract? (y/n): ").strip().lower()

        if confirm != "y":
            print("You decide not to sign this contract.")
            input("\nPress Enter to return to the Driver Market...")
            continue

        # Hire / assign to your team
        state.player_driver = selected_driver
        selected_driver["constructor"] = state.player_constructor  # now races for your company

        state.driver_contract_races = races
        state.driver_pay = pay_per_race

        # Reset career stats for the new lead driver with this team
        state.races_entered_with_team = 0
        state.wins_with_team = 0
        state.podiums_with_team = 0
        state.points_with_team = 0

        # Tiny fame bump for joining a reputable outfit (one-time press attention)
        if state.prestige >= 3.0 and fame < 2.0:
            before_fame = float(selected_driver.get("fame", 0.0))
            bump = min(0.15, state.prestige * 0.02)  # capped small
            selected_driver["fame"] = round(min(5.0, before_fame + bump), 2)


        # --- Instant prestige bump from hiring a name driver ---
        if fame > 0:
            before = state.prestige
            # Small but noticeable bump – scales with fame, but not insane
            boost = fame * 0.4
            state.prestige = max(0.0, min(100.0, state.prestige + boost))

            team_name = state.player_constructor or "Your team"
            state.news.append(
                f"Signing {selected_driver['name']} creates a stir in the paddock – "
                f"{team_name}'s prestige rises ({before:.1f} → {state.prestige:.1f})."
            )

        print(f"\nContract signed: {selected_driver['name']} will race the next {state.driver_contract_races} events.")
        print(f"Driver cost per race: £{state.driver_pay}")
        print(f"Total contract value (if all races are run): £{total_contract_cost}")

        print(f"\nYou have hired {selected_driver['name']} as your driver.")
        print(f"They will now race for {state.player_constructor}.")

        # Check if any AI teams need to refill after losing this driver
        maybe_refill_ai_teams(state, time)

        input("\nPress Enter to return to the main menu...")
        return

def describe_driver_fame(fame: float) -> str:
    """
    Fame is a 0.0–5.0 float.
    These labels are UI only.
    """
    if fame < 1.0:
        return "Unknown privateer"
    elif fame < 2.0:
        return "Locally known"
    elif fame < 3.0:
        return "Known in the paddock"
    elif fame < 4.0:
        return "Respected contender"
    else:
        return "International name"



def warn_if_contract_last_race(state):
    """
    If your driver is entering the final race of their contract,
    add a news item to warn you at the start of the week.
    """
    if not state.player_driver:
        return

    races_left = getattr(state, "driver_contract_races", 0)
    if races_left != 1:
        return

    d = state.player_driver
    team_name = state.player_constructor or "your team"
    state.news.append(
        f"Contract reminder: {d['name']}'s deal with {team_name} ends after this race."
    )


def maybe_offer_driver_extension(state, time):
    """
    When a driver's race-count contract expires, give the player a chance
    to offer a new race deal instead of losing them automatically.

    Returns True if an extension was signed, False otherwise.
    """
    if not state.player_driver:
        return False

    d = state.player_driver
    team_name = state.player_constructor or "your team"

    print(f"\n{d['name']}'s current race contract has expired.")
    choice = input(
        f"Do you want to try to re-sign {d['name']} for more races with {team_name}? (y/n): "
    ).strip().lower()

    if choice != "y":
        # ✅ HARD CLEANUP HERE so we can’t ever “say they left” but keep them
        print(f"\nYou part ways with {d['name']} at the end of the weekend.")
        state.news.append(f"{d['name']}'s contract expires — they leave {team_name}.")
        d["constructor"] = "Independent"

        state.player_driver = None
        state.driver_pay = 0
        state.driver_contract_races = 0
        return False

    # Ask for number of races on the new deal
    while True:
        races_str = input("How many races do you want this new contract to cover? (e.g. 2–8): ").strip()
        if not races_str.isdigit():
            print("Please enter a whole number.")
            continue
        races = int(races_str)
        if races <= 0:
            print("Contract must be at least 1 race.")
            continue
        if races > 12:
            print("That's a bit much for this era. Let's cap it at 12.")
            continue
        break

    # Recalculate pay-per-race
    stat_sum = (
        d["pace"]
        + d["consistency"]
        + d["aggression"]
        + d["mechanical_sympathy"]
        + d["wet_skill"]
    )
    fame = d.get("fame", 0)

    base_pay = stat_sum * 2
    fame_factor = 1 + fame * 0.10
    new_pay_per_race = int(base_pay * fame_factor * 1.05)

    print(f"\nProposed extension for {d['name']}:")
    print(f"  Length: {races} race(s)")
    print(f"  Pay per race: £{new_pay_per_race}")
    confirm = input("Agree this new deal? (y/n): ").strip().lower()
    if confirm != "y":
        # ✅ also treat “no” here as leaving
        print("You shake hands and part ways.")
        state.news.append(f"{d['name']}'s contract expires — they leave {team_name}.")
        d["constructor"] = "Independent"

        state.player_driver = None
        state.driver_pay = 0
        state.driver_contract_races = 0
        return False

    # Lock in extension
    state.driver_contract_races = races
    state.driver_pay = new_pay_per_race
    d["constructor"] = team_name

    print(f"\n{d['name']} agrees to stay with {team_name} for another {races} races.")
    state.news.append(f"{d['name']} signs a new {races}-race deal to stay with {team_name}.")

    fame_boost = max(0, fame) * 0.2
    before = state.prestige
    state.prestige = min(100.0, state.prestige + fame_boost)
    if fame_boost > 0:
        state.news.append(
            f"Keeping {d['name']} onboard boosts {team_name}'s standing "
            f"(prestige {before:.1f} → {state.prestige:.1f})."
        )

    return True
