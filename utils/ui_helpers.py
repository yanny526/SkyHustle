import datetime
from typing import List, Tuple

from utils.google_sheets import load_resources, load_player_army, load_training_queue
from systems import timer_system, tutorial_system

# Maximum storage capacities in resources
MAX_STORAGE = {
    "metal": 5000,
    "fuel": 2500,
    "crystal": 1000,
    "credits": 500,
}

# Icons for army units
UNIT_ICONS = {
    "soldier": "👤",
    "tank": "🚛",
    "scout_drone": "🛰️",
    "raider_mech_suit": "🤖",
    "infinity_scout_vehicle": "🚀",
}

# Timer icons
TIMER_ICONS = {
    "mine": "⛏️",
    "train": "🏭",
}

def _format_timedelta(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts: List[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m{seconds}s")
    return " ".join(parts)

def render_status_panel(player_id: str) -> str:
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
        f"{k.capitalize()}: {res.get(k, 0)}/{MAX_STORAGE.get(k, 0)}"
        for k in ["metal", "fuel", "crystal", "credits"]
    )

    # Army (lazy import to avoid circular)
    from systems.army_system import get_max_army_size

    army = load_player_army(player_id)
    used = sum(army.values())
    cap = get_max_army_size(player_id)
    # Top 3 units
    top_units: List[Tuple[str, int]] = sorted(army.items(), key=lambda x: x[1], reverse=True)[:3]
    army_parts: List[str] = []
    for unit, count in top_units:
        icon = UNIT_ICONS.get(unit, "")
        army_parts.append(f"{icon} {count}")
    army_line = f"🛡️ Army — {used}/{cap}" + (" | " + " | ".join(army_parts) if army_parts else "")

    # Timers
    now = datetime.datetime.now()
    timer_entries: List[Tuple[datetime.timedelta, str]] = []
    # Mining timers
    pm = getattr(timer_system, 'player_mining', {}).get(player_id, {})
    for resource, details in pm.items():
        end_str = details.get('end_time')
        if not end_str:
            continue
        try:
            end = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        rem = end - now
        if rem.total_seconds() > 0:
            msg = f"{TIMER_ICONS['mine']} Mining {resource.capitalize()}: {_format_timedelta(rem)}"
            timer_entries.append((rem, msg))
    # Training timers
    queue = load_training_queue(player_id)
    for task in queue.values():
        end_str = task.get('end_time')
        if not end_str:
            continue
        try:
            end = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        rem = end - now
        if rem.total_seconds() > 0:
            msg = f"{TIMER_ICONS['train']} Training {task['amount']} {task['unit_name'].capitalize()}: {_format_timedelta(rem)}"
            timer_entries.append((rem, msg))
    # Pick up to 2 soonest
    timer_entries.sort(key=lambda x: x[0])
    timer_line = ""
    if timer_entries:
        msgs = [entry[1] for entry in timer_entries[:2]]
        timer_line = f"⏳ {' | '.join(msgs)}"

    # Shield
    shield_line = ""
    exp = tutorial_system.shield_expirations.get(player_id)
    if exp:
        rem = exp - now
        if rem.total_seconds() > 0:
            shield_line = f"🛡️ Shield Active: {_format_timedelta(rem)}"

    # Assemble panel
    lines: List[str] = [f"👤 Commander: {commander}", res_line, army_line]
    if timer_line:
        lines.append(timer_line)
    if shield_line:
        lines.append(shield_line)

    return "\n".join(lines)
