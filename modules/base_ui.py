# modules/base_ui.py
# ───────────────────────────
# Implements the /base command to show a player's resources and base level,
# with inline buttons to "Build New" or "Train Troops".

from typing import Dict, Any

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from modules.sheets_helper import get_player_data

async def base_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Triggered by /base. Fetches the calling user's data and displays
    resources, diamonds, base level, and presents "Build New" / "Train Troops" buttons.
    """
    user = update.effective_user
    chat_id = user.id

    # Fetch player data from Sheets_helper
    player: Dict[str, Any] = get_player_data(chat_id)
    if not player:
        # If no data, prompt them to register
        await update.message.reply_text(
            "❌ You aren't registered yet. Send /start to create your empire."
        )
        return

    # Extract fields (with defaults if missing)
    wood = player.get("resources_wood", 0)
    stone = player.get("resources_stone", 0)
    gold = player.get("resources_gold", 0)
    food = player.get("resources_food", 0)
    diamonds = player.get("diamonds", 0)
    base_level = player.get("base_level", 1)
    game_name = player.get("game_name", "")

    # Build the message text using MarkdownV2
    text = (
        f"🏰 *{game_name}\'s Base Overview*\n\n"
        f"• 🌲 *Wood:* {wood}\n"
        f"• ⛏️ *Stone:* {stone}\n"
        f"• 🪙 *Gold:* {gold}\n"
        f"• 🍗 *Food:* {food}\n"
        f"• 💎 *Diamonds:* {diamonds}\n\n"
        f"🔹 *Base Level:* {base_level}\n"
        f"   — Allows {min(1 + (base_level - 1) // 5, 4)} simultaneous builds\n"
    )

    # Inline buttons: Build New and Train Troops (callbacks to be handled later)
    keyboard = [
        [
            InlineKeyboardButton(text="🏗 Build New", callback_data="BASE_BUILD"),
            InlineKeyboardButton(text="⚔️ Train Troops", callback_data="BASE_TRAIN"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text, parse_mode=constants.ParseMode.MARKDOWN_V2, reply_markup=reply_markup
    )


def setup_base_ui(app: Application) -> None:
    """
    Call this in main.py to register the /base command handler.
    """
    base_command = CommandHandler("base", base_handler)
    app.add_handler(base_command) 