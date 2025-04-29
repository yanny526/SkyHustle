import datetime
from typing import List, Tuple

from utils.google_sheets import load_resources, load_player_army, load_training_queue
from systems import timer_system, tutorial_system

# Maximum storage capacities
MAX_STORAGE = {
    "metal": 5000,
    "fuel": 2500,
    "crystal": 1000,
    "credits": 500,
}

# Icons
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

def _format_timedelta(delta: datetime.timedelta) -> str:
    """Turn a timedelta into 'Xd Yh Zm Ws'."""
    secs = int(delta.total_seconds())
    days, secs = divmod(secs, 86400)
    hours, secs = divmod(secs, 3600)
    mins, secs = divmod(secs, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m {secs}s")
    return " ".join(parts)

def render_status_panel(player_id: str) -> str:
    """
    Returns a nicely formatted status panel:
      👤 Commander: Name
      ⚙️ Resources — Metal:X/X | Fuel:X/X | Crystal:X/X | Credits:X/X
      🛡️ Army — used/cap [| top units…]
      ⏳ Timers — … (up to 2 soonest)
      🛡️ Shield — Active for …
    """
    # avoid circular import
    from systems.army_system import get_max_army_size

    now = datetime.datetime.now()
    lines: List[str] = []

    # 1) Commander
    commander = tutorial_system.player_names.get(player_id, "Commander")
    lines.append(f"👤 <b>Commander</b>: {commander}")

    # 2) Resources
    res = load_resources(player_id)
    res_strs = []
    for key in ("metal", "fuel", "crystal", "credits"):
        cur = res.get(key, 0)
        mx  = MAX_STORAGE[key]
        res_strs.append(f"{key.capitalize()}: {cur}/{mx}")
    lines.append("⚙️ <b>Resources</b> — " + " | ".join(res_strs))

    # 3) Army
    army = load_player_army(player_id)
    used = sum(army.values())
    cap  = get_max_army_size(player_id)
    # pick up to 3 top
    top3: List[Tuple[str,int]] = sorted(army.items(), key=lambda x: x[1], reverse=True)[:3]
    top_parts = [f"{UNIT_ICONS.get(u,'')} {c}" for u,c in top3]
    army_line = f"🛡️ <b>Army</b> — {used}/{cap}"
    if top_parts:
        army_line += " | " + " | ".join(top_parts)
    lines.append(army_line)

    # 4) Active Timers
    timers: List[Tuple[datetime.timedelta,str]] = []
    # 4a) mining
    for resource, details in timer_system.player_mining.get(player_id, {}).items():
        # try both keys just in case:
        end_str = details.get("end_time") or details.get("ready_at")
        if not end_str:
            continue
        end = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            timers.append((rem,
                f"{TIMER_ICONS['mine']} Mining {resource.capitalize()}: {_format_timedelta(rem)}"
            ))
    # 4b) training
    for task in load_training_queue(player_id).values():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() > 0:
            timers.append((rem,
                f"{TIMER_ICONS['train']} Training {task['amount']} {task['unit_name'].capitalize()}: {_format_timedelta(rem)}"
            ))
    # sort & take 2 soonest
    timers = sorted(timers, key=lambda x: x[0])[:2]
    if timers:
        lines.append("⏳ <b>Timers</b> — " + " | ".join(msg for _, msg in timers))

    # 5) Shield
    exp = tutorial_system.shield_expirations.get(player_id)
    if exp:
        rem = exp - now
        if rem.total_seconds() > 0:
            lines.append("🛡️ <b>Shield</b> — Active for " + _format_timedelta(rem))

    # assemble & return plain multiline
    return "\n".join(lines)
