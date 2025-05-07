# modules/ai_manager.py
from sheets_service import get_rows, append_row, update_row
from datetime import datetime
import random

AI_SHEET = "AI_Commanders"
AI_ARMY_SHEET = "AI_Army"

def initialize_ai_commanders():
    """Initialize AI commanders with predefined bases and armies."""
    ais = [
        ("AIDA-1", "The Iron Sentinel", 15000, 8000, 4000),
        ("AIDA-2", "Vanguard Prime", 12000, 10000, 3000),
        ("AIDA-3", "Resource Raider", 3000, 7000, 9000),
    ]
    
    header = ["user_id", "commander_name", "credits", "minerals", "energy"]
    existing = get_rows(AI_SHEET)
    
    if not existing or existing[0] != header:
        append_row(AI_SHEET, header)
    
    for ai in ais:
        if not any(row[0] == ai[0] for row in get_rows(AI_SHEET)[1:]):
            append_row(AI_SHEET, list(ai))

def get_ai_commanders():
    """Return all AI commanders with their stats."""
    return get_rows(AI_SHEET)[1:]

def get_ai_army(ai_id: str):
    """Return the AI's army composition."""
    rows = get_rows(AI_ARMY_SHEET)
    return [row for row in rows[1:] if row[0] == ai_id]

def simulate_ai_attack(ai_id: str, player_id: str):
    """Simulate combat between a player and an AI commander."""
    from modules.combat_manager import calculate_power
    
    # Get AI power
    ai_army = get_ai_army(ai_id)
    ai_power = sum(int(unit[2]) * 10 for unit in ai_army)  # Simplified power calculation
    
    # Get player power
    player_power = calculate_power(player_id)
    
    # Determine outcome
    if ai_power > player_power * random.uniform(0.8, 1.2):  # AI has variable strength
        result = "ai_win"
        credits_change = -min(100, int(int(get_player_credits(player_id)) * 0.05))
    else:
        result = "player_win"
        credits_change = +random.randint(30, 80)  # Random reward
    
    # Update player credits
    update_player_credits(player_id, credits_change)
    
    # Log combat
    append_row("CombatLog", [
        ai_id,
        player_id,
        str(int(datetime.utcnow().timestamp())),
        result,
        str(abs(credits_change))
    ])
    
    ai_commanders = get_ai_commanders()
    ai_name = next((ai[1] for ai in ai_commanders if ai[0] == ai_id), "Unknown AI")
    
    return {
        "result": result,
        "credits_change": credits_change,
        "ai_power": ai_power,
        "player_power": player_power,
        "ai_name": ai_name
    }

def calculate_power(user_id: str) -> int:
    """Calculate combat power for both players and AI."""
    army_rows = get_rows('Army')[1:] + get_rows(AI_ARMY_SHEET)[1:]  # Combine player and AI armies
    power = 0
    for row in army_rows:
        if row[0] != user_id:
            continue
        unit = row[1].lower()
        count = int(row[2])
        if unit == 'infantry':
            power += count * 10
        elif unit == 'tanks':
            power += count * 50
        elif unit == 'artillery':
            power += count * 100
    return power

def get_player_credits(player_id: str) -> str:
    """Helper to get player credits."""
    players = get_rows('Players')
    for row in players[1:]:
        if row[0] == player_id:
            return row[3]
    return "0"

def update_player_credits(player_id: str, change: int):
    """Update player credits by a delta."""
    players = get_rows('Players')
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == player_id:
            current = int(row[3])
            row[3] = str(current + change)
            update_row('Players', idx, row)
            break
