import datetime
from typing import List, Tuple

from utils.google_sheets import load_resources, load_player_army, load_training_queue, get_building_level

# === Constants & Icons ===
MAX_STORAGE = {
    "metal": 5000,
    "fuel": 2500,
    "crystal": 1000,
    "credits": 500
}

UNIT_ICONS = {
    "soldier": "👤",
    "tank": "🚛",
    "scout_drone": "🛰️",
    "raider_mech_suit": "🤖",
    "infinity_scout_vehicle": "🚀",
}

TIMER_ICONS = {
    "mine": "⛏️",
    "train": "🏭"
}

CAPACITY_BY_LEVEL = {
    1: 100,
    5: 300,
    10: 800,
    15: 2000,
}
DEFAULT_CAPACITY = 1000

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


def get_max_army_size(player_id: str) -> int:
    """
    Compute max army size from Command Center level.
    """
    level = get_building_level(player_id, "command_center")
    for lvl in sorted(CAPACITY_BY_LEVEL.keys(), reverse=True):
        if level >= lvl:
            return CAPACITY_BY_LEVEL[lvl]
    return DEFAULT_CAPACITY


def render_status_panel(player_id: str) -> str:
    """
    Returns a multi-line status panel including:
      1) Commander name
      2) Resources (current/max)
      3) Army (used/max + top units)
      4) Up to 2 active timers
      5) Active shield
    """
    # Lazy imports to avoid circular dependencies
    import systems.timer_system as timer_system
    import systems.tutorial_system as tutorial_system

    now = datetime.datetime.now()

    # 1) Commander
    commander = tutorial_system.player_names.get(player_id, "Commander")
    line_commander = f"👤 Commander: {commander}"

    # 2) Resources
    res = load_resources(player_id)
    res_line = (
        "⚙️ Resources — "
        + " | ".join(
            f"{k.capitalize()}: {res.get(k, 0)}/{MAX_STORAGE[k]}"
            for k in ("metal", "fuel", "crystal", "credits")
        )
    )

    # 3) Army
    army = load_player_army(player_id)
    used = sum(army.values())
    cap = get_max_army_size(player_id)
    parts = []
    # Top 3 units
    top = sorted(army.items(), key=lambda x: x[1], reverse=True)[:3]
    for unit, cnt in top:
        icon = UNIT_ICONS.get(unit, "")
        parts.append(f"{icon} {cnt}")
    army_line = f"🛡️ Army — {used}/{cap}" + (" | " + " | ".join(parts) if parts else "")

    # 4) Timers
    timer_msgs: List[Tuple[datetime.timedelta, str]] = []
    # Mining
    for resource, details in getattr(timer_system, 'player_mining', {}).get(player_id, {}).items():
        end = details.get('end_time')
        if not end: continue
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        rem = end_dt - now
        if rem.total_seconds() > 0:
            timer_msgs.append((rem, f"{TIMER_ICONS['mine']} Mining {resource.title()}: {_format_timedelta(rem)}"))
    # Training
    queue = load_training_queue(player_id)
    for task in queue.values():
        end = task.get('end_time')
        if not end: continue
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        rem = end_dt - now
        if rem.total_seconds() > 0:
            timer_msgs.append((rem, f"{TIMER_ICONS['train']} Training {task['amount']}× {task['unit_name'].capitalize()}: {_format_timedelta(rem)}"))
    timer_msgs.sort(key=lambda x: x[0])
    timer_line = ""
    if timer_msgs:
        timer_line = "⏳ " + " | ".join(msg for _, msg in timer_msgs[:2])

    # 5) Shield
    shield_line = ""
    exp = tutorial_system.shield_expirations.get(player_id)
    if exp:
        rem = exp - now
        if rem.total_seconds() > 0:
            shield_line = f"🛡️ Shield Active: {_format_timedelta(rem)}"

    # Assemble all
    lines = [line_commander, res_line, army_line]
    if timer_line:
        lines.append(timer_line)
    if shield_line:
        lines.append(shield_line)

    return "\n".join(lines)
