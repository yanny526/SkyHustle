import datetime
from typing import List, Tuple

from systems import timer_system, tutorial_system
from utils.google_sheets import (
    load_resources,
    load_player_army,
    load_training_queue,
    get_building_level,
)

# === Constants & Icons ===
MAX_STORAGE = {
    "metal": 5000,
    "fuel": 2500,
    "crystal": 1000,
    "credits": 500,
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
    "train": "🏭",
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
    parts: List[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m {seconds}s")
    return " ".join(parts)


def render_status_panel(player_id: str) -> str:
    """
    Assembles the full status panel text for a player.
    """
    # 1) Resources
    resources = load_resources(player_id)
    res_lines = [
        f"• {r.title()}: {amt}/{MAX_STORAGE.get(r, '∞')}"
        for r, amt in resources.items()
    ]
    res_str = "\n".join(res_lines)

    # 2) Army (with icons)
    army = load_player_army(player_id)
    if army:
        army_lines = [
            f"• {UNIT_ICONS.get(unit, '❓')} {unit.title()}: {qty}"
            for unit, qty in army.items()
        ]
    else:
        army_lines = ["(none)"]
    army_str = "\n".join(army_lines)

    # 3) Buildings (just levels)
    building_lines = [
        f"• {building.replace('_', ' ').title()}: Lv {get_building_level(player_id, building) or 0}"
        for building in ["command_center", "metal_mine", "fuel_refinery"]
    ]
    building_str = "\n".join(building_lines)

    # 4) Timers (mining/training)
    now = datetime.datetime.now()
    timer_msgs: List[Tuple[datetime.timedelta, str]] = []

    # Mining timers
    for resource, details in getattr(timer_system, 'player_mining', {}).get(player_id, {}).items():
        end_str = details.get('end')
        if not end_str:
            continue
        end_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        rem = end_dt - now
        if rem.total_seconds() > 0:
            timer_msgs.append(
                (rem, f"{TIMER_ICONS['mine']} Mining {resource.title()}: {_format_timedelta(rem)}")
            )

    # Training timers
    queue = load_training_queue(player_id)
    for task in queue.values():
        end_str = task.get('end_time')
        if not end_str:
            continue
        end_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        rem = end_dt - now
        if rem.total_seconds() > 0:
            timer_msgs.append(
                (
                    rem,
                    f"{TIMER_ICONS['train']} Training {task['amount']}× {task['unit_name'].capitalize()}: {_format_timedelta(rem)}",
                )
            )

    # Sort and select top 2
    timer_msgs.sort(key=lambda x: x[0])
    timer_line = ""
    if timer_msgs:
        timer_line = "⏳ " + " | ".join(msg for _, msg in timer_msgs[:2])

    # 5) Shield timer
    shield_line = ""
    exp = tutorial_system.shield_expirations.get(player_id)
    if exp:
        rem = exp - now
        if rem.total_seconds() > 0:
            shield_line = f"🛡️ Shield: {_format_timedelta(rem)}"

    # Assemble panel
    return (
        f"<b>⚙️ Empire Status:</b>\n"
        f"<b>Resources:</b>\n{res_str}\n\n"
        f"<b>Army:</b>\n{army_str}\n\n"
        f"<b>Buildings:</b>\n{building_str}\n\n"
        f"{timer_line}\n"
        f"{shield_line}"
    )
