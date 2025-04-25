# In-memory game data
enabled_zones = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
adjacency = {
    "Alpha": ["Beta", "Gamma"],
    "Beta": ["Alpha", "Delta"],
    "Gamma": ["Alpha", "Epsilon"],
    "Delta": ["Beta", "Epsilon"],
    "Epsilon": ["Gamma", "Delta"]
}
unit_types = ["scout", "tank", "drone"]
research_techs = ["speed", "armor"]

players = {}
offers = {}
offer_id = 1
factions = {}
zones = {z: None for z in enabled_zones}
world_bank = 0
