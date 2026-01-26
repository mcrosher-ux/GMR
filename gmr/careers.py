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

def tick_driver_contract_after_race_start(state, time):
    """
    Decrement contract length by 1 for any race the player entered.
    If it expires, offer extension; if refused, release driver.
    """
    if not state.player_driver:
        return

    if getattr(state, "driver_contract_races", 0) <= 0:
        return

    # decrement once per race entered
    state.driver_contract_races -= 1

    # expired -> offer extension
    if state.driver_contract_races <= 0:
        extended = maybe_offer_driver_extension(state, time)

        # ✅ IMPORTANT:
        # maybe_offer_driver_extension() now handles the "driver leaves" cleanup itself.
        # So if not extended, do NOT try to log or touch the driver here.
        if not extended:
            return

def tick_driver_contract_after_race_end(state, time, started_race: bool):
    """
    Decrement contract length by 1 ONLY after the race weekend is complete,
    and ONLY if the player actually started the race.

    If it expires, offer extension; if refused, release driver AFTER the race.
    """
    if not state.player_driver:
        return

    if not started_race:
        return

    if getattr(state, "driver_contract_races", 0) <= 0:
        return

    # decrement once per race started
    state.driver_contract_races -= 1

    # expired -> offer extension
    if state.driver_contract_races <= 0:
        extended = maybe_offer_driver_extension(state, time)
        if not extended:
            # maybe_offer_driver_extension() handles cleanup + setting to Independent
            return



def maybe_refill_valdieri_drivers(state, time):
    """
    If Valdieri is active but has fewer than 2 drivers (poached / retired),
    they sign replacements from the Independent pool.
    """

    team = "Scuderia Valdieri"

    # Only after they've arrived in the world
    if not getattr(state, "valdieri_active", False):
        return

    # Current Valdieri roster
    valdieri_drivers = [d for d in drivers if d.get("constructor") == team]
    needed = 2 - len(valdieri_drivers)

    if needed <= 0:
        return

    # Candidate pool: Independent only (don't steal player)
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

        # Valdieri mentality:
        # - Pace + consistency still king
        # - Youth bias (but not too strong)
        # - SOME fame interest (headline value / sponsorship attention)
        youth_bonus = max(0, 38 - age) * 0.12

        s = (
            pace * 1.25 +
            cons * 1.00 +
            fame * 0.45 +
            youth_bonus
        )

        candidates.append((s, d))

    candidates.sort(key=lambda x: x[0], reverse=True)

    if not candidates:
        state.news.append(f"{team} search for replacements, but cannot secure a driver.")
        return

    signed_names = []
    for _ in range(needed):
        if not candidates:
            break

        pick = candidates.pop(0)[1]
        old_team = pick.get("constructor", "Independent")
        pick["constructor"] = team
        signed_names.append(pick["name"])

        # Remove duplicates of the same object if they exist
        candidates = [(s, drv) for (s, drv) in candidates if drv is not pick]

    if signed_names:
        if len(signed_names) == 1:
            state.news.append(
                f"{team} respond to the market: they sign {signed_names[0]} to fill an empty seat."
            )
        else:
            state.news.append(
                f"{team} rebuild their lineup: they sign {signed_names[0]} and {signed_names[1]}."
            )



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
        old_fame = float(d.get("fame", 0.0))

        # If the event is capped and you're already "too known", it stops moving the needle
        if track_cap is not None and old_fame >= float(track_cap):
            continue

        # ------------------------------
        # NEW: baseline fame for finishing
        # ------------------------------
        # Small in 1947–51 because scale=0.35:
        # base_finish_gain becomes ~0.02ish per race before softcap.
        base_finish_gain = 0.06 * fame_mult  # tune: 0.04–0.08
        gain = base_finish_gain

        # ------------------------------
        # Podium bonuses (still the main fame driver)
        # ------------------------------
        if pos == 0:
            gain += 1.0 * fame_mult
        elif pos in (1, 2):
            gain += 0.6 * fame_mult

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
    At the end of each season, introduce a few new independent drivers
    into the global driver pool so the grid stays fresh.
    """
    year = time.year

    # How many new faces per year (early era is still fairly small)
    if year == 1947:
        num_new = 4
    elif year == 1948:
        num_new = 4
    else:
        num_new = 2

      


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
                "Mario", "Renato", "Piero", "Aldo",
            ],
            "last": [
                "Bianchi", "Conti", "De Luca", "Moretti", "Galli", "Marini",
                "Esposito", "Romano", "Colombo", "Serafini", "Barbieri",
                "Valenti", "Bernardi", "Ricci", "Ferretti",
            ],
        },

        "french": {
            "first": [
                "Jean", "Pierre", "Henri", "Lucien", "Marcel", "Jacques",
                "Émile", "Roger", "Louis", "Georges", "André",
                "Armand", "Claude",
            ],
            "last": [
                "Dubois", "Morel", "Lefèvre", "Lambert", "Renaud", "Girard",
                "Faure", "Perrin", "Marchand", "Chevalier",
                "Delattre", "Vandermonde",
            ],
        },

        "germanic": {
            "first": [
                "Hans", "Karl", "Ernst", "Wilhelm", "Otto", "Friedrich",
                "Rudolf", "Heinz", "Kurt", "Franz",
            ],
            "last": [
                "Keller", "Schneider", "Weiss", "Bauer", "Klein",
                "Vogel", "Hartmann", "Neumann", "Hoffner", "Brandt",
            ],
        },

        "british": {
            "first": [
                "John", "Jack", "Arthur", "Edward", "George", "Henry",
                "Ronald", "Stanley", "Frederick", "Albert",
                "Dennis", "Peter", "Norman",
            ],
            "last": [
                "Hawkins", "Turner", "Collins", "Bennett", "Walker",
                "Thompson", "Mitchell", "Baker", "Ellis",
                "Harrison", "Caldwell", "Broome",
            ],
        },

        "iberian": {
            "first": [
                "Juan", "Miguel", "Carlos", "Luis", "Manuel", "Rafael",
            ],
            "last": [
                "Navarro", "Morales", "Serrano", "Domínguez",
                "Carrasco", "Iglesias",
            ],
        },
    }

    existing = {d["name"] for d in drivers}
    created = []

    for i in range(num_new):
        # ------------------------------
        # Name generation (paired pools)
        # ------------------------------
        pool_key = random.choice(list(NAME_POOLS.keys()))
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
        market_drivers = [
            d for d in drivers
            if d["constructor"] not in ("Enzoni", "Test")
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

        choice = input("\nEnter the number of a driver to hire, or press Enter to go back: ").strip()

        if choice == "":
            return  # back to main menu

        if not choice.isdigit():
            print("Invalid input. No hiring done.")
            return

        idx = int(choice)
        if idx < 1 or idx > len(market_drivers):
            print("Invalid driver selection.")
            return

        selected_driver = market_drivers[idx - 1]

        # --- Fame vs prestige gate: some drivers won't sign for small teams ---
        can_sign, required_prestige = can_team_sign_driver(state, selected_driver)
        if not can_sign:
            fame = selected_driver.get("fame", 0)
            print(f"\n{selected_driver['name']} and their backers don't believe your team is ready yet.")
            print(f"  Their fame: {fame}")
            print(f"  Your team prestige: {state.prestige:.1f}")
            print(f"  They'd expect a team with at least {required_prestige:.1f} prestige.")
            print("Put in stronger results or build more reputation before approaching them again.")
            input("\nPress Enter to return to the Driver Market...")
            continue

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
