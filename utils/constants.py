"""
Constants for SkyHustle.
Defines game mechanics, building types, unit types, tech tree, etc.
"""

# Starting resources for new players
PLAYER_STARTING_RESOURCES = {
    "credits": 1000,
    "minerals": 500,
    "energy": 500,
    "skybucks": 0  # Premium currency
}

# Building types
BUILDING_TYPES = [
    {
        "id": "command_center",
        "name": "Command Center",
        "description": "The heart of your aerial base. Required for all operations.",
        "category": "infrastructure",
        "cost_credits": 500,
        "cost_minerals": 250,
        "cost_energy": 100,
        "build_time": 120,  # seconds
        "health": 1000,
        "produces": {
            "credits": 50,  # per hour
            "minerals": 0,
            "energy": 0
        }
    },
    {
        "id": "solar_array",
        "name": "Solar Array",
        "description": "Harnesses solar energy to power your base.",
        "category": "production",
        "cost_credits": 200,
        "cost_minerals": 100,
        "cost_energy": 0,
        "build_time": 60,
        "health": 300,
        "produces": {
            "credits": 0,
            "minerals": 0,
            "energy": 30
        }
    },
    {
        "id": "mineral_extractor",
        "name": "Mineral Extractor",
        "description": "Extracts minerals from clouds and sky debris.",
        "category": "production",
        "cost_credits": 250,
        "cost_minerals": 50,
        "cost_energy": 50,
        "build_time": 90,
        "health": 400,
        "produces": {
            "credits": 0,
            "minerals": 25,
            "energy": 0
        }
    },
    {
        "id": "credit_mint",
        "name": "Credit Mint",
        "description": "Generates credits through trade and commerce.",
        "category": "production",
        "cost_credits": 300,
        "cost_minerals": 150,
        "cost_energy": 75,
        "build_time": 75,
        "health": 350,
        "produces": {
            "credits": 35,
            "minerals": 0,
            "energy": 0
        }
    },
    {
        "id": "barracks",
        "name": "Barracks",
        "description": "Trains infantry units for your army.",
        "category": "military",
        "cost_credits": 400,
        "cost_minerals": 200,
        "cost_energy": 50,
        "build_time": 120,
        "health": 500,
        "unlocks": ["soldier", "heavy_gunner"]
    },
    {
        "id": "hangar",
        "name": "Hangar",
        "description": "Constructs aerial combat units.",
        "category": "military",
        "cost_credits": 600,
        "cost_minerals": 300,
        "cost_energy": 100,
        "build_time": 180,
        "health": 450,
        "unlocks": ["drone", "fighter"]
    },
    {
        "id": "research_lab",
        "name": "Research Lab",
        "description": "Researches new technologies to enhance your base.",
        "category": "infrastructure",
        "cost_credits": 800,
        "cost_minerals": 400,
        "cost_energy": 200,
        "build_time": 240,
        "health": 300,
        "unlocks_research": True
    },
    {
        "id": "defense_turret",
        "name": "Defense Turret",
        "description": "Automated defense system to protect your base.",
        "category": "defense",
        "cost_credits": 300,
        "cost_minerals": 150,
        "cost_energy": 75,
        "build_time": 90,
        "health": 400,
        "attack": 50,
        "range": 2
    },
    {
        "id": "shield_generator",
        "name": "Shield Generator",
        "description": "Generates a protective shield around your base.",
        "category": "defense",
        "cost_credits": 500,
        "cost_minerals": 250,
        "cost_energy": 150,
        "build_time": 150,
        "health": 350,
        "shield": 1000,
        "recharge_rate": 10  # per hour
    },
    {
        "id": "alliance_hall",
        "name": "Alliance Hall",
        "description": "Allows joining and creating alliances with other players.",
        "category": "infrastructure",
        "cost_credits": 1000,
        "cost_minerals": 500,
        "cost_energy": 250,
        "build_time": 300,
        "health": 800,
        "unlocks_alliances": True
    }
]

# Unit types
UNIT_TYPES = [
    {
        "id": "drone",
        "name": "Reconnaissance Drone",
        "description": "Basic aerial unit for scouting and light combat.",
        "category": "air",
        "cost_credits": 100,
        "cost_minerals": 50,
        "cost_energy": 25,
        "train_time": 30,  # seconds
        "health": 100,
        "attack": 20,
        "defense": 10,
        "speed": 3,
        "prerequisites": ["hangar"]
    },
    {
        "id": "fighter",
        "name": "Sky Fighter",
        "description": "Medium combat aircraft with balanced stats.",
        "category": "air",
        "cost_credits": 200,
        "cost_minerals": 100,
        "cost_energy": 50,
        "train_time": 60,
        "health": 200,
        "attack": 40,
        "defense": 20,
        "speed": 4,
        "prerequisites": ["hangar"]
    },
    {
        "id": "bomber",
        "name": "Heavy Bomber",
        "description": "Slow but powerful aircraft that deals massive damage.",
        "category": "air",
        "cost_credits": 400,
        "cost_minerals": 200,
        "cost_energy": 100,
        "train_time": 120,
        "health": 300,
        "attack": 80,
        "defense": 30,
        "speed": 2,
        "prerequisites": ["hangar", "advanced_aviation"]
    },
    {
        "id": "soldier",
        "name": "Sky Marine",
        "description": "Basic infantry unit for base defense.",
        "category": "infantry",
        "cost_credits": 50,
        "cost_minerals": 25,
        "cost_energy": 10,
        "train_time": 20,
        "health": 80,
        "attack": 15,
        "defense": 15,
        "speed": 1,
        "prerequisites": ["barracks"]
    },
    {
        "id": "heavy_gunner",
        "name": "Heavy Gunner",
        "description": "Specialized infantry with high attack power.",
        "category": "infantry",
        "cost_credits": 150,
        "cost_minerals": 75,
        "cost_energy": 30,
        "train_time": 45,
        "health": 120,
        "attack": 35,
        "defense": 25,
        "speed": 1,
        "prerequisites": ["barracks"]
    },
    {
        "id": "engineer",
        "name": "Combat Engineer",
        "description": "Support unit that can repair buildings and boost defenses.",
        "category": "infantry",
        "cost_credits": 200,
        "cost_minerals": 100,
        "cost_energy": 40,
        "train_time": 60,
        "health": 100,
        "attack": 10,
        "defense": 20,
        "speed": 1,
        "special": "repair",
        "prerequisites": ["barracks", "advanced_engineering"]
    }
]

# Technology research tree
TECH_TREE = [
    {
        "id": "advanced_materials",
        "name": "Advanced Materials",
        "description": "Improves building durability by 15%.",
        "cost_credits": 500,
        "cost_minerals": 250,
        "cost_energy": 100,
        "research_time": 300,  # seconds
        "prerequisites": []
    },
    {
        "id": "energy_efficiency",
        "name": "Energy Efficiency",
        "description": "Reduces energy costs of buildings by 10%.",
        "cost_credits": 400,
        "cost_minerals": 200,
        "cost_energy": 150,
        "research_time": 240,
        "prerequisites": []
    },
    {
        "id": "advanced_aviation",
        "name": "Advanced Aviation",
        "description": "Unlocks bomber units and improves air unit stats by 10%.",
        "cost_credits": 800,
        "cost_minerals": 400,
        "cost_energy": 200,
        "research_time": 480,
        "prerequisites": ["advanced_materials"]
    },
    {
        "id": "advanced_engineering",
        "name": "Advanced Engineering",
        "description": "Unlocks engineer units and improves building output by 15%.",
        "cost_credits": 600,
        "cost_minerals": 300,
        "cost_energy": 150,
        "research_time": 360,
        "prerequisites": ["energy_efficiency"]
    },
    {
        "id": "shield_technology",
        "name": "Shield Technology",
        "description": "Improves shield regeneration rate by 20%.",
        "cost_credits": 1000,
        "cost_minerals": 500,
        "cost_energy": 250,
        "research_time": 600,
        "prerequisites": ["advanced_materials", "energy_efficiency"]
    },
    {
        "id": "weapons_systems",
        "name": "Advanced Weapons",
        "description": "Increases attack power of all units by 15%.",
        "cost_credits": 1200,
        "cost_minerals": 600,
        "cost_energy": 300,
        "research_time": 720,
        "prerequisites": ["advanced_aviation"]
    },
    {
        "id": "resource_optimization",
        "name": "Resource Optimization",
        "description": "Increases resource production by 20%.",
        "cost_credits": 1500,
        "cost_minerals": 750,
        "cost_energy": 375,
        "research_time": 900,
        "prerequisites": ["advanced_engineering"]
    }
]
