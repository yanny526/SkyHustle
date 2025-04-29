import datetime
from typing import List, Tuple

from utils.google_sheets import load_resources, load_player_army, load_training_queue
from systems import timer_system, tutorial_system


# Maximum storage capacities (adjust as needed)
MAX_STORAGE = {
    "metal": 5000,
    "fuel": 2500,
    "crystal": 1000,
    "credits": 500
}

# Icons for unit types
UNIT_ICONS = {
    "soldier": "👤",
    "tank": "🚛",
    "scout_drone": "🛰️",
    "raider_mech_suit": "🤖",
    "infinity_scout_vehicle": "🚀",
}

# Icons for timers
TIMER_ICONS = {
    "mine": "⛏️",
    "train": "🏭"
}


def _format_timedelta(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m {seconds}s")
    return " ".join(parts)


def render_status_panel(player_id: str) -> str:
    """
    Returns a two-line status panel showing current resources and army composition, including capacity.
    """
    # Lazy import to avoid circular dependencies
    from systems.army_system import get_max_army_size

    # Load player data
    res = load_resources(player_id)
    army = load_player_army(player_id)

    # Build resource line
    metal = res.get('metal', 0)
    fuel = res.get('fuel', 0)
    crystal = res.get('crystal', 0)
    resource_line = f"⚙️ Resources — Metal: {metal} | Fuel: {fuel} | Crystal: {crystal}"

    # Build army line with capacity
    max_cap = get_max_army_size(player_id)
    total_units = sum(army.values())
    if army:
        parts = []
        for unit_key, qty in army.items():
            icon = UNIT_ICONS.get(unit_key, '')
            name = unit_key.replace('_', ' ').title()
            parts.append(f"{icon} {name}: {qty}")
        army_line = (
            f"🛡️ Army — {total_units}/{max_cap} | "
            + " | ".join(parts)
        )
    else:
        army_line = f"🛡️ Army — 0/{max_cap} (no units)"

    return resource_line + "
" + army_line(player_id: str) -> str:
    """
    Returns a multi-line status panel:
      1. Commander name
      2. Resources (current/max)
      3. Army (used/max + top 3 units)
      4. Up to 2 active timers
      5. Active Shield (if any)
    """
    # Commander
    commander = tutorial_system.player_names.get(player_id, "Commander")

    # Resources
    res = load_resources(player_id)
    res_line = "⚙️ Resources — " + " | ".join(
        f"{k.capitalize()}: {res.get(k,0)}/{MAX_STORAGE.get(k,0)}"
        for k in ["metal", "fuel", "crystal", "credits"]
    )

    # Army
    army = load_player_army(player_id)
    used = sum(army.values())
    cap = get_max_army_size(player_id)
    # Top 3
    top_units: List[Tuple[str,int]] = sorted(army.items(), key=lambda x: x[1], reverse=True)[:3]
    parts = []
    for unit, count in top_units:
        icon = UNIT_ICONS.get(unit, "")
        parts.append(f"{icon} {count}")
    army_line = f"🛡️ Army — {used}/{cap}" + (" | " + " | ".join(parts) if parts else "")

    # Active Timers
    # Mining (in-memory)
    mining = []
    now = datetime.datetime.now()
    for resource, details in getattr(timer_system, 'player_mining', {}).get(player_id, {}).items():
        end = datetime.datetime.strptime(details['end_time'], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            mining.append((rem, f"{TIMER_ICONS['mine']} Mining {resource.capitalize()}: {_format_timedelta(rem)}"))
    # Training
    training = []
    queue = load_training_queue(player_id)
    for task in queue.values():
        end = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            training.append((rem, f"{TIMER_ICONS['train']} Training {task['amount']} {task['unit_name'].capitalize()}: {_format_timedelta(rem)}"))
    # Select up to 2 soonest
    timers = [msg for (_, msg) in sorted(mining + training, key=lambda x: x[0])[:2]]
    timer_line = "⏳ " + " | ".join(timers) if timers else ""

    # Shield
    shield_line = ""
    exp = tutorial_system.shield_expirations.get(player_id)
    if exp:
        rem = exp - now
        if rem.total_seconds() > 0:
            shield_line = f"🛡️ Shield Active: {_format_timedelta(rem)}"

    # Assemble
    lines = [f"👤 Commander: {commander}", res_line, army_line]
    if timer_line:
        lines.append(timer_line)
    if shield_line:
        lines.append(shield_line)

    return "\n".join(lines)
