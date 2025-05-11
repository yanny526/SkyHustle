"""
Game constants for SkyHustle
Defines building types, unit types, research tree, and other game elements
"""

# Building types and their properties
BUILDINGS = {
    "command_center": {
        "name": "Command Center",
        "description": "Central command structure for your sky base",
        "base_cost": {"credits": 500, "minerals": 300, "energy": 200},
        "cost_multiplier": 1.5,
        "build_time": 300,  # seconds
        "prerequisites": {},
        "provides": {
            "command_points": 5,
            "max_buildings": 2
        }
    },
    "mineral_extractor": {
        "name": "Mineral Extractor",
        "description": "Extracts minerals from clouds",
        "base_cost": {"credits": 200, "minerals": 100, "energy": 50},
        "cost_multiplier": 1.2,
        "build_time": 120,
        "prerequisites": {"command_center": 1},
        "provides": {
            "minerals_per_hour": 10
        }
    },
    "energy_collector": {
        "name": "Energy Collector",
        "description": "Collects solar and atmospheric energy",
        "base_cost": {"credits": 150, "minerals": 200, "energy": 0},
        "cost_multiplier": 1.2,
        "build_time": 120,
        "prerequisites": {"command_center": 1},
        "provides": {
            "energy_per_hour": 15
        }
    },
    "credit_mint": {
        "name": "Credit Mint",
        "description": "Generates credits through trade and finance",
        "base_cost": {"credits": 100, "minerals": 150, "energy": 100},
        "cost_multiplier": 1.2,
        "build_time": 150,
        "prerequisites": {"command_center": 1},
        "provides": {
            "credits_per_hour": 20
        }
    },
    "barracks": {
        "name": "Barracks",
        "description": "Training facility for infantry units",
        "base_cost": {"credits": 300, "minerals": 200, "energy": 100},
        "cost_multiplier": 1.3,
        "build_time": 180,
        "prerequisites": {"command_center": 1},
        "provides": {
            "max_infantry": 10,
            "training_speed": 1.0
        }
    },
    "hangar": {
        "name": "Hangar",
        "description": "Construction and maintenance bay for aerial units",
        "base_cost": {"credits": 400, "minerals": 300, "energy": 200},
        "cost_multiplier": 1.4,
        "build_time": 240,
        "prerequisites": {"command_center": 2, "barracks": 1},
        "provides": {
            "max_aerial": 5,
            "training_speed": 1.0
        }
    },
    "laboratory": {
        "name": "Laboratory",
        "description": "Research facility for new technologies",
        "base_cost": {"credits": 500, "minerals": 300, "energy": 400},
        "cost_multiplier": 1.5,
        "build_time": 300,
        "prerequisites": {"command_center": 2},
        "provides": {
            "research_speed": 1.0,
            "max_research": 1
        }
    },
    "defense_matrix": {
        "name": "Defense Matrix",
        "description": "Provides aerial defense for your base",
        "base_cost": {"credits": 400, "minerals": 500, "energy": 300},
        "cost_multiplier": 1.3,
        "build_time": 240,
        "prerequisites": {"command_center": 2},
        "provides": {
            "defense_bonus": 10,
            "attack_interception": 0.1  # 10% chance to intercept incoming attacks
        }
    },
    "radar_array": {
        "name": "Radar Array",
        "description": "Scans distant bases and increases visibility",
        "base_cost": {"credits": 300, "minerals": 200, "energy": 500},
        "cost_multiplier": 1.3,
        "build_time": 210,
        "prerequisites": {"command_center": 2},
        "provides": {
            "scan_range": 2,
            "scan_detail": 1
        }
    },
    "alliance_embassy": {
        "name": "Alliance Embassy",
        "description": "Enables alliance membership and coordination",
        "base_cost": {"credits": 1000, "minerals": 800, "energy": 600},
        "cost_multiplier": 1.4,
        "build_time": 600,
        "prerequisites": {"command_center": 3},
        "provides": {
            "alliance_contribution": 5,
            "alliance_position": "Member"
        }
    }
}

# Unit types and their properties
UNITS = {
    "sky_trooper": {
        "name": "Sky Trooper",
        "description": "Basic infantry unit with jetpacks",
        "category": "infantry",
        "base_cost": {"credits": 50, "minerals": 20, "energy": 10},
        "cost_multiplier": 1.1,
        "train_time": 60,
        "prerequisites": {"barracks": 1},
        "stats": {
            "attack": 5,
            "defense": 3,
            "health": 20,
            "speed": 1
        }
    },
    "tech_specialist": {
        "name": "Tech Specialist",
        "description": "Support unit that buffs allies and debuffs enemies",
        "category": "infantry",
        "base_cost": {"credits": 75, "minerals": 30, "energy": 40},
        "cost_multiplier": 1.2,
        "train_time": 90,
        "prerequisites": {"barracks": 2},
        "stats": {
            "attack": 2,
            "defense": 2,
            "health": 15,
            "speed": 1,
            "special": "tech_boost"
        }
    },
    "heavy_gunner": {
        "name": "Heavy Gunner",
        "description": "Slow but powerful infantry with heavy weaponry",
        "category": "infantry",
        "base_cost": {"credits": 100, "minerals": 60, "energy": 20},
        "cost_multiplier": 1.2,
        "train_time": 120,
        "prerequisites": {"barracks": 3},
        "stats": {
            "attack": 12,
            "defense": 5,
            "health": 30,
            "speed": 0.7
        }
    },
    "sky_bike": {
        "name": "Sky Bike",
        "description": "Fast reconnaissance aerial unit",
        "category": "aerial",
        "base_cost": {"credits": 150, "minerals": 100, "energy": 80},
        "cost_multiplier": 1.3,
        "train_time": 180,
        "prerequisites": {"hangar": 1},
        "stats": {
            "attack": 8,
            "defense": 6,
            "health": 25,
            "speed": 2.5
        }
    },
    "attack_drone": {
        "name": "Attack Drone",
        "description": "Automated aerial attack unit",
        "category": "aerial",
        "base_cost": {"credits": 200, "minerals": 120, "energy": 150},
        "cost_multiplier": 1.3,
        "train_time": 210,
        "prerequisites": {"hangar": 2},
        "stats": {
            "attack": 15,
            "defense": 8,
            "health": 35,
            "speed": 1.8
        }
    },
    "sky_fortress": {
        "name": "Sky Fortress",
        "description": "Heavy aerial unit with massive firepower",
        "category": "aerial",
        "base_cost": {"credits": 500, "minerals": 400, "energy": 300},
        "cost_multiplier": 1.4,
        "train_time": 600,
        "prerequisites": {"hangar": 3},
        "stats": {
            "attack": 30,
            "defense": 25,
            "health": 100,
            "speed": 0.5
        }
    }
}

# Research technology tree
RESEARCH = {
    "advanced_alloys": {
        "name": "Advanced Alloys",
        "description": "Stronger building materials",
        "level_effects": {
            1: {"building_health": 1.1},
            2: {"building_health": 1.2},
            3: {"building_health": 1.3}
        },
        "base_cost": {"credits": 200, "minerals": 300, "energy": 100},
        "cost_multiplier": 1.5,
        "research_time": 300,
        "prerequisites": {"laboratory": 1}
    },
    "energy_efficiency": {
        "name": "Energy Efficiency",
        "description": "Reduces energy costs for all operations",
        "level_effects": {
            1: {"energy_cost": 0.95},
            2: {"energy_cost": 0.9},
            3: {"energy_cost": 0.85}
        },
        "base_cost": {"credits": 300, "minerals": 100, "energy": 200},
        "cost_multiplier": 1.5,
        "research_time": 300,
        "prerequisites": {"laboratory": 1}
    },
    "aerial_dynamics": {
        "name": "Aerial Dynamics",
        "description": "Improved flight systems for aerial units",
        "level_effects": {
            1: {"aerial_speed": 1.1, "aerial_attack": 1.05},
            2: {"aerial_speed": 1.2, "aerial_attack": 1.1},
            3: {"aerial_speed": 1.3, "aerial_attack": 1.15}
        },
        "base_cost": {"credits": 400, "minerals": 200, "energy": 300},
        "cost_multiplier": 1.6,
        "research_time": 450,
        "prerequisites": {"laboratory": 2, "hangar": 1}
    },
    "weapons_tech": {
        "name": "Weapons Technology",
        "description": "Enhanced weapons for all units",
        "level_effects": {
            1: {"unit_attack": 1.1},
            2: {"unit_attack": 1.2},
            3: {"unit_attack": 1.3}
        },
        "base_cost": {"credits": 500, "minerals": 400, "energy": 200},
        "cost_multiplier": 1.6,
        "research_time": 480,
        "prerequisites": {"laboratory": 2, "barracks": 2}
    },
    "defense_systems": {
        "name": "Defense Systems",
        "description": "Improved defensive capabilities",
        "level_effects": {
            1: {"unit_defense": 1.1, "building_defense": 1.05},
            2: {"unit_defense": 1.2, "building_defense": 1.1},
            3: {"unit_defense": 1.3, "building_defense": 1.15}
        },
        "base_cost": {"credits": 400, "minerals": 500, "energy": 200},
        "cost_multiplier": 1.6,
        "research_time": 480,
        "prerequisites": {"laboratory": 2, "defense_matrix": 1}
    },
    "resource_optimization": {
        "name": "Resource Optimization",
        "description": "More efficient resource production",
        "level_effects": {
            1: {"resource_production": 1.05},
            2: {"resource_production": 1.1},
            3: {"resource_production": 1.15}
        },
        "base_cost": {"credits": 600, "minerals": 300, "energy": 400},
        "cost_multiplier": 1.5,
        "research_time": 420,
        "prerequisites": {"laboratory": 2, "mineral_extractor": 2, "energy_collector": 2}
    },
    "advanced_scanning": {
        "name": "Advanced Scanning",
        "description": "Enhanced radar capabilities for better target selection",
        "level_effects": {
            1: {"scan_range": 1, "scan_detail": 1},
            2: {"scan_range": 2, "scan_detail": 2},
            3: {"scan_range": 3, "scan_detail": 3}
        },
        "base_cost": {"credits": 300, "minerals": 300, "energy": 600},
        "cost_multiplier": 1.5,
        "research_time": 360,
        "prerequisites": {"laboratory": 2, "radar_array": 1}
    },
    "advanced_infantry": {
        "name": "Advanced Infantry",
        "description": "Elite infantry training and equipment",
        "level_effects": {
            1: {"infantry_attack": 1.1, "infantry_health": 1.05},
            2: {"infantry_attack": 1.2, "infantry_health": 1.1},
            3: {"infantry_attack": 1.3, "infantry_health": 1.15}
        },
        "base_cost": {"credits": 800, "minerals": 500, "energy": 400},
        "cost_multiplier": 1.7,
        "research_time": 600,
        "prerequisites": {"laboratory": 3, "barracks": 3, "weapons_tech": 1}
    },
    "advanced_aerial": {
        "name": "Advanced Aerial",
        "description": "Cutting-edge aerial unit technology",
        "level_effects": {
            1: {"aerial_attack": 1.1, "aerial_health": 1.05},
            2: {"aerial_attack": 1.2, "aerial_health": 1.1},
            3: {"aerial_attack": 1.3, "aerial_health": 1.15}
        },
        "base_cost": {"credits": 1000, "minerals": 600, "energy": 800},
        "cost_multiplier": 1.7,
        "research_time": 720,
        "prerequisites": {"laboratory": 3, "hangar": 3, "aerial_dynamics": 1}
    }
}

# Achievement types
ACHIEVEMENTS = {
    "base_builder": {
        "name": "Base Builder",
        "description": "Build a total of {target} structures",
        "levels": {
            1: {"target": 5, "reward": {"credits": 100}},
            2: {"target": 20, "reward": {"credits": 300}},
            3: {"target": 50, "reward": {"credits": 500, "skybucks": 5}}
        }
    },
    "resource_magnate": {
        "name": "Resource Magnate",
        "description": "Accumulate {target} total resources",
        "levels": {
            1: {"target": 1000, "reward": {"minerals": 100}},
            2: {"target": 5000, "reward": {"minerals": 300}},
            3: {"target": 20000, "reward": {"minerals": 500, "skybucks": 5}}
        }
    },
    "army_general": {
        "name": "Army General",
        "description": "Train {target} total units",
        "levels": {
            1: {"target": 10, "reward": {"energy": 100}},
            2: {"target": 50, "reward": {"energy": 300}},
            3: {"target": 200, "reward": {"energy": 500, "skybucks": 5}}
        }
    },
    "battle_master": {
        "name": "Battle Master",
        "description": "Win {target} battles",
        "levels": {
            1: {"target": 5, "reward": {"credits": 200}},
            2: {"target": 25, "reward": {"credits": 500}},
            3: {"target": 100, "reward": {"credits": 1000, "skybucks": 10}}
        }
    },
    "tech_pioneer": {
        "name": "Tech Pioneer",
        "description": "Research {target} technologies",
        "levels": {
            1: {"target": 3, "reward": {"energy": 200}},
            2: {"target": 10, "reward": {"energy": 500}},
            3: {"target": 20, "reward": {"energy": 1000, "skybucks": 10}}
        }
    },
    "alliance_diplomat": {
        "name": "Alliance Diplomat",
        "description": "Participate in {target} alliance activities",
        "levels": {
            1: {"target": 5, "reward": {"minerals": 200}},
            2: {"target": 20, "reward": {"minerals": 500}},
            3: {"target": 50, "reward": {"minerals": 1000, "skybucks": 10}}
        }
    }
}

# Tutorial steps
TUTORIAL_STEPS = [
    {
        "id": "welcome",
        "message": "Welcome to SkyHustle, Commander! I'll guide you through the basics of managing your aerial base. Let's get started!",
        "next_instruction": "First, check your base status with the /status command."
    },
    {
        "id": "status_check",
        "message": "Great! This is your base status. You can see your resources, buildings, and units here.\n\nNow let's build your first structure. Try the /build command to see available buildings.",
        "next_instruction": "Use /build command to see what you can construct."
    },
    {
        "id": "build_instruction",
        "message": "Excellent! Let's build a Mineral Extractor to start gathering resources. Use the command /build mineral_extractor or select it from the menu.",
        "next_instruction": "Build your first Mineral Extractor."
    },
    {
        "id": "first_build",
        "message": "Your Mineral Extractor is under construction! Once completed, it will generate minerals automatically.\n\nNow let's train your first units. Try the /train command to see available units.",
        "next_instruction": "Use /train command to see what units you can train."
    },
    {
        "id": "train_instruction",
        "message": "Perfect! Let's train some Sky Troopers to defend your base. Use the command /train sky_trooper 2 to train 2 Sky Troopers.",
        "next_instruction": "Train 2 Sky Troopers for your base."
    },
    {
        "id": "first_train",
        "message": "Your Sky Troopers are being trained! They'll be ready to defend your base soon.\n\nFinally, let's set a name for your base. Use the /setname command followed by the name you want.",
        "next_instruction": "Set a name for your base using /setname <your_base_name>."
    },
    {
        "id": "set_name",
        "message": "Perfect! Your base now has a name that will be displayed to other players.\n\nYou've completed the basic tutorial! Here's a bonus of resources to help you get started.",
        "next_instruction": "You can check your updated status with /status or explore other commands with /help."
    }
]

# Response messages and templates
MESSAGES = {
    "welcome": "Welcome to SkyHustle, Commander! Build your aerial base, train your army, and dominate the skies!",
    "tutorial_start": "Welcome to the SkyHustle tutorial! I'll guide you through the basics of the game. Let's get started!",
    "tutorial_skip": "Tutorial skipped. You can always start it again with /tutorial start.",
    "tutorial_completed": "Tutorial completed! You've learned the basics of SkyHustle. Good luck, Commander!",
    "error_invalid_command": "❌ Invalid command. Try /help for a list of commands.",
    "error_insufficient_resources": "❌ Insufficient resources for this action.",
    "error_invalid_building": "❌ Invalid building type. Use /build to see available buildings.",
    "error_invalid_unit": "❌ Invalid unit type. Use /train to see available units.",
    "error_invalid_research": "❌ Invalid research type. Use /research to see available technologies.",
    "error_prerequisites_not_met": "❌ Prerequisites not met for this action.",
    "error_max_queue": "❌ Build queue is full. Maximum queue length is {max_queue}.",
    "error_name_too_long": "❌ Name too long. Maximum length is {max_length} characters.",
    "error_name_format": "❌ Name must contain only alphanumeric characters and spaces.",
    "error_name_taken": "❌ This name is already taken. Please choose another one.",
    "success_build": "✅ Building {quantity}x {building_name} - Construction will complete in {time}.",
    "success_train": "✅ Training {quantity}x {unit_name} - Training will complete in {time}.",
    "success_research": "✅ Researching {tech_name} - Research will complete in {time}.",
    "success_name_set": "✅ Base name set to {name}.",
    "success_alliance_create": "✅ Alliance {name} created successfully! Alliance code: {code}",
    "success_alliance_join": "✅ You have joined the alliance {name}!",
    "success_attack": "✅ Attack launched against {target_name}. Battle report: {result}",
    "success_daily": "✅ Daily reward claimed! You received: {rewards}",
    "info_status": "ℹ️ **Base Status:**\n{status_details}",
    "info_buildings": "ℹ️ **Available Buildings:**\n{buildings_list}",
    "info_units": "ℹ️ **Available Units:**\n{units_list}",
    "info_research": "ℹ️ **Available Technologies:**\n{research_list}",
    "info_leaderboard": "ℹ️ **Leaderboard ({scope}):**\n{leaderboard_entries}",
    "info_scan": "ℹ️ **Scan Results:**\n{scan_results}",
    "info_alliance": "ℹ️ **Alliance Information:**\n{alliance_details}",
    "info_war": "ℹ️ **War Status:**\n{war_details}",
    "info_achievements": "ℹ️ **Achievements:**\n{achievements_list}",
    "info_events": "ℹ️ **Active Events:**\n{events_list}",
    "info_help": "ℹ️ **Available Commands:**\n{commands_list}"
}

# Weather messages (just for fun)
WEATHER_MESSAGES = [
    "The skies are clear today. Perfect visibility for aerial operations!",
    "Light cloud cover detected. Slight visibility reduction, but otherwise favorable conditions.",
    "Heavy cloud formations approaching. Expect reduced solar energy collection efficiency.",
    "Electrical storm detected in your sector. Energy collectors operating at 120% efficiency!",
    "High winds reported. Aerial unit speed temporarily increased by 10%.",
    "Rare mineral-rich cloud formation detected! Mineral extractors operating at 115% efficiency.",
    "Dense fog reported. Radar systems temporarily reduced in effectiveness.",
    "Unusual cosmic radiation levels. Research speed temporarily increased by 5%.",
    "Beautiful sunset reported. Morale boost: all construction speeds increased by 3%.",
    "Meteor shower expected tonight. No gameplay effects, but it's a spectacular sight!"
]
