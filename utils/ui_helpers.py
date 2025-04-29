# utils/ui_helpers.py

import datetime
from typing import List, Tuple

from utils.google_sheets import load_resources, load_player_army, load_training_queue
from systems.army_system import get_max_army_size
import systems.timer_system as timer_system
import systems.tutorial_system as tutorial_system

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
    Returns a multi-line HTML-formatted status panel including:
      • Commander name
      • Resources (current/max)
      • Army (used/max + top units)
      • Up to 2 soonest timers (mining/training)
      • Active shield remaining
    """

    now = datetime.datetime.now()

    # 1) Commander
    commander = tutorial_system.player_names.get(player_id, "Commander")
    line_commander = f"<b>Commander:</b> {commander}"

    # 2) Resources
    res = load_resources(player_id)
    res_line = (
        "⚙️ <b>Resources</b> — "
        + " | ".join(
            f"{k.capitalize()}: {res.get(k,0)}/{MAX_STORAGE[k]}"
            for k in ("metal", "fuel", "crystal", "credits")
        )
    )

    # 3) Army
    army = load_player_army(player_id)
    used = sum(army.values())
    cap = get_max_army_size(player_id)
    # show top 3 unit types by quantity
    top_units: List[Tuple[str,int]] = sorted(army.items(), key=lambda x: x[1], reverse=True)[:3]
    parts = [f"{UNIT_ICONS.get(u,'')} {cnt}" for u,cnt in top_units]
    army_line = f"🛡️ <b>Army</b> — {used}/{cap}" + ((" | " + " | ".join(parts)) if parts else "")

    # 4) Active Timers
    timer_msgs: List[Tuple[datetime.timedelta,str]] = []

    # 4a) Mining timers
    for res_key, details in getattr(timer_system, "player_mining", {}).get(player_id, {}).items():
        end = datetime.datetime.strptime(details["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            timer_msgs.append((rem, f"{TIMER_ICONS['mine']} Mining {res_key.capitalize()}: {_format_timedelta(rem)}"))

    # 4b) Training timers
    queue = load_training_queue(player_id)
    for task in queue.values():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            timer_msgs.append((rem, f"{TIMER_ICONS['train']} Training {task['amount']}× {task['unit_name'].capitalize()}: {_format_timedelta(rem)}"))

    # pick up to 2 soonest
    timer_msgs.sort(key=lambda x: x[0])
    timer_line = ""
    if timer_msgs:
        timer_line = "⏳ " + " | ".join(msg for _, msg in timer_msgs[:2])

    # 5) Shield status
    shield_line = ""
    exp = tutorial_system.shield_expirations.get(player_id)
    if exp:
        rem = exp - now
        if rem.total_seconds() > 0:
            shield_line = f"🛡️ Shield Active: {_format_timedelta(rem)}"

    # Assemble all lines
    lines = [line_commander, res_line, army_line]
    if timer_line:
        lines.append(timer_line)
    if shield_line:
        lines.append(shield_line)

    # Join with newlines and return HTML-ready string
    return "\n".join(lines)
