import json
import datetime
from typing import Dict

from utils import google_sheets
from utils.google_sheets import (
    load_player_army,
    load_training_queue,
    save_training_task,
    delete_training_task,
    load_resources,
    save_player_army,
    save_resources,
)
from utils.google_sheets import get_building_level
from utils.ui_helpers import render_status_panel

# Load unit stats
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)

def get_max_army_size(player_id: str) -> int:
    lvl = get_building_level(player_id, "command_center") or 1
    return 1000 + lvl * 500

def calculate_upgrade_stats(unit_name: str, upgrade_level: int) -> Dict[str, int]:
    data = UNIT_STATS.get(unit_name)
    if not data:
        return {}
    ba = data.get("base_attack", 0)
    bd = data.get("base_defense", 0)
    bh = data.get("base_hp", 0)
    bs = data.get("base_speed", 0)
    inc = data.get("upgrade_increment", {})
    return {
        "attack": ba + upgrade_level * inc.get("attack", 0),
        "defense": bd + upgrade_level * inc.get("defense", 0),
        "hp": bh + upgrade_level * inc.get("hp", 0),
        "speed": bs + upgrade_level * inc.get("speed", 0),
    }

def calculate_upgrade_cost(unit_name: str, upgrade_level: int) -> Dict[str, int]:
    data = UNIT_STATS.get(unit_name)
    if not data:
        return {}
    base = data.get("upgrade_cost", {})
    mult = 1.1
    return {res: int(base_amt * (mult ** (upgrade_level - 1))) for res, base_amt in base.items()}

def calculate_upgrade_time(unit_name: str, upgrade_level: int) -> int:
    data = UNIT_STATS.get(unit_name)
    if not data:
        return 0
    base = data.get("upgrade_time", 0)
    mult = 1.1
    return int(base * (mult ** (upgrade_level - 1)))

async def train_units(update, context):
    pid = str(update.effective_user.id)
    args = context.args or []
    panel = render_status_panel(pid)

    if len(args) != 2:
        return await update.message.reply_text("🛡️ Usage: ,train [unit] [amount]\n\n" + panel)

    unit, amt_str = args[0].lower(), args[1]
    try:
        amt = int(amt_str)
        if amt <= 0:
            raise ValueError
    except ValueError:
        return await update.message.reply_text("⚡ Amount must be a positive integer.\n\n" + panel)

    if unit not in UNIT_STATS:
        available = ", ".join(UNIT_STATS.keys())
        return await update.message.reply_text(f"❌ Unknown unit. Available: {available}\n\n" + panel)

    cap = get_max_army_size(pid)
    current = sum(load_player_army(pid).values())
    if current + amt > cap:
        return await update.message.reply_text(f"❌ Training {amt} more exceeds capacity ({cap}).\n\n" + panel)

    now = datetime.datetime.now()
    end_time = now + datetime.timedelta(seconds=UNIT_STATS[unit]["training_time"])
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    save_training_task(pid, unit, amt, end_str)
    await update.message.reply_text(f"✅ Queued {amt}× {UNIT_STATS[unit]['display_name']} for training.\n\n" + panel)

async def training_status(update, context):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    queue = load_training_queue(pid)
    now = datetime.datetime.now()
    tasks = {tid: t for tid, t in queue.items() if not t['unit_name'].startswith('upgrade:')}

    if not tasks:
        return await update.message.reply_text("⏳ No units training.\n\n" + panel)

    msgs = []
    for t in tasks.values():
        end = datetime.datetime.strptime(t['end_time'], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        name = t['unit_name'].title()
        qty = t['amount']
        if rem <= datetime.timedelta(0):
            msgs.append(f"✅ {qty}× {name} ready!")
        else:
            m, s = divmod(int(rem.total_seconds()), 60)
            msgs.append(f"⏳ {qty}× {name}: {m}m{s}s")

    await update.message.reply_text("🛡️ Training Status:\n\n" + "\n".join(msgs) + "\n\n" + panel)

async def claim_training(update, context):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    queue = load_training_queue(pid)
    now = datetime.datetime.now()

    claimed = {}
    for tid, t in list(queue.items()):
        if t['unit_name'].startswith('upgrade:'):
            continue
        end = datetime.datetime.strptime(t['end_time'], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            claimed[t['unit_name']] = claimed.get(t['unit_name'], 0) + t['amount']
            delete_training_task(tid)

    if not claimed:
        return await update.message.reply_text("⏳ Nothing ready.\n\n" + panel)

    army = load_player_army(pid)
    for u, cnt in claimed.items():
        army[u] = army.get(u, 0) + cnt
    save_player_army(pid, army)
    summary = ", ".join(f"{cnt}× {UNIT_STATS[u]['display_name']}" for u, cnt in claimed.items())
    await update.message.reply_text(f"✅ Claimed {summary}.\n\n" + panel)

async def view_army(update, context):
    pid = str(update.effective_user.id)
    army = load_player_army(pid)
    if not army:
        return await update.message.reply_text("🛡️ No units. Train with ,train.\n\n" + render_status_panel(pid))

    lines = ["<b>Your Army:</b>"]
    total = 0
    for u, qty in army.items():
        dn = UNIT_STATS.get(u, {}).get('display_name', u.title())
        lines.append(f"• {dn}: {qty} units")
        total += qty
    cap = get_max_army_size(pid)
    lines.append(f"\nTotal: {total}/{cap}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def upgrade_unit(update, context):
    pid = str(update.effective_user.id)
    args = context.args or []
    panel = render_status_panel(pid)

    if len(args) != 2:
        return await update.message.reply_text("🛡️ Usage: ,upgrade [unit] [level]\n\n" + panel)

    unit, lvl_str = args[0].lower(), args[1]
    try:
        lvl = int(lvl_str)
        if lvl <= 0:
            raise ValueError
    except ValueError:
        return await update.message.reply_text("⚡ Level must be a positive integer.\n\n" + panel)

    if unit not in UNIT_STATS:
        av = ", ".join(UNIT_STATS.keys())
        return await update.message.reply_text(f"❌ Unknown unit. Available: {av}\n\n" + panel)

    army = load_player_army(pid)
    cur_lvl = army.get(f"{unit}_level", 0)
    if lvl <= cur_lvl:
        return await update.message.reply_text(f"⚡ {UNIT_STATS[unit]['display_name']} already ≥ level {lvl}.\n\n" + panel)

    cost = calculate_upgrade_cost(unit, lvl)
    res = load_resources(pid)
    for r, c in cost.items():
        if res.get(r, 0) < c:
            cs = ", ".join(f"{c} {r}" for r, c in cost.items())
            return await update.message.reply_text(f"❌ Need {cs} to upgrade.\n\n" + panel)

    for r, c in cost.items():
        res[r] -= c
    save_resources(pid, res)
    secs = calculate_upgrade_time(unit, lvl)
    now = datetime.datetime.now()
    end = now + datetime.timedelta(seconds=secs)
    save_training_task(pid, f"upgrade:{unit}", lvl, end.strftime("%Y-%m-%d %H:%M:%S"))
    await update.message.reply_text(f"✅ Upgrading {UNIT_STATS[unit]['display_name']} to level {lvl}. Ready in {secs}s.\n\n" + panel)

async def claim_upgrade(update, context):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    queue = load_training_queue(pid)
    now = datetime.datetime.now()

    done = {}
    for tid, t in list(queue.items()):
        if not t['unit_name'].startswith('upgrade:'):
            continue
        end = datetime.datetime.strptime(t['end_time'], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            _, unit = t['unit_name'].split(':', 1)
            done[unit] = t['amount']
            delete_training_task(tid)

    if not done:
        return await update.message.reply_text("⏳ No upgrades ready.\n\n" + panel)

    army = load_player_army(pid)
    for u, lvl in done.items():
        army[f"{u}_level"] = lvl
        stats = calculate_upgrade_stats(u, lvl)
        for k, v in stats.items():
            army[f"{u}_{k}"] = v
    save_player_army(pid, army)
    sm = ", ".join(f"{UNIT_STATS[u]['display_name']} → Lv {lvl}" for u, lvl in done.items())
    await update.message.reply_text(f"✅ Claimed upgrades: {sm}.\n\n" + panel)
