import datetime
from typing import List, Tuple

from utils.google_sheets import (
    load_resources,
    load_player_army,
    load_training_queue,
)
from systems import timer_system, tutorial_system

# Maximum storage capacities
MAX_STORAGE = {
    "metal": 5000,
    "fuel": 2500,
    "crystal": 1000,
    "credits": 500,
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
    "train": "🏭",
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
    Returns a multi-line status panel:
      1. Commander name
      2. Resources (current/max)
      3. Army (used/max + up to 3 top units)
      4. Up to 2 soonest active timers
      5. Active Shield (if any)
    """
    # Commander name
    commander = tutorial_system.player_names.get(player_id, "Commander")

    # Resources with max storage
    res = load_resources(player_id)
    res_line = "⚙️ Resources — " + " | ".join(
        f"{k.capitalize()}: {res.get(k,0)}/{MAX_STORAGE[k]}"
        for k in ["metal", "fuel", "crystal", "credits"]
    )

    # Army used vs capacity + top 3 units
    from systems.army_system import get_max_army_size  # lazy import to avoid circular
    army = load_player_army(player_id)
    used = sum(army.values())
    cap = get_max_army_size(player_id)
    top_units: List[Tuple[str,int]] = sorted(army.items(), key=lambda x: x[1], reverse=True)[:3]
    unit_parts = [
        f"{UNIT_ICONS.get(u,'')} {u.replace('_',' ').title()}: {cnt}"
        for u, cnt in top_units
    ]
    army_line = f"🛡️ Army — {used}/{cap}"
    if unit_parts:
        army_line += " | " + " | ".join(unit_parts)

    # Build timer lines (mining + training), pick two soonest
    now = datetime.datetime.now()
    timers: List[Tuple[datetime.timedelta,str]] = []

    # Mining timers (in-memory)
    for resource, details in timer_system.player_mining.get(player_id, {}).items():
        end = datetime.datetime.strptime(details["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            timers.append((rem, f"{TIMER_ICONS['mine']} Mining {resource.capitalize()}: {_format_timedelta(rem)}"))

    # Training timers (Google Sheets)
    for task in load_training_queue(player_id).values():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            timers.append((rem, f"{TIMER_ICONS['train']} Training {task['amount']} {task['unit_name'].capitalize()}: {_format_timedelta(rem)}"))

    timers.sort(key=lambda x: x[0])
    timer_lines = [msg for _, msg in timers[:2]]

    # Shield line if active
    shield_line = ""
    exp = tutorial_system.shield_expirations.get(player_id)
    if exp:
        rem = exp - now
        if rem.total_seconds() > 0:
            shield_line = f"🛡️ Shield Active: {_format_timedelta(rem)}"

    # Assemble all parts
    lines = [
        f"👤 Commander: {commander}",
        res_line,
        army_line,
    ]
    if timer_lines:
        lines.append("⏳ " + " | ".join(timer_lines))
    if shield_line:
        lines.append(shield_line)

    return "\n".join(lines)
