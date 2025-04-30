# base_expansion_system.py (Part 1 of X)

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from utils.google_sheets import load_resources, save_resources, load_player_bases, save_player_base
from utils.ui_helpers import render_status_panel

# Constants
BASE_UNLOCK_COST = {
    "metal": 5000,
    "fuel": 3000,
    "crystal": 1000,
    "credits": 200
}

MAX_BASES = 5

def _format_costs(costs: dict) -> str:
    return " | ".join(f"{res.title()}: {amt}" for res, amt in costs.items())

async def list_bases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    bases = load_player_bases(player_id)

    if not bases:
        return await update.message.reply_text("You have no bases yet. Use /expandbase to build one.")

    lines = [f"<b>🏠 Your Bases ({len(bases)}/{MAX_BASES}):</b>"]
    for b in bases:
        lines.append(f"• {b['name']} — Built on {b['created']}")
    lines.append("\nUse /expandbase to create a new one.")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
# base_expansion_system.py (Part 2 of X)

async def expand_base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    bases = load_player_bases(player_id)

    if len(bases) >= MAX_BASES:
        return await update.message.reply_text(
            f"❌ Max number of bases reached ({MAX_BASES}).",
            parse_mode=ParseMode.HTML
        )

    resources = load_resources(player_id)
    for res, cost in BASE_UNLOCK_COST.items():
        if resources.get(res, 0) < cost:
            return await update.message.reply_text(
                f"⚠️ Not enough {res.title()} to build new base.\n\n"
                f"Cost: {_format_costs(BASE_UNLOCK_COST)}\n\n" +
                render_status_panel(player_id),
                parse_mode=ParseMode.HTML
            )

    # Deduct resources
    for res, cost in BASE_UNLOCK_COST.items():
        resources[res] -= cost
    save_resources(player_id, resources)

    # Name the base automatically
    base_number = len(bases) + 1
    base_name = f"Outpost #{base_number}"
    created_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_player_base(player_id, {"name": base_name, "created": created_on})

    await update.message.reply_text(
        f"✅ New base established: <b>{base_name}</b>\n\n" +
        render_status_panel(player_id),
        parse_mode=ParseMode.HTML
    )
# base_expansion_system.py (Part 3 of X)

async def delete_base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    bases = load_player_bases(player_id)

    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /deletebase [number]")

    try:
        index = int(context.args[0]) - 1
    except ValueError:
        return await update.message.reply_text("❌ Invalid base number.")

    if index < 0 or index >= len(bases):
        return await update.message.reply_text("❌ No base with that number.")

    removed = bases.pop(index)
    save_all_player_bases(player_id, bases)

    await update.message.reply_text(
        f"🗑️ Removed base <b>{removed['name']}</b>.\n\n" +
        render_status_panel(player_id),
        parse_mode=ParseMode.HTML
    )


async def rename_base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    bases = load_player_bases(player_id)

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /renamebase [number] [new_name]")

    try:
        index = int(context.args[0]) - 1
    except ValueError:
        return await update.message.reply_text("❌ Invalid base number.")

    if index < 0 or index >= len(bases):
        return await update.message.reply_text("❌ No base with that number.")

    new_name = " ".join(context.args[1:]).strip()
    if not new_name:
        return await update.message.reply_text("❌ Name cannot be empty.")

    bases[index]["name"] = new_name
    save_all_player_bases(player_id, bases)

    await update.message.reply_text(
        f"✏️ Renamed base to <b>{new_name}</b>.\n\n" +
        render_status_panel(player_id),
        parse_mode=ParseMode.HTML
    )
# base_expansion_system.py (Part 4 of X)

from telegram.ext import CommandHandler

def register_base_expansion_handlers(app):
    app.add_handler(CommandHandler("createbase", create_base))
    app.add_handler(CommandHandler("mybases", view_bases))
    app.add_handler(CommandHandler("upgradebase", upgrade_base))
    app.add_handler(CommandHandler("deletebase", delete_base))
    app.add_handler(CommandHandler("renamebase", rename_base))

# Optionally, you can call this from main.py:
# from systems import base_expansion_system
# base_expansion_system.register_base_expansion_handlers(app)

# Example usage:
# /createbase Outpost Alpha
# /mybases
# /upgradebase 2
# /deletebase 1
# /renamebase 1 Fortress Prime
