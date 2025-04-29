import json, datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheets import (
    load_resources,
    save_resources,
    get_building_level,
    save_build_task,
    load_build_queue,
    delete_build_task,
)
from utils.ui_helpers import render_status_panel

# Load building definitions
with open("config/buildings.json", "r") as f:
    BUILDINGS = json.load(f)

def _level_cost_and_time(key: str, current_level: int):
    cfg = BUILDINGS[key]
    # next level is current_level+1
    lvl = current_level  # zero-indexed effect list
    cost = {
        r: int(cfg["base_cost"][r] * (cfg["cost_multiplier"] ** lvl))
        for r in cfg["base_cost"]
    }
    build_minutes = int(cfg["base_time_min"] * (cfg["time_multiplier"] ** lvl))
    return cost, datetime.timedelta(minutes=build_minutes)

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build [building] — start or queue a building/upgrade.
    """
    player = str(update.effective_user.id)
    args = context.args
    if len(args) != 1 or args[0] not in BUILDINGS:
        available = ", ".join(BUILDINGS.keys())
        return await update.message.reply_text(
            f"⚙️ Usage: /build [building]\nAvailable: {available}\n\n"
            + render_status_panel(player)
        )

    key = args[0]
    cur_lvl = get_building_level(player, key)
    if cur_lvl >= BUILDINGS[key]["max_level"]:
        return await update.message.reply_text(
            f"✅ Your {BUILDINGS[key]['display_name']} is already at max level!\n\n"
            + render_status_panel(player)
        )

    # show next level cost & ask confirm?
    cost, duration = _level_cost_and_time(key, cur_lvl)
    res = load_resources(player)
    # check affordability
    missing = [f"{r}: {cost[r]-res.get(r,0)}" 
               for r in cost if res.get(r,0) < cost[r]]
    if missing:
        return await update.message.reply_text(
            "⚠️ Not enough resources:\n  " + "\n  ".join(missing) +
            "\n\nUse /buildinfo to see next level requirements.\n\n"
            + render_status_panel(player)
        )

    # deduct resources
    for r in cost:
        res[r] = res.get(r,0) - cost[r]
    save_resources(player, res)

    # schedule build
    ready_at = datetime.datetime.now() + duration
    save_build_task(player, key, cur_lvl+1, ready_at)

    await update.message.reply_text(
        f"🛠️ Upgrade queued: {BUILDINGS[key]['display_name']} → L{cur_lvl+1}\n"
        f"⏱️ Time: {duration}\n"
        f"🔜 Ready at {ready_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        + render_status_panel(player)
    )

async def buildinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /buildinfo [building] — show your current and next-level stats.
    """
    player = str(update.effective_user.id)
    args = context.args
    if len(args)!=1 or args[0] not in BUILDINGS:
        return await update.message.reply_text(
            f"Usage: /buildinfo [building]\nAvailable: {', '.join(BUILDINGS.keys())}"
        )

    key = args[0]
    cfg = BUILDINGS[key]
    cur = get_building_level(player, key)
    cur_effects = {k: cfg["effects"][k][cur-1] for k in cfg["effects"]} if cur>0 else {}
    nxt_lvl = cur+1
    msg = [f"🏗️ {cfg['display_name']} Info"]
    msg.append(f"• Current Level: {cur}")
    if cur_effects:
        for e,v in cur_effects.items():
            msg.append(f"   ↳ {e.replace('_',' ').title()}: {v}")
    if cur < cfg["max_level"]:
        cost, duration = _level_cost_and_time(key, cur)
        nxt_eff = {k: cfg["effects"][k][nxt_lvl-1] for k in cfg["effects"]}
        msg.append(f"\n➡️ Next Level: {nxt_lvl}")
        for e,v in nxt_eff.items():
            msg.append(f"   ↳ {e.replace('_',' ').title()}: {v}")
        cost_line = " | ".join(f"{r}: {cost[r]}" for r in cost)
        msg.append(f"• Cost: {cost_line}")
        msg.append(f"• Build Time: {duration}")
    else:
        msg.append("🎉 Already at max level!")

    await update.message.reply_text("\n".join(msg)+"\n\n"+render_status_panel(player))

async def buildstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /buildstatus — view your in-progress builds.
    """
    player = str(update.effective_user.id)
    queue = load_build_queue(player)
    if not queue:
        return await update.message.reply_text(
            "🏗️ No buildings under construction.\n\n"+render_status_panel(player)
        )

    now = datetime.datetime.now()
    lines = ["🏗️ Construction Queue:"]
    for tid, task in queue.items():
        end = datetime.datetime.strptime(task["ready_at"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds()<=0:
            lines.append(f"✅ {BUILDINGS[task['key']]['display_name']} → L{task['target_level']} ready!")
            # auto-claim
            save_build_level = __import__("utils.google_sheets").google_sheets.save_building_level
            save_build_level(player, task["key"], task["target_level"])
            delete_build_task(tid)
        else:
            lines.append(
                f"⏳ {BUILDINGS[task['key']]['display_name']} → L{task['target_level']}: {_fmt(rem)}"
            )

    await update.message.reply_text("\n".join(lines)+"\n\n"+render_status_panel(player))


def _fmt(delta: datetime.timedelta) -> str:
    secs = int(delta.total_seconds())
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"
