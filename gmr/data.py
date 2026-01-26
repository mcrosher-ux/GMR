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
        "name": "Giovanni Rossi", "constructor": "Independent",
        "pace": 5, "consistency": 5,
        "aggression": 5, "mechanical_sympathy": 5, "wet_skill": 5,
        "fame": 0,
        "age": 37,
        "country": "Italy",
    },
    {
        "name": "Marco Bianchi", "constructor": "Independent",
        "pace": 6, "consistency": 6,
        "aggression": 6, "mechanical_sympathy": 6, "wet_skill": 6,
        "fame": 1,
        "age": 34,
        "country": "Italy",
    },
    {
        "name": "Luca Ferrari", "constructor": "Independent",
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
]





constructors = {
    "Enzoni": {
        "country": "Italy",
        "engine_id": "enzoni_works_v12",
        "chassis_id": "enzoni_works_monocoque",
        "dev_bonus": 0.25,          # already using this idea
        "dev_attempt_chance": 0.85, # how often they try per offseason
    },
    "Scuderia Valdieri": {
        "country": "Italy",
        "engine_id": "valdieri_works_v12",
        "chassis_id": "valdieri_works_spaceframe",
        "dev_bonus": 0.20,
        "dev_attempt_chance": 0.80,
    },
    "Independent": {"speed": 5, "reliability": 4},
    "Test": {"speed": 5, "reliability": 4},
}

 





tracks = {
    "Marblethorpe GP": {
        "country": "UK",
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
   },
    "Château-des-Prés GP": {
        "country": "France",
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
  },
    "Vallone GP": {
        "country": "Italy",
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
},
    "Rougemont GP": {
        "country": "Switzerland",
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
},
    "Ardennes Endurance GP": {
        "country": "Belgium",
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
},

    "Bradley Fields": {
        "country": "UK",
        "allowed_nationalities": ["UK", "France", "Belgium", "Switzerland"],
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
    },
    "Little Autodromo": {
        "country": "Italy",        
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
    },
    #idea for race that pops up in 1950
    "Union Speedway": {
        "country": "USA",
        "allowed_nationalities": ["USA"],
        "engine_danger": 1.10,
        "crash_danger": 1.15,
        "pace_weight": 1.15,            # bit more about raw speed
        "consistency_weight": 1.00,
        "wet_chance": 0.20,
        "base_hot_chance": 0.45,        # hot Italian afternoons
        "heat_intensity": 1.15,
        "weight_pace_importance": 1.1,
        "weight_crash_importance": 0.8,
        "length_km": 4.0,
        "race_distance_km": 230.0,
        "fame_mult": 1.6,
        "xp_mult": 1.3,
        "fame_cap": 5.0,
        "appearance_base": 100,
        "appearance_prestige_mult": 20,
        "grid_size": 40,
        "suspension_importance": 1.05,
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


]