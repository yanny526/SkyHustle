# handlers/alliance.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.alliance import Alliance
from utils.format import section_header

alliances = {}

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name

    if not args:
        kb = [
            [InlineKeyboardButton("Create Alliance", callback_data="create_alliance")],
            [InlineKeyboardButton("Join Alliance", callback_data="join_alliance")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ]

        await update.message.reply_text(
            f"{section_header('ALLIANCE SYSTEM', '🤝', 'purple')}\n\n"
            "Form alliances to enhance your strategic capabilities:\n\n"
            "Use /alliance create <name> to create a new alliance\n"
            "Use /alliance join <name> to join an existing alliance",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    action = args[0].lower()
    if action == "create" and len(args) > 1:
        alliance_name = " ".join(args[1:])
        if uid not in [member for alliance in alliances.values() for member in alliance.members]:
            new_alliance = Alliance(alliance_name, uid)
            alliances[alliance_name] = new_alliance
            await update.message.reply_text(
                f"✓ *Alliance Created!* ✓\n\n"
                f"You've founded the **{alliance_name}** alliance!\n"
                f"Use /alliance to manage your alliance.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "You are already part of an alliance!",
                parse_mode="Markdown"
            )
    elif action == "join" and len(args) > 1:
        alliance_name = " ".join(args[1:])
        if alliance_name in alliances:
            if uid not in alliances[alliance_name].members:
                alliances[alliance_name].add_member(uid)
                await update.message.reply_text(
                    f"✓ *Alliance Joined!* ✓\n\n"
                    f"You've joined the **{alliance_name}** alliance!\n"
                    f"Work together for shared victories!",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "You are already part of this alliance!",
                    parse_mode="Markdown"
                )
        else:
            await update.message.reply_text(
                "Alliance not found. Use /alliance to see available alliances.",
                parse_mode="Markdown"
            )
