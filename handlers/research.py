# handlers/research.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.research import research_items
from utils.format import section_header

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args

    if not args:
        kb = []
        for research_name, item in research_items.items():
            status = "✅ Unlocked" if item.unlocked else "❌ Locked"
            kb.append([InlineKeyboardButton(
                f"{item.name} - {status}",
                callback_data=f"research_{research_name}"
            )])

        kb.append([InlineKeyboardButton("Close", callback_data="close")])

        await update.message.reply_text(
            f"{section_header('RESEARCH TREE', '🔬')}\n\n"
            "Unlock advanced technologies to enhance your military capabilities:\n\n" +
            "\n".join([f"{i+1}. {item.name}: {item.description} - Cost: {item.cost}" for i, item in enumerate(research_items.values())]),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    research_name = args[0]
    if research_name in research_items:
        item = research_items[research_name]
        player_data = load_player_data(uid)

        # Check if already unlocked
        if item.unlocked:
            await update.message.reply_text(
                f"✅ *Research Already Completed* ✅\n\n"
                f"{item.name} has already been unlocked!",
                parse_mode="Markdown"
            )
            return

        # Check prerequisites
        for prereq in item.prerequisites:
            if not prereq.unlocked:
                await update.message.reply_text(
                    f"❌ *Research Unavailable* ❌\n\n"
                    f"{item.name} requires the following prerequisites:\n" +
                    "\n".join([f"• {p.name}" for p in item.prerequisites if not p.unlocked]),
                    parse_mode="Markdown"
                )
                return

        # Check resources
        sufficient_resources = True
        for resource, amount in item.cost.items():
            if resource == 'credits' and player_data['credits'] < amount:
                sufficient_resources = False
            if resource == 'minerals' and player_data['minerals'] < amount:
                sufficient_resources = False
            if resource == 'skybucks' and player_data['skybucks'] < amount:
                sufficient_resources = False

        if not sufficient_resources:
            await update.message.reply_text(
                f"❌ *Insufficient Resources* ❌\n\n"
                f"Cost: {item.cost}",
                parse_mode="Markdown"
            )
            return

        # Deduct resources and unlock research
        for resource, amount in item.cost.items():
            if resource == 'credits':
                player_data['credits'] -= amount
            if resource == 'minerals':
                player_data['minerals'] -= amount
            if resource == 'skybucks':
                player_data['skybucks'] -= amount
        save_player_data(uid, player_data)

        item.unlocked = True
        result = item.apply_effect(uid)

        await update.message.reply_text(
            f"🔬 *Research Unlocked!* 🧪\n\n"
            f"{item.name} has been unlocked!\n"
            f"{result}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "Research item not found. Use /research to see available options.",
            parse_mode="Markdown"
        )
