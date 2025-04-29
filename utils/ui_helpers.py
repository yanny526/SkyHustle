# utils/ui_helpers.py

import datetime
from typing import List, Tuple

from utils.google_sheets import load_resources, load_player_army, load_training_queue

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
    """
    Nicely formats a timedelta as 'Xd Yh Zm Ws', dropping zero units.
    """
    seconds = int(delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def render_status_panel(player_id: str) -> str:
    """
    Returns a multi-line status panel:
      1. 👤 Commander: [Name]
      2. ⚙️ Resources — Metal:X/Y | Fuel:A/B | Crystal:C/D | Credits:E/F
      3. 🛡️ Army — used/limit [| top 3 units…]
      4. ⏳ Up to 2 active timers (mine/train)
      5. 🛡️ Shield Active: remaining (if any)
    """
    now = datetime.datetime.now()

    # Lazy imports to avoid circular dependencies
    from systems.army_system import get_max_army_size
    from systems.timer_system import player_mining
    from systems.tutorial_system import player_names, shield_expirations

    # 1) Commander name
    commander = player_names.get(player_id, "Commander")

    # 2) Resources
    res = load_resources(player_id)
    res_line = (
        "⚙️ Resources — "
        + " | ".join(
            f"{k.capitalize()}: {res.get(k, 0)}/{MAX_STORAGE.get(k, 0)}"
            for k in ("metal", "fuel", "crystal", "credits")
        )
    )

    # 3) Army usage & top 3
    army = load_player_army(player_id)
    used = sum(army.values())
    cap = get_max_army_size(player_id)
    # pick top 3 units by count
    top: List[Tuple[str,int]] = sorted(army.items(), key=lambda x: x[1], reverse=True)[:3]
    top_parts = [
        f"{UNIT_ICONS.get(unit,'')} {unit.replace('_',' ').title()}:{count}"
        for unit, count in top
    ]
    army_line = f"🛡️ Army — {used}/{cap}"
    if top_parts:
        army_line += " | " + " | ".join(top_parts)

    # 4) Active timers (mining + training)
    timers: List[Tuple[datetime.timedelta, str]] = []

    # 4a) Mining timers
    mining_ops = player_mining.get(player_id, {})
    for resource, details in mining_ops.items():
        end = datetime.datetime.strptime(details["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            msg = f"{TIMER_ICONS['mine']} Mining {resource.title()}: {_format_timedelta(rem)}"
            timers.append((rem, msg))

    # 4b) Training timers
    queue = load_training_queue(player_id)
    for task in queue.values():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            msg = (
                f"{TIMER_ICONS['train']} Training "
                f"{task['amount']} {task['unit_name'].capitalize()}: {_format_timedelta(rem)}"
            )
            timers.append((rem, msg))

    # take up to 2 soonest
    timers = [m for _, m in sorted(timers, key=lambda x: x[0])[:2]]
    timer_line = f"⏳ {' | '.join(timers)}" if timers else ""

    # 5) Starter shield
    shield_line = ""
    exp = shield_expirations.get(player_id)
    if exp:
        rem = exp - now
        if rem.total_seconds() > 0:
            shield_line = f"🛡️ Shield Active: {_format_timedelta(rem)}"

    # assemble all lines
    lines = [f"👤 Commander: {commander}", res_line, army_line]
    if timer_line:
        lines.append(timer_line)
    if shield_line:
        lines.append(shield_line)

    return "\n".join(lines)
