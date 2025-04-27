# data.py — In-Memory Global Game State (used outside Google Sheets)

# ✅ Map Zones
enabled_zones = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
adjacency = {
    "Alpha": ["Beta", "Gamma"],
    "Beta": ["Alpha", "Delta"],
    "Gamma": ["Alpha", "Epsilon"],
    "Delta": ["Beta", "Epsilon"],
    "Epsilon": ["Gamma", "Delta"]
}

# ✅ Army Types
unit_types = ["scout", "tank", "drone"]

# ✅ Research Types
research_techs = ["speed", "armor"]

# ✅ In-Memory Game State
players = {}             # player_id → player data (if not using sheet)
offers = {}              # offer_id → {seller, resource, amount, price}
offer_id = 1             # incrementing counter for offer IDs
factions = {}            # name → {members, bank}
zones = {z: None for z in enabled_zones}  # zone → controlling player
world_bank = 0           # Accumulates 5% of marketplace sales
