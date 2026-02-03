# gmr/data.py

drivers = [
    # Enzoni factory drivers – slightly younger, proper pros
    {
        "name": "Carlo Bianci", "constructor": "Enzoni",
        "pace": 7, "consistency": 6,
        "aggression": 7, "mechanical_sympathy": 6, "wet_skill": 6,
        "fame": 1,
        "age": 33,
        "country": "Italy",
    },
    {
        "name": "Alberto Rossi", "constructor": "Enzoni",
        "pace": 7, "consistency": 7,
        "aggression": 6, "mechanical_sympathy": 7, "wet_skill": 7,
        "fame": 1,
        "age": 31,
        "country": "Italy", 
   },

    # Independents – older mix of journeymen and local heroes
    {
        "name": "Emmanuel Dubois", "constructor": "Independent",
        "pace": 5, "consistency": 5,
        "aggression": 5, "mechanical_sympathy": 5, "wet_skill": 5,
        "fame": 0,
        "age": 39,
        "country": "France",
    },
    {
        "name": "George McCallister", "constructor": "Independent",
        "pace": 5, "consistency": 5,
        "aggression": 4, "mechanical_sympathy": 6, "wet_skill": 5,
        "fame": 0,
        "age": 41,
        "country": "UK",
    },
    {
        "name": "Hans Keller", "constructor": "Independent",
        "pace": 5, "consistency": 4,
        "aggression": 7, "mechanical_sympathy": 4, "wet_skill": 4,
        "fame": 0,
        "age": 42,
        "country": "Switzerland",
    },
    {
        "name": "Luis Navarro", "constructor": "Independent",
        "pace": 4, "consistency": 6,
        "aggression": 4, "mechanical_sympathy": 6, "wet_skill": 6,
        "fame": 0,
        "age": 38,
        "country": "Spain",
    },
    {
        "name": "Ivan Petrov", "constructor": "Independent",
        "pace": 4, "consistency": 5,
        "aggression": 5, "mechanical_sympathy": 5, "wet_skill": 4,
        "fame": 0,
        "age": 40,
        "country": "Poland",
    },
    {
        "name": "Antonio Marquez", "constructor": "Independent",
        "pace": 5, "consistency": 3,
        "aggression": 8, "mechanical_sympathy": 3, "wet_skill": 4,
        "fame": 0,
        "age": 37,
        "country": "Spain",
    },

    # Extra independents for driver market – some slightly younger “coming guys”
    {
        "name": "Franco Moretti", "constructor": "Independent",
        "pace": 6, "consistency": 6,
        "aggression": 6, "mechanical_sympathy": 6, "wet_skill": 6,
        "fame": 1,
        "age": 34,
        "country": "Italy",
    },
    {
        "name": "Peter Lang", "constructor": "Independent",
        "pace": 6, "consistency": 5,
        "aggression": 6, "mechanical_sympathy": 5, "wet_skill": 5,
        "fame": 2,
        "age": 29,
        "country": "UK",
    },
    {
        "name": "Jan Novak", "constructor": "Independent",
        "pace": 5, "consistency": 6,
        "aggression": 4, "mechanical_sympathy": 7, "wet_skill": 7,
        "fame": 0,
        "age": 36,
        "country": "USA",
    },
    {
        "name": "Billy Jenkins", "constructor": "Independent",
        "pace": 6, "consistency": 5,
        "aggression": 7, "mechanical_sympathy": 4, "wet_skill": 4,
        "fame": 1,
        "age": 31,
        "country": "USA",
    },
    # High-fame American drivers for Indy-style events
    {
        "name": "Rex Callahan", "constructor": "Independent",
        "pace": 7, "consistency": 4,
        "aggression": 8, "mechanical_sympathy": 3, "wet_skill": 3,
        "fame": 3,
        "age": 28,
        "country": "USA",
    },
    {
        "name": "Duke Harrington", "constructor": "Independent",
        "pace": 6, "consistency": 5,
        "aggression": 6, "mechanical_sympathy": 5, "wet_skill": 4,
        "fame": 2,
        "age": 30,
        "country": "USA",
    },
    {
        "name": "Mikel Herrera", "constructor": "Independent",
        "pace": 4, "consistency": 7,
        "aggression": 3, "mechanical_sympathy": 7, "wet_skill": 5,
        "fame": 0,
        "age": 35,
        "country": "USA",
    },
    {
        "name": "Otto Schmidt", "constructor": "Independent",
        "pace": 4, "consistency": 6,
        "aggression": 4, "mechanical_sympathy": 6, "wet_skill": 4,
        "fame": 0,
        "age": 43,
        "country": "Switzerland",
    },
    {
        "name": "Roberto Silva", "constructor": "Independent",
        "pace": 5, "consistency": 4,
        "aggression": 7, "mechanical_sympathy": 4, "wet_skill": 5,
        "fame": 0,
        "age": 36,
        "country": "Spain",
    },
    {
        "name": "Jack Thompson", "constructor": "Independent",
        "pace": 6, "consistency": 5,
        "aggression": 5, "mechanical_sympathy": 5, "wet_skill": 5,
        "fame": 1,
        "age": 32,
        "country": "UK",
    },
    # More British drivers
    {
        "name": "Reginald Hargrove", "constructor": "Independent",
        "pace": 5, "consistency": 6,
        "aggression": 4, "mechanical_sympathy": 6, "wet_skill": 5,
        "fame": 0,
        "age": 38,
        "country": "UK",
    },
    {
        "name": "Nigel Brooks", "constructor": "Independent",
        "pace": 4, "consistency": 7,
        "aggression": 3, "mechanical_sympathy": 7, "wet_skill": 6,
        "fame": 0,
        "age": 41,
        "country": "UK",
    },
    {
        "name": "Simon Whitaker", "constructor": "Independent",
        "pace": 6, "consistency": 4,
        "aggression": 6, "mechanical_sympathy": 4, "wet_skill": 4,
        "fame": 1,
        "age": 30,
        "country": "UK",
    },
    # More Italian drivers
    {
        "name": "Giovanni Morandi", "constructor": "Independent",
        "pace": 5, "consistency": 5,
        "aggression": 5, "mechanical_sympathy": 5, "wet_skill": 5,
        "fame": 0,
        "age": 37,
        "country": "Italy",
    },
    {
        "name": "Marco Galli", "constructor": "Independent",
        "pace": 6, "consistency": 6,
        "aggression": 6, "mechanical_sympathy": 6, "wet_skill": 6,
        "fame": 1,
        "age": 34,
        "country": "Italy",
    },
    {
        "name": "Luca Bernardi", "constructor": "Independent",
        "pace": 4, "consistency": 6,
        "aggression": 4, "mechanical_sympathy": 6, "wet_skill": 7,
        "fame": 0,
        "age": 39,
        "country": "Italy",
    },
    # More Spanish drivers
    {
        "name": "Carlos Ramirez", "constructor": "Independent",
        "pace": 5, "consistency": 5,
        "aggression": 7, "mechanical_sympathy": 3, "wet_skill": 4,
        "fame": 0,
        "age": 35,
        "country": "Spain",
    },
    {
        "name": "Diego Lopez", "constructor": "Independent",
        "pace": 4, "consistency": 7,
        "aggression": 3, "mechanical_sympathy": 7, "wet_skill": 5,
        "fame": 0,
        "age": 42,
        "country": "Spain",
    },

    # Brazilian drivers
    {
        "name": "João Figueiredo", "constructor": "Independent",
        "pace": 6, "consistency": 5,
        "aggression": 7, "mechanical_sympathy": 5, "wet_skill": 6,
        "fame": 1,
        "age": 29,
        "country": "Brazil",
    },
    {
        "name": "Carlos Mendonça", "constructor": "Independent",
        "pace": 5, "consistency": 6,
        "aggression": 5, "mechanical_sympathy": 6, "wet_skill": 5,
        "fame": 0,
        "age": 34,
        "country": "Brazil",
    },
    {
        "name": "Rubens Almeida", "constructor": "Independent",
        "pace": 7, "consistency": 4,
        "aggression": 8, "mechanical_sympathy": 4, "wet_skill": 4,
        "fame": 2,
        "age": 27,
        "country": "Brazil",
    },
    {
        "name": "Paulo Ribeiro", "constructor": "Independent",
        "pace": 4, "consistency": 7,
        "aggression": 4, "mechanical_sympathy": 7, "wet_skill": 6,
        "fame": 0,
        "age": 38,
        "country": "Brazil",
    },

    # Argentinian drivers
    {
        "name": "Juan Manuel Ortega", "constructor": "Independent",
        "pace": 7, "consistency": 6,
        "aggression": 6, "mechanical_sympathy": 6, "wet_skill": 5,
        "fame": 2,
        "age": 31,
        "country": "Argentina",
    },
    {
        "name": "Héctor Ramos", "constructor": "Independent",
        "pace": 5, "consistency": 5,
        "aggression": 6, "mechanical_sympathy": 5, "wet_skill": 4,
        "fame": 1,
        "age": 33,
        "country": "Argentina",
    },
    {
        "name": "Raúl Fernández", "constructor": "Independent",
        "pace": 6, "consistency": 5,
        "aggression": 7, "mechanical_sympathy": 4, "wet_skill": 5,
        "fame": 1,
        "age": 28,
        "country": "Argentina",
    },
    {
        "name": "Miguel Sánchez", "constructor": "Independent",
        "pace": 4, "consistency": 6,
        "aggression": 4, "mechanical_sympathy": 7, "wet_skill": 6,
        "fame": 0,
        "age": 40,
        "country": "Argentina",
    },

    # =========================================================================
    # GERMAN DRIVERS - Appear from 1950 (West Germany returns to motorsport)
    # =========================================================================
    # These drivers represent the return of German motorsport after WWII.
    # Before 1950, German drivers were banned from international competition.
    {
        "name": "Wolfgang Bergmann", "constructor": "Independent",
        "pace": 6, "consistency": 6,
        "aggression": 5, "mechanical_sympathy": 7, "wet_skill": 5,
        "fame": 1,
        "age": 32,
        "country": "Germany",
        "appears_from_year": 1950,  # West Germany returns
    },
    {
        "name": "Klaus Richter", "constructor": "Independent",
        "pace": 7, "consistency": 5,
        "aggression": 6, "mechanical_sympathy": 6, "wet_skill": 4,
        "fame": 2,
        "age": 28,
        "country": "Germany",
        "appears_from_year": 1950,
    },
    {
        "name": "Helmut Braun", "constructor": "Independent",
        "pace": 5, "consistency": 7,
        "aggression": 4, "mechanical_sympathy": 8, "wet_skill": 5,
        "fame": 0,
        "age": 35,
        "country": "Germany",
        "appears_from_year": 1950,
    },
    {
        "name": "Dieter Hoffmann", "constructor": "Independent",
        "pace": 5, "consistency": 6,
        "aggression": 5, "mechanical_sympathy": 6, "wet_skill": 6,
        "fame": 0,
        "age": 33,
        "country": "Germany",
        "appears_from_year": 1950,
    },

    {
        "name": "Rico Valente", "constructor": "Test",
        "pace": 9, "consistency": 3,
        "aggression": 9, "mechanical_sympathy": 2, "wet_skill": 5,
        "fame": 0,
        "age": 30,
    },
    {
        "name": "Walter Hume", "constructor": "Test",
        "pace": 4, "consistency": 9,
        "aggression": 2, "mechanical_sympathy": 9, "wet_skill": 5,
        "fame": 0,
        "age": 43,
    },
    {
        "name": "Marius Rainier", "constructor": "Test",
        "pace": 6, "consistency": 7,
        "aggression": 5, "mechanical_sympathy": 7, "wet_skill": 10,
        "fame": 0,
        "age": 33,
    },
    {
        "name": "Elena Straka", "constructor": "Test",
        "pace": 8, "consistency": 8,
        "aggression": 6, "mechanical_sympathy": 3, "wet_skill": 6,
        "fame": 0,
        "age": 32,
    },

    # === Gentleman Drivers / Privateers ===
    # These wealthy amateurs appear at select races with their own privately-entered cars
    {
        "name": "Prince Sagat", "constructor": "Independent",
        "pace": 4, "consistency": 5,  # meh pace, reasonable consistency
        "aggression": 3, "mechanical_sympathy": 8, "wet_skill": 6,  # great with machinery, ok in wet, cautious
        "fame": 2,  # royal fame
        "age": 26,  # young prince in 1949
        "country": "Thailand",
        "gentleman_driver": True,
        "appears_from_year": 1949,
        "selective_entries": True,  # only big races + random medium ones
    },
]





constructors = {
    "Enzoni": {
        "country": "Italy",
        "engine_id": "enzoni_works_v12",
        "chassis_id": "enzoni_works_monocoque",
        "dev_bonus": 0.25,          # already using this idea
        "dev_attempt_chance": 0.85, # how often they try per offseason
        "prestige": 15.0,           # team prestige - affects driver loyalty and poaching
        "max_drivers": 2,           # how many cars/drivers the team can field
        "replenishes": True,        # AI team will sign replacements if below max_drivers
    },
    "Scuderia Valdieri": {
        "country": "Italy",
        "engine_id": "valdieri_works_v12",
        "chassis_id": "valdieri_works_spaceframe",
        "dev_bonus": 0.20,
        "dev_attempt_chance": 0.80,
        "prestige": 12.0,           # strong team but below Enzoni
        "max_drivers": 2,           # standard two-car team
        "replenishes": True,        # AI team will sign replacements
    },
    "Silberkern-Stahl": {
        "country": "Germany",
        "engine_id": "silberkern_works_i6",
        "chassis_id": "silberkern_works_spaceframe",
        "dev_bonus": 0.22,
        "dev_attempt_chance": 0.90,  # German engineering precision
        "prestige": 13.0,            # prestigious German works team
        "max_drivers": 2,
        "replenishes": True,
        "allowed_nationalities": ["Germany", "Switzerland"],  # Germanic drivers only
        "appears_from_year": 1952,   # West Germany returns to motorsport
    },
    "Independent": {
        "speed": 5,
        "reliability": 4,
        "prestige": 0.0,            # no team prestige
        "max_drivers": 999,         # no limit (catch-all category)
        "replenishes": False,       # not a real team
    },
    "Test": {
        "speed": 5,
        "reliability": 4,
        "prestige": 0.0,
        "max_drivers": 999,
        "replenishes": False,
    },
}

 





tracks = {
    # ==========================================================================
    # EUROPEAN GRAND PRIX CIRCUITS
    # ==========================================================================
    
    "Marblethorpe GP": {
        "country": "UK",
        "flavor": "Nestled in the rolling hills of the northern countryside, Marblethorpe is a test of endurance on its long, sweeping corners. The circuit's high speeds demand precise car setup, and the unpredictable weather often turns races into survival challenges. Local fans pack the grandstands, waving flags and cheering for homegrown talent.",
        "engine_danger": 1.05,
        "crash_danger": 1.00,
        "pace_weight": 1.04,
        "consistency_weight": 0.96,
        "wet_chance": 0.50,
        "base_hot_chance": 0.08,
        "heat_intensity": 1.00,
        "weight_pace_importance": 0.8,
        "weight_crash_importance": 0.7,
        "length_km": 5.0,
        "race_distance_km": 250.0,
        "fame_mult": 1.1,
        "xp_mult": 1.1, 
        "fame_cap": 3.0,
        "appearance_base": 35,
        "appearance_prestige_mult": 14,
        "suspension_importance": 1.00,
        "grid_size": 28,
        # Track evolution ratings
        "safety_rating": 4,         # Decent for the era
        "facilities_rating": 5,     # Good grandstands
        "prestige_rating": 5,       # Respected British venue
   },
    "Château-des-Prés GP": {
        "country": "France",
        "flavor": "Set in the picturesque valley, Château-des-Prés combines elegance with danger. The chateau's historic walls echo with the roar of engines, and the tight, technical layout punishes any lapse in concentration. Passionate crowds are enthusiastic, with drinks flowing freely in the pits and the air thick with smoke.",
        "engine_danger": 0.95,
        "crash_danger": 1.10,
        "pace_weight": 0.95,
        "consistency_weight": 1.10,
        "wet_chance": 0.35,
        "base_hot_chance": 0.20,
        "heat_intensity": 1.05,
        "weight_pace_importance": 1.3,
        "weight_crash_importance": 0.9,
        "length_km": 6.2,
        "race_distance_km": 250.0,
        "fame_mult": 1.0,
        "xp_mult": 1.1,
        "fame_cap": 3.1, 
        "suspension_importance": 1.35,
        "appearance_base": 40,
        "appearance_prestige_mult": 15,             
        "grid_size": 20,
        # Track evolution ratings
        "safety_rating": 3,         # Tight streets = dangerous
        "facilities_rating": 6,     # French elegance
        "prestige_rating": 6,       # Historic venue
  },
    "Vallone GP": {
        "country": "Italy",
        "flavor": "The crown jewel of Italian motorsport, Vallone's high-speed straights and blistering heat push cars and drivers to their limits. Nestled in the Tuscan hills, the circuit's demanding nature has claimed many victims, but the glory of victory here is unmatched. Espresso-fueled mechanics work through the night, and the air vibrates with the passion of tifosi.",
        "engine_danger": 1.10,
        "crash_danger": 1.05,
        "pace_weight": 1.12,
        "consistency_weight": 0.92,
        "wet_chance": 0.20,
        "base_hot_chance": 0.55,
        "heat_intensity": 1.15,
        "weight_pace_importance": 0.4,
        "weight_crash_importance": 0.5,
        "length_km": 7.0,
        "race_distance_km": 250.0,
        "fame_mult": 1.35,
        "xp_mult": 1.35,   
        "fame_cap": 4.1,
        "suspension_importance": 0.85,
        "appearance_base": 70,
        "appearance_prestige_mult": 18,
        "grid_size": 30,
        # Track evolution ratings
        "safety_rating": 4,         # Fast but some barriers
        "facilities_rating": 7,     # Premier Italian venue
        "prestige_rating": 9,       # Crown jewel of motorsport
    },
    "Rougemont GP": {
        "country": "Switzerland",
        "flavor": "Perched in the pristine Swiss Alps, Rougemont is a circuit of precision and beauty. The cool mountain air and sweeping alpine views create a serene backdrop for intense competition, where mechanical perfection is rewarded. Swiss efficiency reigns in the pits, with watches ticking in sync with lap times, and the crisp air carries the scent of fresh snow from nearby peaks.",
        "engine_danger": 1.00,
        "crash_danger": 0.95,
        "pace_weight": 1.00,
        "consistency_weight": 1.00,
        "wet_chance": 0.30,
        "base_hot_chance": 0.20,
        "heat_intensity": 1.05,
        "weight_pace_importance": 1.0,
        "weight_crash_importance": 0.8,
        "length_km": 5.8,
        "race_distance_km": 250.0,
        "fame_mult": 0.6,
        "xp_mult": 0.1,
        "fame_cap": 2.0, 
        "appearance_base": 30,
        "suspension_importance": 1.00,
        "appearance_prestige_mult": 14,
        # Track evolution ratings
        "safety_rating": 5,         # Swiss precision
        "facilities_rating": 5,     # Well-maintained
        "prestige_rating": 4,       # Scenic but smaller
    },
    "Ardennes Endurance GP": {
        "country": "Belgium",
        "flavor": "The grueling Ardennes circuit winds through the dense forests of the Belgian Ardennes, a true test of man and machine. Its long distance and variable weather make reliability paramount, and the thick woods muffle the cheers of sparse crowds. Victory here is a badge of honor, whispered about in smoky bars across Europe.",
        "engine_danger": 1.15,
        "crash_danger": 1.05,
        "pace_weight": 1.08,
        "consistency_weight": 1.02,
        "wet_chance": 0.50,
        "base_hot_chance": 0.10,
        "heat_intensity": 1.05,
        "weight_pace_importance": 1.1,
        "weight_crash_importance": 0.9,
        "length_km": 7.5,
        "race_distance_km": 400.0,
        "fame_mult": 1.5,
        "xp_mult": 1.5,
        "fame_cap": 5.0,  
        "suspension_importance": 0.85, 
        "appearance_base": 80,
        "appearance_prestige_mult": 20,
        "grid_size": 35,
        # Track evolution ratings
        "safety_rating": 3,         # Forest = dangerous
        "facilities_rating": 5,     # Basic but functional
        "prestige_rating": 8,       # Legendary endurance test
    },
    
    "Schwarzwald Ring": {
        "country": "Germany",
        "flavor": "The Green Hell. Over 170 corners carved into the forested mountains, the Schwarzwald Ring is motorsport's ultimate challenge. Dense forests, blind crests, and unpredictable weather create a lethal combination that has humbled the greatest drivers. The German crowds gather at infamous corners like Teufelskurve and Adlersprung, where courage is tested against the mountain itself.",
        "engine_danger": 1.20,
        "crash_danger": 1.25,
        "pace_weight": 1.05,
        "consistency_weight": 1.15,
        "wet_chance": 0.45,
        "base_hot_chance": 0.15,
        "heat_intensity": 1.00,
        "weight_pace_importance": 0.6,
        "weight_crash_importance": 1.2,
        "length_km": 22.8,          # The full Nordschleife
        "race_distance_km": 350.0,
        "fame_mult": 1.6,
        "xp_mult": 1.6,
        "fame_cap": 5.0,
        "suspension_importance": 1.25,
        "appearance_base": 90,
        "appearance_prestige_mult": 22,
        "grid_size": 30,
        # Track evolution ratings
        "safety_rating": 2,         # Terrifyingly dangerous
        "facilities_rating": 6,     # Good German infrastructure
        "prestige_rating": 9,       # Legendary status
    },
    
    "Circuito de las Palmas": {
        "country": "Spain",
        "flavor": "The coastal street circuit winds through the elegant harbor district, where palm trees line the course and Mediterranean sunshine beats down on the tarmac. Spanish passion fills the air as local heroes battle international stars on the tight, demanding layout. The post-race celebrations spill into the city's tapas bars.",
        "engine_danger": 1.00,
        "crash_danger": 1.12,
        "pace_weight": 0.98,
        "consistency_weight": 1.08,
        "wet_chance": 0.15,
        "base_hot_chance": 0.50,
        "heat_intensity": 1.18,
        "weight_pace_importance": 1.1,
        "weight_crash_importance": 1.0,
        "length_km": 6.3,
        "race_distance_km": 250.0,
        "fame_mult": 1.1,
        "xp_mult": 1.1,
        "fame_cap": 3.5,
        "suspension_importance": 1.15,
        "track_roughness": 1.15,        # Street circuit
        "appearance_base": 55,
        "appearance_prestige_mult": 16,
        "grid_size": 24,
        # Track evolution ratings
        "safety_rating": 3,         # Street circuit
        "facilities_rating": 5,     # City provides support
        "prestige_rating": 6,       # Growing reputation
    },

    "Monaco GP": {
        "country": "Monaco",
        "flavor": "The jewel of motorsport. A ribbon of tarmac carved through the principality's streets, where millionaires watch from yacht decks and drivers thread their machines past casino, tunnel, and harbor at impossible speeds. One mistake means the barriers. No room for error, no room for the timid. Victory at Monaco elevates a driver to legend.",
        "engine_danger": 0.90,          # Slow speeds spare engines
        "crash_danger": 1.20,           # Barriers everywhere
        "pace_weight": 0.85,            # Less about raw speed
        "consistency_weight": 1.25,     # Precision is everything
        "wet_chance": 0.20,
        "base_hot_chance": 0.40,
        "heat_intensity": 1.12,
        "weight_pace_importance": 1.4,   # Light nimble cars excel
        "track_roughness": 1.20,        # Bumpy street circuit
        "weight_crash_importance": 1.3,
        "length_km": 3.18,
        "race_distance_km": 318.0,       # 100 laps
        "fame_mult": 2.0,               # THE prestige race
        "xp_mult": 1.8,
        "fame_cap": 5.0,
        "suspension_importance": 1.40,   # Bumpy streets
        "appearance_base": 120,
        "appearance_prestige_mult": 30,
        "grid_size": 20,                 # Small grid, tight streets
        # Track evolution ratings
        "safety_rating": 2,              # Barriers and harbor = death
        "facilities_rating": 8,          # Principality spares no expense
        "prestige_rating": 10,           # The ultimate prize
    },

    # ==========================================================================
    # EUROPEAN CLUB CIRCUITS (Regional/Local)
    # ==========================================================================
    
    "Bradley Fields": {
        "country": "UK",
        "allowed_nationalities": ["UK", "France", "Belgium", "Switzerland"],
        "flavor": "A modest club circuit on the windswept Yorkshire moors, Bradley Fields is where newcomers prove themselves. The short, tight layout favors mechanical sympathy over outright speed, and the damp air often brings fog and rain. It's a humble venue, but podiums here open doors to bigger stages.",
        "engine_danger": 0.95,          # not too hard on engines
        "crash_danger": 1.00,           # club-level risk
        "pace_weight": 0.98,
        "consistency_weight": 1.05,     # rewards tidy drivers a bit
        "wet_chance": 0.55,             # moors = often grim
        "base_hot_chance": 0.10,
        "heat_intensity": 1.00,
        "weight_pace_importance": 0.9,
        "weight_crash_importance": 0.9,
        "length_km": 3.2,
        "race_distance_km": 160.0,      # short, sprint-y
        "fame_mult": 0.7,
        "xp_mult": 0.7,
        "fame_cap": 2.0,
        "appearance_base": 20,
        "appearance_prestige_mult": 12,
        "grid_size": 15,
        "suspension_importance": 1.00,
        # Track evolution ratings
        "safety_rating": 2,         # Basic club facilities
        "facilities_rating": 2,     # Hay bales and hope
        "prestige_rating": 2,       # Local hero venue
    },
    "Little Autodromo": {
        "country": "Italy",
        "allowed_nationalities": ["Italy", "Spain"],
        "flavor": "A sun-baked testing ground in the Italian countryside, Little Autodromo is where Italian hopefuls hone their skills. The warm climate and straightforward layout make it ideal for learning, but the heat can expose weaknesses. Local mechanics share tips over gelato, and the atmosphere is one of camaraderie rather than cutthroat competition.",
        "engine_danger": 1.00,
        "crash_danger": 1.02,
        "pace_weight": 1.05,            # bit more about raw speed
        "consistency_weight": 0.95,
        "wet_chance": 0.25,
        "base_hot_chance": 0.45,        # hot Italian afternoons
        "heat_intensity": 1.10,
        "weight_pace_importance": 1.1,
        "weight_crash_importance": 0.8,
        "length_km": 3.5,
        "race_distance_km": 180.0,
        "fame_mult": 0.7,
        "xp_mult": 0.7,
        "fame_cap": 2.0,
        "appearance_base": 20,
        "appearance_prestige_mult": 12,
        "grid_size": 20,
        "suspension_importance": 1.00,
        # Track evolution ratings
        "safety_rating": 3,         # Italian testing venue
        "facilities_rating": 3,     # Small but proper
        "prestige_rating": 3,       # Stepping stone circuit
    },
    # ==========================================================================
    # AMERICAS CIRCUITS (from 1948)
    # ==========================================================================
    
    "Union Speedway": {
        "country": "USA",
        "flavor": "A vast American oval under the wide-open skies, Union Speedway is where horsepower reigns supreme. The long straights and high banking test the limits of speed and courage, with the roar of engines echoing across the plains. American crowds are boisterous, waving flags, and the post-race gatherings are legendary. Victory here is about raw power and the dream of motorsport.",
        "engine_danger": 1.15,
        "crash_danger": 1.25,
        "pace_weight": 1.25,            # heavily favors raw speed
        "consistency_weight": 0.75,     # driving skill less important
        "wet_chance": 0.20,
        "base_hot_chance": 0.45,
        "heat_intensity": 1.15,
        "weight_pace_importance": 1.3,
        "weight_crash_importance": 0.7,
        "length_km": 4.0,
        "race_distance_km": 230.0,
        "fame_mult": 1.8,
        "xp_mult": 1.5,
        "fame_cap": 6.0,
        "appearance_base": 120,
        "appearance_prestige_mult": 25,
        "grid_size": 40,
        "suspension_importance": 1.05,
        "track_roughness": 0.90,        # Smooth American oval
        # Track evolution ratings
        "safety_rating": 3,         # Ovals are fast and dangerous
        "facilities_rating": 8,     # American money
        "prestige_rating": 8,       # Legendary American venue
    },
    
    "Autódromo General San Martín": {
        "country": "Argentina",
        "flavor": "The pride of South American motorsport, Autódromo General San Martín is a cathedral of speed where Fangio's legend was born. The passionate Argentine crowds pack the grandstands, waving blue and white flags and singing for their heroes. The sweltering summer heat tests man and machine, and victory here grants instant legend status across the continent. The post-race asado celebrations are legendary.",
        "engine_danger": 1.12,
        "crash_danger": 1.08,
        "pace_weight": 1.10,
        "consistency_weight": 0.94,
        "wet_chance": 0.15,
        "base_hot_chance": 0.60,        # Southern hemisphere summer = hot
        "heat_intensity": 1.20,
        "weight_pace_importance": 0.5,
        "weight_crash_importance": 0.6,
        "length_km": 6.8,
        "race_distance_km": 270.0,
        "fame_mult": 1.30,
        "xp_mult": 1.30,
        "fame_cap": 4.0,
        "suspension_importance": 0.90,
        "appearance_base": 65,
        "appearance_prestige_mult": 18,
        "grid_size": 28,
        # Track evolution ratings
        "safety_rating": 4,         # Modern South American venue
        "facilities_rating": 6,     # Good infrastructure
        "prestige_rating": 7,       # Continental pride
    },
    
    "Circuito da Estrada Velha": {
        "country": "Brazil",
        "allowed_nationalities": ["Brazil", "Argentina", "USA"],
        "flavor": "A dusty proving ground on the outskirts of São Paulo, Circuito da Estrada Velha is where Brazilian dreams of motorsport glory begin. The undulating layout through the favela hills tests mechanical sympathy, and the tropical heat demands careful car management. Local fans bring drums and celebration, turning race day into a carnival of speed and passion.",
        "engine_danger": 1.02,
        "crash_danger": 1.05,
        "pace_weight": 1.02,
        "consistency_weight": 1.00,
        "wet_chance": 0.35,             # Tropical afternoon storms
        "base_hot_chance": 0.50,
        "heat_intensity": 1.12,
        "weight_pace_importance": 1.0,
        "weight_crash_importance": 0.9,
        "length_km": 3.8,
        "race_distance_km": 175.0,      # Shorter club race
        "fame_mult": 0.75,
        "xp_mult": 0.75,
        "fame_cap": 2.2,
        "appearance_base": 22,
        "appearance_prestige_mult": 13,
        "grid_size": 18,
        "suspension_importance": 1.10,
        # Track evolution ratings
        "safety_rating": 2,         # Basic Brazilian club
        "facilities_rating": 2,     # Humble beginnings
        "prestige_rating": 2,       # Local proving ground
    },
    
    "Copper State Circuit": {
        "country": "USA",
        "allowed_nationalities": ["USA", "UK", "Argentina", "Brazil"],
        "flavor": "Carved into the Arizona desert, Copper State Circuit is a rugged circuit where the sun beats down mercilessly on both driver and machine. The red dust kicks up behind every car, and the dry heat pushes engines to their limits. American racers from the dusty oval circuits come here to test themselves against European machinery. The sunsets over the canyon are spectacular, and the roadside diners serve the best pie west of the Mississippi.",
        "engine_danger": 1.05,
        "crash_danger": 1.02,
        "pace_weight": 1.00,
        "consistency_weight": 1.02,
        "wet_chance": 0.08,             # Desert = almost never wet
        "base_hot_chance": 0.70,        # Arizona is brutal
        "heat_intensity": 1.25,
        "weight_pace_importance": 0.95,
        "weight_crash_importance": 0.85,
        "length_km": 4.2,
        "race_distance_km": 200.0,
        "fame_mult": 0.85,
        "xp_mult": 0.85,
        "fame_cap": 2.5,
        "appearance_base": 28,
        "appearance_prestige_mult": 14,
        "grid_size": 22,
        "suspension_importance": 1.05,
        # Track evolution ratings
        "safety_rating": 3,         # Desert run-off helps
        "facilities_rating": 3,     # Modest American venue
        "prestige_rating": 3,       # Regional interest
    },
    
    # ==========================================================================
    # AFRICAN CIRCUITS (from 1950)
    # ==========================================================================
    
    "Kingsport Coastal Circuit": {
        "country": "South Africa",
        "flavor": "On the rugged Eastern Cape coastline, the Kingsport circuit brings motorsport to the southern tip of Africa. The sea breeze and coastal humidity create unique conditions, while the passionate South African crowds embrace racing with colonial-era enthusiasm. The circuit's challenging elevation changes and fast corners demand respect, and victory here earns acclaim across the Commonwealth.",
        "engine_danger": 1.05,
        "crash_danger": 1.08,
        "pace_weight": 1.05,
        "consistency_weight": 1.00,
        "wet_chance": 0.25,
        "base_hot_chance": 0.40,
        "heat_intensity": 1.10,
        "weight_pace_importance": 0.9,
        "weight_crash_importance": 0.85,
        "length_km": 5.0,
        "race_distance_km": 240.0,
        "fame_mult": 1.0,
        "xp_mult": 1.0,
        "fame_cap": 3.0,
        "appearance_base": 45,
        "appearance_prestige_mult": 15,
        "grid_size": 24,
        "suspension_importance": 1.05,
        # Track evolution ratings
        "safety_rating": 3,         # Developing venue
        "facilities_rating": 4,     # Colonial infrastructure
        "prestige_rating": 5,       # Commonwealth prestige
    },
    
    "Circuit de Sable d'Or": {
        "country": "Morocco",
        "flavor": "Along the Atlantic coast, the Circuit de Sable d'Or is an exotic jewel in motorsport's crown. The North African heat shimmers on the tarmac as European teams face unfamiliar conditions. The French colonial influence shows in the organization, while Moroccan hospitality provides a unique atmosphere. Palm trees line the pit straight, and the call to prayer mingles with the scream of engines.",
        "engine_danger": 1.08,
        "crash_danger": 1.05,
        "pace_weight": 1.02,
        "consistency_weight": 1.00,
        "wet_chance": 0.10,             # North Africa = dry
        "base_hot_chance": 0.55,
        "heat_intensity": 1.18,
        "weight_pace_importance": 0.85,
        "weight_crash_importance": 0.9,
        "length_km": 7.6,
        "race_distance_km": 280.0,
        "fame_mult": 1.1,
        "xp_mult": 1.1,
        "fame_cap": 3.2,
        "appearance_base": 50,
        "appearance_prestige_mult": 16,
        "grid_size": 26,
        "suspension_importance": 0.95,
        # Track evolution ratings
        "safety_rating": 3,         # Coastal but basic
        "facilities_rating": 5,     # French colonial quality
        "prestige_rating": 5,       # Exotic appeal
    },
    
    # ==========================================================================
    # ASIAN CIRCUITS (from 1952)
    # ==========================================================================
    
    "Fuji Kogen Circuit": {
        "country": "Japan",
        "flavor": "Rising from the mists of rural Japan, Fuji Kogen is a technical masterpiece that rewards precision driving. The unique figure-eight layout with its crossover bridge creates corners unlike anywhere else, from the lightning-fast Hayabusa curve to the tight Tanuki bends. Japanese efficiency keeps the facility immaculate, and the respectful crowds bring a different energy to racing. Cherry blossoms frame the paddock in spring, and victory here earns honor across Asia.",
        "engine_danger": 1.10,
        "crash_danger": 1.15,
        "pace_weight": 1.08,
        "consistency_weight": 1.05,
        "wet_chance": 0.35,             # Japanese monsoons
        "base_hot_chance": 0.35,
        "heat_intensity": 1.12,
        "weight_pace_importance": 0.7,
        "weight_crash_importance": 1.0,
        "length_km": 5.8,
        "race_distance_km": 260.0,
        "fame_mult": 1.2,
        "xp_mult": 1.2,
        "fame_cap": 3.8,
        "appearance_base": 55,
        "appearance_prestige_mult": 17,
        "grid_size": 26,
        "suspension_importance": 1.15,
        # Track evolution ratings
        "safety_rating": 4,         # Japanese attention to detail
        "facilities_rating": 6,     # Excellent infrastructure
        "prestige_rating": 6,       # Growing Asian interest
    },



}

# ------------------------------
# ENGINES
# ------------------------------
engines = [
    {
        "id": "dad_old",
        "name": "Harper Type-1",
        "supplier": "Inherited",
        "speed": 4,
        "reliability": 4,
        "acceleration": 3,
        "heat_tolerance": 3,
        "price": 0,
        "description": "A creaking pre-war single-carb straight-4.",

    },
    {
        "id": "harper_improved",
        "name": "Harper Type-1B",
        "supplier": "Surplus Dealer",
        "speed": 5,
        "reliability": 5,
        "acceleration": 5,
        "heat_tolerance": 4,
        "price": 1500,
        "description": "A factory-refurbished upgrade of the Type-1.",
 

    },
    {
        "id": "enzoni_customer_spec",
        "name": "Enzoni 1500 V12",
        "supplier": "Enzoni",
        "speed": 7,
        "reliability": 6,
        "acceleration": 7,
        "heat_tolerance": 7,
        "price": 3500,
        "description": "Customer-spec version of Enzoni's feared 1500 V12 – close to works pace, but not quite.",


     },
    {
        "id": "enzoni_works_v12",
        "name": "Enzoni 1500 V12 (Works)",
        "supplier": "Enzoni Works",
        "speed": 8,
        "reliability": 7,
        "acceleration": 8,
        "heat_tolerance": 8,
        "price": 0,
        "for_sale": False,   # <-- add this
        "description": "Works-only unit. Not available to customers.",
},


{
        "id": "valdieri_works_v12",
        "name": "Valdieri 1500 V12",
        "supplier": "Scuderia Valdieri",
        "speed": 8,
        "reliability": 5,          # faster but fragile
        "acceleration": 8,
        "heat_tolerance": 5,       # THIS is where they suffer
        "price": 0,
        "for_sale": False,
        "description": (
            "A ferociously fast Italian V12. Matches the best on pace, "
            "but prone to overheating and mechanical drama over long distances."
        ),
},
{
        "id": "silberkern_works_i6",
        "name": "Silberkern M196 I6",
        "supplier": "Silberkern-Stahl",
        "speed": 7,
        "reliability": 8,          # German reliability
        "acceleration": 7,
        "heat_tolerance": 8,       # Excellent cooling design
        "price": 0,
        "for_sale": False,
        "description": (
            "A masterpiece of German engineering. The fuel-injected straight-six "
            "may lack the fury of Italian V12s, but compensates with uncanny "
            "reliability and superior heat management. The Silver Arrows return."
        ),
},


]


# ------------------------------
# CHASSIS
# ------------------------------
chassis_list = [
{
        "id": "scrapyard_roller",
        "name": "Scrapyard Roller Frame",
        "supplier": "Breaker’s Yard",
        "weight": 8,
        "aero": 1,
        "suspension": 2,
        "price": 0,
        "description": (
        "Barely straight and held together by faith. "
        "Awful pace, but it gets you back onto the grid."
        ),
        "dev_slots": 0,
        "dev_runs_done": 0,
    },
    {
        "id": "dad_chassis",
        "name": "Harper Tube-Frame Mk1",
        "supplier": "Inherited",
        "weight": 7,
        "aero": 2,
        "suspension": 3,
        "price": 400,
        "description": "An aging pre-war ladder frame. Sturdy but heavy.",
       
        "dev_slots": 1,
        "dev_runs_done": 0,
    },
    {
        "id": "lightweight_special",
        "name": "Harrington Lightweight Special",
        "supplier": "Private Fabricator",
        "weight": 4,
        "aero": 3,
        "suspension": 5,
        "price": 900,
        "description": "A lighter, more modern frame.",
       
        "dev_slots": 1,
        "dev_runs_done": 0,
    },
    {
        "id": "enzoni_works_monocoque",
        "name": "Enzoni Works Monocoque",
        "supplier": "Enzoni Works",
        "weight": 3,
        "aero": 4,
        "suspension": 6,        
        "price": 0,  # not for sale        
        "for_sale": False,
        "description": "Factory-only chassis. Lighter and stiffer than customer frames.",
       
        "dev_slots": 2,
        "dev_runs_done": 0,

    },

{
        "id": "valdieri_works_spaceframe",
        "name": "Valdieri Lightweight Spaceframe",
        "supplier": "Scuderia Valdieri",
        "weight": 3,        # extremely light
        "aero": 5,          # better aero than Enzoni
        "suspension": 7,
        "price": 0,
        "for_sale": False,
        "description": (
            "A radical lightweight chassis prioritising agility and speed. "
            "Superb when pushed, but less forgiving over race distance."
        ),
       
        "dev_slots": 2,
        "dev_runs_done": 0,
},
{
        "id": "silberkern_works_spaceframe",
        "name": "Silberkern W196 Stromlinien",
        "supplier": "Silberkern-Stahl",
        "weight": 4,        # heavier than Italian rivals
        "aero": 3,          # less aero focus
        "suspension": 8,    # superb German engineering
        "price": 0,
        "for_sale": False,
        "description": (
            "The Silver Arrow reborn. A heavy but immaculately engineered chassis "
            "with exceptional suspension geometry. What it lacks in lightness, "
            "it makes up for in mechanical grip and reliability."
        ),
       
        "dev_slots": 2,
        "dev_runs_done": 0,
},


]