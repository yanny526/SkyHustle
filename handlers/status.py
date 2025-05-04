# handlers/status.py

from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.upgrade_manager import get_pending_upgrades
from modules.building_manager import (
    get_building_info,
    get_production_rates,
    get_building_health,
)
from modules.unit_manager import UNITS
from sheets_service import get_rows, update_row

from handlers.army import army as army_command
from handlers.build import build as build_command
from handlers.train import train as train_command

# Cache to throttle Sheets calls
STATUS_CACHE: dict = {}
CACHE_TTL = timedelta(seconds=30)


def render_bar(current: int, maximum: int, length: int = 10) -> str:
    if maximum <= 0:
        return ""
    filled = int(current / maximum * length)
    return "▇" * filled + "▁" * (length - filled)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = datetime.utcnow()

    # 1) Serve cached if fresh
    cache = STATUS_CACHE.get(uid)
    if cache and now - cache["time"] < CACHE_TTL:
        text = cache["text"]
        keyboard = cache["keyboard"]
    else:
        # 2) Load player resources
        players = get_rows("Players")
        for row in players[1:]:
            if row[0] == uid:
                name = row[1]
                credits, minerals, energy = map(int, row[3:6])
                break
        else:
            return await update.message.reply_text("❗ Please run /start first.")

        # 3) Historical deltas
        prev = cache["resources"] if cache else {}
        deltas = {
            "credits":  (credits  - prev.get("credits",  credits))  if "credits"  in prev else None,
            "minerals": (minerals - prev.get("minerals", minerals)) if "minerals" in prev else None,
            "energy":   (energy   - prev.get("energy",   energy))   if "energy"   in prev else None,
        }

        # 4) Buildings, production & health
        binfo  = get_building_info(uid)
        rates  = get_production_rates(binfo)
        health = get_building_health(uid)

        # 5) Build status text
        lines = [
            f"🏰 *Status for {name}*",
            "",
            f"💳 Credits: {credits}" + (f" ({deltas['credits']:+d})" if deltas["credits"] is not None else ""),
            f"▸ {render_bar(credits, max(credits, rates['credits'] * 5))}",
            f"⛏️ Minerals: {minerals}" + (f" ({deltas['minerals']:+d})" if deltas["minerals"] is not None else ""),
            f"▸ {render_bar(minerals, max(minerals, rates['minerals'] * 5))}",
            f"⚡ Energy: {energy}" + (f" ({deltas['energy']:+d})" if deltas["energy"] is not None else ""),
            f"▸ {render_bar(energy, max(energy, rates['energy'] * 5))}",
            "",
            f"💹 *Production/min:* Credits {rates['credits']}, Minerals {rates['minerals']}, Energy {rates['energy']}",
            "",
            "🏗️ *Buildings:*",
        ]
        for btype, lvl in binfo.items():
            line = f" • {btype}: Lvl {lvl}"
            if btype in health:
                cur, mx = health[btype]["current"], health[btype]["max"]
                line += f" (HP {cur}/{mx})"
            lines.append(line)

        # 6) Upgrades in Progress
        pending = get_pending_upgrades(uid)
        lines += ["", "⏳ *Upgrades in Progress:*"]
        if pending:
            for upg in sorted(pending, key=lambda x: x["end_ts"]):
                rem = int(upg["end_ts"] - now.timestamp())
                hrs, rem2 = divmod(rem, 3600)
                mins, secs = divmod(rem2, 60)
                rem_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                lines.append(f" • {upg['bname']} → Lvl {upg['target_lvl']} ({rem_str} remaining)")
        else:
            lines.append(" • None")

        # 7) Army counts
        army_rows = get_rows("Army")
        counts    = {r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid}
        lines   += ["", "⚔️ *Army:*"]
        for key, info in UNITS.items():
            disp, emoji, *_ = info
            cnt = counts.get(key, 0)
            if cnt > 0:
                lines.append(f" • {emoji} {disp}: {cnt}")

        text = "\n".join(lines)

        # 8) Inline keyboard
        keyboard = InlineKeyboardMarkup.from_row([
            InlineKeyboardButton("Upgrade HQ", callback_data="upgrade_HQ"),
            InlineKeyboardButton("Train Units", callback_data="train_units"),
            InlineKeyboardButton("View Army", callback_data="view_army"),
        ])

        # 9) Cache & send
        STATUS_CACHE[uid] = {
            "time":      now,
            "text":      text,
            "resources": {"credits": credits, "minerals": minerals, "energy": energy},
            "keyboard":  keyboard,
        }

    # 10) Respond to triggers
    if update.message:
        sent = await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    else:  # CallbackQuery
        sent = await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

    # 11) QUEST PROGRESSION STEP 4: first status check reward
    players = get_rows("Players")
    header = players[0]
    for pi, prow in enumerate(players[1:], start=1):
        if prow[0] == uid:
            while len(prow) < len(header):
                prow.append("")
            progress = prow[7]
            break
    else:
        return

    if progress == 'step3':
        prow[3] = str(int(prow[3]) + 300)
        prow[7] = 'step4'
        update_row("Players", pi, prow)

        reward_msg = (
            "🎉 Mission Update!\n"
            "✅ You checked your status!\n"
            "💳 +300 Credits awarded!\n\n"
            "Next mission: `/attack <CommanderName>` – begin your conquests."
        )
        await context.bot.send_message(
            chat_id=sent.chat.id,
            text=reward_msg,
            parse_mode=ParseMode.MARKDOWN
        )


async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Handle the Check Status button
    if query.data == "status":
        return await status(update, context)

    # Existing button handlers
    msg = query.message
    if query.data == "view_army":
        update.message = msg
        return await army_command(update, context)

    if query.data == "upgrade_HQ":
        update.message = msg
        update.message.text = "/build"
        return await build_command(update, context)

    if query.data == "train_units":
        update.message = msg
        update.message.text = "/train"
        return await train_command(update, context)


# Export handlers
handler = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(
    status_button,
    pattern="^(status|upgrade_HQ|train_units|view_army)$"
)
