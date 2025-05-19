from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from google_sheets import add_new_user, get_user_by_name, get_user_resources

CHOOSING_NAME = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Welcome to *SkyHustle*!\n\n"
        "Please reply with your desired commander name (3–20 characters, no spaces).",
        parse_mode="Markdown"
    )
    return CHOOSING_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        name = update.message.text.strip()
        print("✅ REACHED receive_name():", name)

        if " " in name or len(name) < 3 or len(name) > 20:
            await update.message.reply_text("❌ Invalid name. Use 3–20 characters, no spaces. Try again.")
            return CHOOSING_NAME

        existing, row = get_user_by_name(name)
        print("🔍 get_user_by_name result:", existing, row)

        if existing:
            await update.message.reply_text("🚫 That name is already taken. Please choose a different one.")
            return CHOOSING_NAME

        success = add_new_user(name, update.effective_user.id)
        print("🧾 add_new_user returned:", success)

        if success:
            context.user_data["game_name"] = name
            res = get_user_resources(name)
            print("📦 Resources fetched:", res)
            await update.message.reply_text(
                f"✅ Commander *{name}* registered!\n\n"
                f"🏗️ Base Level: 0\n"
                f"🪵 Wood: {res['wood']} | 🪨 Stone: {res['stone']}\n"
                f"💰 Gold: {res['gold']} | 🍖 Food: {res['food']}\n"
                f"🎖️ Power: 0\n\n"
                "Use /status or /build to continue.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ Something went wrong while saving your commander. Please try again.")
        return ConversationHandler.END

    except Exception as e:
        print("❌ FULL ERROR in receive_name():", repr(e))
        await update.message.reply_text("⚠️ An internal error occurred. Please try again later.")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚫 Cancelled.")
    return ConversationHandler.END

def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
