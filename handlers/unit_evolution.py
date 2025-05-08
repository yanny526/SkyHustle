# handlers/unit_evolution.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.unit_evolution import UnitEvolution
from utils.format import section_header

evolutions = [
    UnitEvolution("Infantry Elite", "Upgrade infantry to elite status", {"credits": 500, "minerals": 200}, lambda uid: True),
    UnitEvolution("Tank Commander", "Upgrade tanks to commander level", {"credits": 800, "minerals": 300}, lambda uid: True),
    UnitEvolution("Artillery Specialist", "Upgrade artillery to specialist level", {"credits": 1000, "minerals": 400}, lambda uid: True)
]

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args

    if not args:
        kb = [[InlineKeyboardButton(f"Evolve {evo.name}", callback_data=f"evolve_{i}")] for i, evo in enumerate(evolutions)]
        kb.append([InlineKeyboardButton("Close", callback_data="close")])

        await update.message.reply_text(
            f"{section_header('UNIT EVOLUTION', '🌟')}\n\n"
            "Select a unit to evolve:\n\n" +
            "\n".join([f"{i+1}. {evo.name} - {evo.description}" for i, evo in enumerate(evolutions)]),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    evolution_id = args[0]
    if evolution_id.isdigit() and 0 <= int(evolution_id) < len(evolutions):
        evo = evolutions[int(evolution_id)]
        if evo.can_evolve(uid):
            evo.unlocked = True
            evo.apply_effect(uid)
            await update.message.reply_text(
                f"🚀 *Unit Evolved!* 🚀\n\n"
                f"{evo.name} unlocked!\n"
                f"Your units have been enhanced!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "Insufficient resources to perform evolution!",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "Invalid evolution selection. Use /evolve to see available evolutions.",
            parse_mode="Markdown"
        )
