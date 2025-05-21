"""
Game configuration and constants for SkyHustle 2
"""

# Resource Types
RESOURCES = {
    'wood': {
        'name': 'Wood',
        'emoji': '🪵',
        'base_production': 10,  # per minute
    },
    'stone': {
        'name': 'Stone',
        'emoji': '🪨',
        'base_production': 5,   # per minute
    },
    'gold': {
        'name': 'Gold',
        'emoji': '💰',
        'base_production': 2,   # per minute
    },
    'food': {
        'name': 'Food',
        'emoji': '🍖',
        'base_production': 15,  # per minute
    }
}

# Building Definitions
BUILDINGS = {
    'lumberhouse': {
        'name': 'Lumberhouse',
        'emoji': '🏭',
        'description': 'Produces wood for your base',
        'base_cost': {
            'wood': 100,
            'stone': 50,
            'gold': 0,
            'food': 0
        },
        'production': {
            'wood': 10  # base production per minute
        },
        'max_level': 20
    },
    'mine': {
        'name': 'Mine',
        'emoji': '⛏️',
        'description': 'Produces stone and gold',
        'base_cost': {
            'wood': 150,
            'stone': 100,
            'gold': 0,
            'food': 0
        },
        'production': {
            'stone': 5,
            'gold': 2
        },
        'max_level': 20
    },
    'warehouse': {
        'name': 'Warehouse',
        'emoji': '🏪',
        'description': 'Stores food and increases food production',
        'base_cost': {
            'wood': 200,
            'stone': 100,
            'gold': 50,
            'food': 0
        },
        'production': {
            'food': 15
        },
        'max_level': 20
    },
    'barracks': {
        'name': 'Barracks',
        'emoji': '🏰',
        'description': 'Trains military units',
        'base_cost': {
            'wood': 300,
            'stone': 200,
            'gold': 100,
            'food': 0
        },
        'max_level': 20
    },
    'research_center': {
        'name': 'Research Center',
        'emoji': '🔬',
        'description': 'Unlocks new technologies and upgrades',
        'base_cost': {
            'wood': 400,
            'stone': 300,
            'gold': 200,
            'food': 0
        },
        'max_level': 20
    },
    'defense_tower': {
        'name': 'Defense Tower',
        'emoji': '🏰',
        'description': 'Protects your base from attacks',
        'base_cost': {
            'wood': 250,
            'stone': 200,
            'gold': 150,
            'food': 0
        },
        'defense_bonus': 1.1,  # 10% defense bonus per level
        'max_level': 20
    }
}

# Unit Definitions
UNITS = {
    'infantry': {
        'name': 'Infantry',
        'emoji': '👥',
        'description': 'Basic military unit',
        'base_cost': {
            'wood': 50,
            'stone': 20,
            'gold': 10,
            'food': 5
        },
        'stats': {
            'attack': 10,
            'defense': 5,
            'hp': 100,
            'speed': 1
        },
        'training_time': 60  # seconds
    },
    'tank': {
        'name': 'Tank',
        'emoji': '🛡️',
        'description': 'Heavy armored unit',
        'base_cost': {
            'wood': 100,
            'stone': 150,
            'gold': 200,
            'food': 10
        },
        'stats': {
            'attack': 25,
            'defense': 20,
            'hp': 300,
            'speed': 0.5
        },
        'training_time': 180  # seconds
    },
    'archer': {
        'name': 'Archer',
        'emoji': '🏹',
        'description': 'Long-range unit',
        'base_cost': {
            'wood': 75,
            'stone': 50,
            'gold': 75,
            'food': 8
        },
        'stats': {
            'attack': 15,
            'defense': 8,
            'hp': 80,
            'speed': 1.2,
            'range': 2
        },
        'training_time': 90  # seconds
    },
    'cavalry': {
        'name': 'Cavalry',
        'emoji': '🐎',
        'description': 'Fast-moving unit',
        'base_cost': {
            'wood': 150,
            'stone': 100,
            'gold': 150,
            'food': 15
        },
        'stats': {
            'attack': 20,
            'defense': 15,
            'hp': 150,
            'speed': 2
        },
        'training_time': 120  # seconds
    }
}

# Research Definitions
RESEARCH = {
    'military': {
        'tier1': {
            'name': 'Basic Military Training',
            'description': 'Improves basic unit stats',
            'base_cost': {
                'wood': 200,
                'stone': 100,
                'gold': 50,
                'food': 0
            },
            'effects': {
                'unit_attack': 1.1,  # 10% attack bonus
                'unit_defense': 1.1   # 10% defense bonus
            },
            'research_time': 300  # seconds
        }
    }
}

# Quest Definitions
QUESTS = {
    'first_building': {
        'name': 'First Steps',
        'description': 'Build your first building',
        'target': 1,
        'reward': {
            'gold': 100,
            'xp': 50
        },
        'emoji': '🏗️'
    },
    'resource_master': {
        'name': 'Resource Master',
        'description': 'Collect 1000 resources in total',
        'target': 1000,
        'reward': {
            'gold': 200,
            'xp': 100
        },
        'emoji': '📦'
    },
    'military_power': {
        'name': 'Military Power',
        'description': 'Train 10 military units',
        'target': 10,
        'reward': {
            'gold': 300,
            'xp': 150
        },
        'emoji': '⚔️'
    },
    'combat_veteran': {
        'name': 'Combat Veteran',
        'description': 'Win 10 battles',
        'target': 10,
        'reward': {
            'gold': 500,
            'xp': 250
        },
        'emoji': '🏆'
    },
    'league_champion': {
        'name': 'League Champion',
        'description': 'Reach the top 100 in the league',
        'target': 1,
        'reward': {
            'gold': 1000,
            'xp': 500,
            'hustlecoins': 5
        },
        'emoji': '👑'
    }
}

# Achievement Definitions
ACHIEVEMENTS = {
    'first_building': {
        'name': 'First Steps',
        'description': 'Build your first building',
        'emoji': '🏗️',
        'reward': {'coins': 100}
    },
    'resource_master': {
        'name': 'Resource Master',
        'description': 'Collect 1000 of any resource',
        'emoji': '📦',
        'reward': {'coins': 500}
    },
    'military_power': {
        'name': 'Military Power',
        'description': 'Train 10 military units',
        'emoji': '⚔️',
        'reward': {'coins': 300}
    },
    'combat_veteran': {
        'name': 'Combat Veteran',
        'description': 'Win 10 battles',
        'emoji': '🏆',
        'reward': {'coins': 1000, 'hustlecoins': 5}
    },
    'league_champion': {
        'name': 'League Champion',
        'description': 'Reach the top league',
        'emoji': '👑',
        'reward': {'coins': 2000, 'hustlecoins': 10}
    }
}

# Daily Rewards Configuration
DAILY_REWARDS = {
    1: {'coins': 100, 'hustlecoins': 1},
    2: {'coins': 200, 'hustlecoins': 1},
    3: {'coins': 300, 'hustlecoins': 1},
    4: {'coins': 400, 'hustlecoins': 1},
    5: {'coins': 500, 'hustlecoins': 2},
    6: {'coins': 600, 'hustlecoins': 2},
    7: {'coins': 1000, 'hustlecoins': 5}  # Special 7th day reward
}

# Special Events
EVENTS = {
    'resource_boost': {
        'name': 'Resource Rush',
        'emoji': '⚡',
        'description': 'Double resource production for 1 hour',
        'duration': 3600,  # 1 hour in seconds
        'effect': {
            'wood_production': 2.0,
            'stone_production': 2.0,
            'gold_production': 2.0
        }
    },
    'training_boost': {
        'name': 'Rapid Training',
        'emoji': '⚔️',
        'description': '50% faster unit training for 30 minutes',
        'duration': 1800,  # 30 minutes in seconds
        'effect': {
            'training_speed': 1.5
        }
    },
    'combat_boost': {
        'name': 'Battle Rush',
        'emoji': '⚔️',
        'description': '25% increased attack power for 1 hour',
        'duration': 3600,  # 1 hour in seconds
        'effect': {
            'attack_power': 1.25
        }
    }
}

# Combat Settings
COMBAT = {
    'base_rating': 1000,  # Starting rating for new players
    'rating_change': {
        'base': 30,  # Base rating change per battle
        'min': 5,    # Minimum rating change
        'max': 50    # Maximum rating change
    },
    'leagues': {
        'bronze': {
            'min_rating': 0,
            'max_rating': 1000,
            'reward_multiplier': 1.0
        },
        'silver': {
            'min_rating': 1001,
            'max_rating': 2000,
            'reward_multiplier': 1.2
        },
        'gold': {
            'min_rating': 2001,
            'max_rating': 3000,
            'reward_multiplier': 1.5
        },
        'platinum': {
            'min_rating': 3001,
            'max_rating': 4000,
            'reward_multiplier': 2.0
        },
        'diamond': {
            'min_rating': 4001,
            'max_rating': float('inf'),
            'reward_multiplier': 3.0
        }
    },
    'battle_cooldown': 300,  # 5 minutes between battles
    'resource_steal_ratio': 0.1,  # 10% of resources can be stolen
    'defense_bonus': {
        'base': 1.1,  # 10% defense bonus for defending
        'per_tower': 0.05  # 5% additional bonus per defense tower
    }
}

# Alliance Settings
ALLIANCE_SETTINGS = {
    'max_alliances': 100,  # Maximum number of alliances in the game
    'max_members': 50,     # Maximum members per alliance
    'min_level': 5,        # Minimum player level to create an alliance
    'xp_per_resource': 1,  # XP gained per resource donated
    'xp_per_level': 1000,  # XP needed per alliance level
    'war_cooldown': 86400, # 24 hours between war declarations
    'war_duration': 604800 # 7 days war duration
}

# Quest Settings
QUEST_SETTINGS = {
    'refresh_cooldown': 86400,  # 24 hours between quest refreshes
    'quest_duration': 172800,   # 48 hours quest duration
    'quests_per_refresh': 3,    # Number of quests per refresh
    'max_active_quests': 5      # Maximum number of active quests
}

# Quest Types
QUEST_TYPES = {
    'gather_wood': {
        'name': 'Wood Gatherer',
        'description': 'Gather {target} wood',
        'min_target': 100,
        'max_target': 1000,
        'emoji': '🪵'
    },
    'gather_stone': {
        'name': 'Stone Collector',
        'description': 'Gather {target} stone',
        'min_target': 50,
        'max_target': 500,
        'emoji': '🪨'
    },
    'gather_gold': {
        'name': 'Gold Miner',
        'description': 'Gather {target} gold',
        'min_target': 20,
        'max_target': 200,
        'emoji': '💰'
    },
    'gather_food': {
        'name': 'Food Hunter',
        'description': 'Gather {target} food',
        'min_target': 150,
        'max_target': 1500,
        'emoji': '🍖'
    },
    'build_structures': {
        'name': 'Master Builder',
        'description': 'Build or upgrade {target} structures',
        'min_target': 1,
        'max_target': 10,
        'emoji': '🏗️'
    },
    'train_units': {
        'name': 'Army Commander',
        'description': 'Train {target} military units',
        'min_target': 5,
        'max_target': 50,
        'emoji': '⚔️'
    },
    'win_battles': {
        'name': 'Battle Champion',
        'description': 'Win {target} battles',
        'min_target': 1,
        'max_target': 10,
        'emoji': '🏆'
    },
    'complete_research': {
        'name': 'Master Researcher',
        'description': 'Complete {target} research projects',
        'min_target': 1,
        'max_target': 5,
        'emoji': '🔬'
    },
    'donate_resources': {
        'name': 'Generous Donor',
        'description': 'Donate {target} resources to your alliance',
        'min_target': 100,
        'max_target': 1000,
        'emoji': '🎁'
    }
}

# Quest Rewards
QUEST_REWARDS = {
    'gather_wood': {
        'wood': 200,
        'gold': 50
    },
    'gather_stone': {
        'stone': 100,
        'gold': 50
    },
    'gather_gold': {
        'gold': 100
    },
    'gather_food': {
        'food': 300,
        'gold': 50
    },
    'build_structures': {
        'wood': 300,
        'stone': 200,
        'gold': 100
    },
    'train_units': {
        'gold': 200,
        'food': 100
    },
    'win_battles': {
        'gold': 300,
        'wood': 200,
        'stone': 200
    },
    'complete_research': {
        'gold': 400,
        'wood': 300,
        'stone': 300
    },
    'donate_resources': {
        'gold': 500,
        'wood': 400,
        'stone': 400
    }
}

# Market Settings
MARKET_SETTINGS = {
    'max_listings_per_player': 5,  # Maximum number of active listings per player
    'listing_duration': 86400,     # 24 hours listing duration
    'trade_fee': 0.05,            # 5% fee on trades
    'min_listing_value': 100,     # Minimum value for a listing (in gold)
    'max_listing_value': 10000,   # Maximum value for a listing (in gold)
    'event_cooldown': 604800      # 7 days between market events
}

# Market Events
MARKET_EVENTS = {
    'trade_festival': {
        'name': 'Trade Festival',
        'description': 'Reduced trading fees and increased listing limits',
        'duration': 86400,  # 24 hours
        'bonus': {
            'trade_fee': 0.5,  # 50% reduced fees
            'max_listings': 2   # Double listing limit
        }
    },
    'resource_rush': {
        'name': 'Resource Rush',
        'description': 'Special resource trading bonuses',
        'duration': 43200,  # 12 hours
        'bonus': {
            'wood_value': 1.2,   # 20% increased wood value
            'stone_value': 1.2,  # 20% increased stone value
            'gold_value': 1.1    # 10% increased gold value
        }
    },
    'market_crash': {
        'name': 'Market Crash',
        'description': 'Temporary market instability with fluctuating prices',
        'duration': 21600,  # 6 hours
        'bonus': {
            'price_volatility': 0.3,  # 30% price fluctuation
            'trade_volume': 2.0       # Double trade volume required
        }
    }
}

GAME_SETTINGS = {
    'starting_gold': 100,
    'starting_wood': 200,
    'starting_stone': 100,
    'starting_food': 300
}

# Research Types and Categories
RESEARCH_TYPES = {
    'military': {
        'name': 'Military Research',
        'emoji': '⚔️',
        'description': 'Improve your military capabilities',
        'categories': ['combat', 'training', 'defense']
    },
    'economy': {
        'name': 'Economic Research',
        'emoji': '💰',
        'description': 'Enhance resource production and efficiency',
        'categories': ['production', 'storage', 'trade']
    },
    'technology': {
        'name': 'Technology Research',
        'emoji': '🔬',
        'description': 'Unlock new technologies and upgrades',
        'categories': ['buildings', 'units', 'special']
    }
}

# Research Rewards
RESEARCH_REWARDS = {
    'military': {
        'combat': {
            'attack_bonus': 0.1,  # 10% attack bonus
            'defense_bonus': 0.1  # 10% defense bonus
        },
        'training': {
            'speed_bonus': 0.15,  # 15% training speed bonus
            'cost_reduction': 0.1  # 10% cost reduction
        },
        'defense': {
            'tower_bonus': 0.2,   # 20% tower defense bonus
            'wall_bonus': 0.15    # 15% wall defense bonus
        }
    },
    'economy': {
        'production': {
            'resource_bonus': 0.2,  # 20% resource production bonus
            'efficiency_bonus': 0.15 # 15% efficiency bonus
        },
        'storage': {
            'capacity_bonus': 0.25,  # 25% storage capacity bonus
            'protection_bonus': 0.2   # 20% resource protection bonus
        },
        'trade': {
            'fee_reduction': 0.1,    # 10% trading fee reduction
            'value_bonus': 0.15      # 15% resource value bonus
        }
    }
}

# Building Upgrades
BUILDING_UPGRADES = {
    'cost_multiplier': 1.5,  # Each level costs 50% more
    'production_multiplier': 1.2,  # Each level produces 20% more
    'max_level': 20,
    'upgrade_time_multiplier': 1.3,  # Each level takes 30% longer to upgrade
    'base_upgrade_time': 300  # 5 minutes base upgrade time
}

# Unit Upgrades
UNIT_UPGRADES = {
    'cost_multiplier': 1.4,  # Each level costs 40% more
    'stats_multiplier': 1.15,  # Each level improves stats by 15%
    'max_level': 10,
    'training_time_multiplier': 1.2,  # Each level takes 20% longer to train
    'base_training_time': 60  # 1 minute base training time
}

# League Rewards
LEAGUE_REWARDS = {
    'bronze': {
        'daily': {'gold': 100, 'hustlecoins': 1},
        'weekly': {'gold': 500, 'hustlecoins': 5},
        'monthly': {'gold': 2000, 'hustlecoins': 20}
    },
    'silver': {
        'daily': {'gold': 200, 'hustlecoins': 2},
        'weekly': {'gold': 1000, 'hustlecoins': 10},
        'monthly': {'gold': 4000, 'hustlecoins': 40}
    },
    'gold': {
        'daily': {'gold': 300, 'hustlecoins': 3},
        'weekly': {'gold': 1500, 'hustlecoins': 15},
        'monthly': {'gold': 6000, 'hustlecoins': 60}
    },
    'platinum': {
        'daily': {'gold': 400, 'hustlecoins': 4},
        'weekly': {'gold': 2000, 'hustlecoins': 20},
        'monthly': {'gold': 8000, 'hustlecoins': 80}
    },
    'diamond': {
        'daily': {'gold': 500, 'hustlecoins': 5},
        'weekly': {'gold': 2500, 'hustlecoins': 25},
        'monthly': {'gold': 10000, 'hustlecoins': 100}
    }
}

# Alliance Perks
ALLIANCE_PERKS = {
    'resource_bonus': {
        'name': 'Resource Boost',
        'description': 'Increases resource production for all members',
        'levels': {
            1: {'bonus': 0.05},  # 5% bonus
            2: {'bonus': 0.10},  # 10% bonus
            3: {'bonus': 0.15}   # 15% bonus
        }
    },
    'training_bonus': {
        'name': 'Rapid Training',
        'description': 'Reduces unit training time',
        'levels': {
            1: {'bonus': 0.10},  # 10% faster
            2: {'bonus': 0.20},  # 20% faster
            3: {'bonus': 0.30}   # 30% faster
        }
    },
    'research_bonus': {
        'name': 'Research Boost',
        'description': 'Reduces research time',
        'levels': {
            1: {'bonus': 0.10},  # 10% faster
            2: {'bonus': 0.20},  # 20% faster
            3: {'bonus': 0.30}   # 30% faster
        }
    }
}

# Alliance Ranks
ALLIANCE_RANKS = {
    'leader': {
        'name': 'Leader',
        'permissions': [
            'manage_members',
            'manage_ranks',
            'declare_war',
            'manage_alliance',
            'manage_perks',
            'manage_resources'
        ]
    },
    'officer': {
        'name': 'Officer',
        'permissions': [
            'manage_members',
            'manage_ranks',
            'manage_resources'
        ]
    },
    'veteran': {
        'name': 'Veteran',
        'permissions': [
            'manage_resources'
        ]
    },
    'member': {
        'name': 'Member',
        'permissions': [
            'view_alliance',
            'donate_resources'
        ]
    }
} 