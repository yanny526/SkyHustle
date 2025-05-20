"""
Alliance configuration settings for SkyHustle 2
"""

ALLIANCE_SETTINGS = {
    'max_alliances': 100,  # Maximum number of alliances in the game
    'max_members': 50,     # Maximum members per alliance
    'min_level': 5,        # Minimum player level to create an alliance
    'xp_per_resource': 1,  # XP gained per resource donated
    'xp_per_level': 1000,  # XP needed per alliance level
    'war_cooldown': 86400, # 24 hours between war declarations
    'war_duration': 604800 # 7 days war duration
}

ALLIANCE_RANKS = {
    'leader': {
        'name': 'Leader',
        'permissions': ['manage_members', 'declare_war', 'manage_roles', 'manage_resources']
    },
    'officer': {
        'name': 'Officer',
        'permissions': ['manage_members', 'manage_resources']
    },
    'veteran': {
        'name': 'Veteran',
        'permissions': ['manage_resources']
    },
    'member': {
        'name': 'Member',
        'permissions': []
    }
}

ALLIANCE_BENEFITS = {
    'resource_bonus': 0.1,  # 10% resource production bonus
    'research_bonus': 0.05, # 5% research speed bonus
    'defense_bonus': 0.15,  # 15% defense bonus
    'attack_bonus': 0.1     # 10% attack bonus
}

ALLIANCE_WAR_SETTINGS = {
    'min_members': 5,       # Minimum members to declare war
    'max_active_wars': 3,   # Maximum active wars per alliance
    'victory_points': {
        'resource_steal': 1,
        'building_destroy': 5,
        'unit_kill': 2
    }
}

ALLIANCE_SETTINGS = {
    # Member limits
    'max_members': 50,
    'min_members_for_war': 5,
    
    # Level progression
    'xp_per_level': 1000,
    'xp_per_resource': 1,
    'max_level': 50,
    
    # War settings
    'war_duration': 7 * 24 * 3600,  # 7 days in seconds
    'war_preparation_time': 24 * 3600,  # 24 hours in seconds
    'war_cooldown': 3 * 24 * 3600,  # 3 days in seconds
    'min_level_for_war': 5,
    'max_active_wars': 1,
    'battle_cooldown': 3600,  # 1 hour in seconds
    'max_battles_per_day': 10,
    
    # Resource donation limits
    'max_daily_donation': 1000,
    'donation_cooldown': 3600,  # 1 hour in seconds
    
    # Officer settings
    'max_officers': 5,
    'promotion_cooldown': 24 * 3600,  # 24 hours in seconds
    
    # Alliance benefits
    'resource_bonus_per_level': 0.05,  # 5% per level
    'xp_bonus_per_level': 0.02,  # 2% per level
    'production_bonus_per_level': 0.02,  # 2% per level
    'research_bonus_per_level': 0.01,  # 1% per level
    'combat_bonus_per_level': 0.015,  # 1.5% per level
    'defense_bonus_per_level': 0.015,  # 1.5% per level
    
    # XP milestone bonuses
    'xp_milestones': [
        {'xp': 10000, 'bonus': 0.05},  # 5% bonus at 10k XP
        {'xp': 50000, 'bonus': 0.05},  # 5% bonus at 50k XP
        {'xp': 100000, 'bonus': 0.05},  # 5% bonus at 100k XP
        {'xp': 500000, 'bonus': 0.05},  # 5% bonus at 500k XP
        {'xp': 1000000, 'bonus': 0.05},  # 5% bonus at 1M XP
    ],
    
    # Alliance perks
    'perks': {
        'resource_master': {
            'name': 'Resource Master',
            'description': 'Increases resource production by 10%',
            'cost': 50000,  # XP cost
            'bonus': {'resource_bonus': 0.10}
        },
        'research_expert': {
            'name': 'Research Expert',
            'description': 'Reduces research time by 15%',
            'cost': 75000,
            'bonus': {'research_bonus': 0.15}
        },
        'combat_veteran': {
            'name': 'Combat Veteran',
            'description': 'Increases combat power by 15%',
            'cost': 100000,
            'bonus': {'combat_bonus': 0.15}
        },
        'defense_specialist': {
            'name': 'Defense Specialist',
            'description': 'Increases defense power by 15%',
            'cost': 100000,
            'bonus': {'defense_bonus': 0.15}
        },
        'xp_boost': {
            'name': 'XP Boost',
            'description': 'Increases XP gain by 10%',
            'cost': 50000,
            'bonus': {'xp_bonus': 0.10}
        }
    },
    
    # Chat settings
    'max_chat_messages': 100,
    'chat_cooldown': 5,  # 5 seconds
    
    # Alliance creation
    'creation_cost': {
        'gold': 10000,
        'wood': 5000,
        'stone': 3000
    },
    'min_level_to_create': 10,
    
    # War rewards
    'war_rewards': {
        'winner': {
            'gold_multiplier': 1000,
            'wood_multiplier': 500,
            'stone_multiplier': 300,
            'food_multiplier': 800,
            'xp_multiplier': 100
        },
        'loser': {
            'gold_multiplier': 500,
            'wood_multiplier': 250,
            'stone_multiplier': 150,
            'food_multiplier': 400,
            'xp_multiplier': 50
        }
    },
    
    # War battle settings
    'battle_settings': {
        'min_units_per_battle': 5,
        'max_units_per_battle': 100,
        'power_calculation': {
            'attack_weight': 0.6,
            'defense_weight': 0.4
        },
        'random_factor': {
            'min': 0.8,
            'max': 1.2
        }
    },
    
    # War scoring
    'scoring': {
        'win_points': 3,
        'draw_points': 1,
        'loss_points': 0,
        'bonus_points': {
            'first_blood': 2,
            'perfect_victory': 5,
            'comeback': 3
        }
    },
    
    'research': {
        'max_active_projects': 1,
        'contribution_cooldown': 3600,  # 1 hour
        'min_contribution': 100,
        'max_contribution_per_day': 10000,
        'benefits': {
            'resource_production': 0.05,  # 5% increase per level
            'research_speed': 0.10,  # 10% faster research
            'combat_power': 0.08,  # 8% more combat power
            'defense_power': 0.08,  # 8% more defense power
            'resource_storage': 0.15,  # 15% more storage
            'unit_training': 0.12,  # 12% faster training
        },
        'categories': {
            'economy': {
                'name': 'Economic Research',
                'description': 'Improve resource production and storage',
                'icon': '💰'
            },
            'military': {
                'name': 'Military Research',
                'description': 'Enhance combat and defense capabilities',
                'icon': '⚔️'
            },
            'technology': {
                'name': 'Technology Research',
                'description': 'Advance general technology and efficiency',
                'icon': '🔬'
            }
        },
        'projects': {
            'advanced_mining': {
                'name': 'Advanced Mining',
                'description': 'Increase resource production by 10%',
                'category': 'economy',
                'cost': 5000,
                'benefits': {
                    'resource_production': 0.10
                }
            },
            'enhanced_storage': {
                'name': 'Enhanced Storage',
                'description': 'Increase resource storage capacity by 15%',
                'category': 'economy',
                'cost': 3000,
                'benefits': {
                    'resource_storage': 0.15
                }
            },
            'combat_tactics': {
                'name': 'Combat Tactics',
                'description': 'Increase combat power by 8%',
                'category': 'military',
                'cost': 4000,
                'benefits': {
                    'combat_power': 0.08
                }
            },
            'defensive_structures': {
                'name': 'Defensive Structures',
                'description': 'Increase defense power by 8%',
                'category': 'military',
                'cost': 4000,
                'benefits': {
                    'defense_power': 0.08
                }
            },
            'efficient_training': {
                'name': 'Efficient Training',
                'description': 'Reduce unit training time by 12%',
                'category': 'technology',
                'cost': 6000,
                'benefits': {
                    'unit_training': 0.12
                }
            },
            'research_optimization': {
                'name': 'Research Optimization',
                'description': 'Increase research speed by 10%',
                'category': 'technology',
                'cost': 7000,
                'benefits': {
                    'research_speed': 0.10
                }
            }
        }
    },
    
    'diplomacy': {
        'relationship_thresholds': {
            'allied_threshold': 1000,
            'friendly_threshold': 500,
            'hostile_threshold': -500
        },
        'treaty_types': {
            'non_aggression': {
                'name': 'Non-Aggression Pact',
                'description': 'Alliances agree not to attack each other',
                'duration': 7 * 24 * 3600,  # 7 days
                'relationship_points': 100
            },
            'mutual_defense': {
                'name': 'Mutual Defense Pact',
                'description': 'Alliances agree to defend each other in wars',
                'duration': 14 * 24 * 3600,  # 14 days
                'relationship_points': 200
            },
            'resource_sharing': {
                'name': 'Resource Sharing Agreement',
                'description': 'Alliances share a portion of their resources',
                'duration': 5 * 24 * 3600,  # 5 days
                'relationship_points': 150
            },
            'research_cooperation': {
                'name': 'Research Cooperation',
                'description': 'Alliances share research benefits',
                'duration': 10 * 24 * 3600,  # 10 days
                'relationship_points': 175
            }
        },
        'peace_treaty': {
            'min_duration': 24 * 3600,  # 1 day
            'max_duration': 30 * 24 * 3600,  # 30 days
            'relationship_points': 50
        },
        'diplomatic_actions': {
            'gift_resources': {
                'points': 10,
                'cooldown': 24 * 3600  # 24 hours
            },
            'joint_war': {
                'points': 50,
                'cooldown': 7 * 24 * 3600  # 7 days
            },
            'trade_agreement': {
                'points': 25,
                'cooldown': 3 * 24 * 3600  # 3 days
            },
            'alliance_visit': {
                'points': 5,
                'cooldown': 12 * 3600  # 12 hours
            }
        },
        'relationship_decay': {
            'rate': 1,  # points per day
            'min_points': -1000,
            'max_points': 1000
        }
    },
    
    'trading': {
        'offer_cooldown': 3600,  # 1 hour cooldown between trade offers
        'max_active_offers': 5,  # Maximum number of active trade offers per alliance
        'min_trade_value': 1000,  # Minimum value of resources in a trade
        'max_trade_value': 100000,  # Maximum value of resources in a trade
        'trade_tax_rate': 0.05,  # 5% tax on all trades
        'agreement_duration': {
            'min': 86400,  # 1 day minimum
            'max': 604800  # 7 days maximum
        },
        'max_active_agreements': 3,  # Maximum number of active trade agreements per alliance
        'resource_restrictions': {
            'restricted_resources': ['premium_currency', 'rare_materials'],
            'max_quantity': {
                'premium_currency': 1000,
                'rare_materials': 100
            }
        }
    }
} 