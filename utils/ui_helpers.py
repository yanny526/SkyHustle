from utils.google_sheets import load_resources, load_player_army

# Optional: icon mapping for unit types
UNIT_ICONS = {
    "soldier": "👤",
    "tank": "🚛",
    "scout_drone": "🛰️",
    "raider_mech_suit": "🤖",
    "infinity_scout_vehicle": "🚀",
    # Add other unit keys from army_stats.json as needed
}


def render_status_panel(player_id: str) -> str:
    """
    Returns a two-line status panel showing current resources and army composition.
    """
    # Load player data
    res = load_resources(player_id)
    army = load_player_army(player_id)

    # Build resource line
    metal = res.get('metal', 0)
    fuel = res.get('fuel', 0)
    crystal = res.get('crystal', 0)
    resource_line = f"⚙️ Resources — Metal: {metal} | Fuel: {fuel} | Crystal: {crystal}"

    # Build army line
    if army:
        parts = []
        for unit_key, qty in army.items():
            icon = UNIT_ICONS.get(unit_key, '')
            # Format unit name nicely
            name = unit_key.replace('_', ' ').title()
            parts.append(f"{icon} {name}: {qty}")
        army_line = "🛡️ Army — " + " | ".join(parts)
    else:
        army_line = "🛡️ Army — (no units)"

    return resource_line + "\n" + army_line

