from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

# Replace this with your real Telegram ID!
ADMIN_ID = 123456789  

def is_admin(user_id):
    return user_id == ADMIN_ID

async def givegold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Give gold to a player."""
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("🚫 Access Denied!")

    if len(context.args) != 2:
        return await update.message.reply_text("💰 Usage: /givegold <telegram_id> <amount>")

    target_id = context.args[0]
    amount = int(context.args[1])

    db.update_player_resources(target_id, gold_delta=amount)

    await update.message.reply_text(f"💰 Gave {amount} Gold to {target_id}!")

async def wipeplayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Wipe a player from the database."""
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("🚫 Access Denied!")

    if len(context.args) != 1:
        return await update.message.reply_text("🧹 Usage: /wipeplayer <telegram_id>")

    target_id = context.args[0]

    # Remove from PlayerProfile
    player_row = db.find_player(target_id)
    if player_row:
        db.player_profile.delete_rows(player_row)

    # Remove from Army
    ids = db.army.col_values(1)
    if str(target_id) in ids:
        row = ids.index(str(target_id)) + 1
        db.army.delete_rows(row)

    # Remove from Research
    ids = db.research.col_values(1)
    if str(target_id) in ids:
        row = ids.index(str(target_id)) + 1
        db.research.delete_rows(row)

    await update.message.reply_text(f"🧹 Player {target_id} has been wiped clean!")

async def shieldforce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Force activate shield for a player."""
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("🚫 Access Denied!")

    if len(context.args) != 1:
        return await update.message.reply_text("🛡️ Usage: /shieldforce <telegram_id>")

    target_id = context.args[0]

    player_row = db.find_player(target_id)
    if player_row:
        db.player_profile.update_cell(player_row, 9, "Yes")  # ShieldActive column
        await update.message.reply_text(f"🛡️ Shield activated for {target_id}!")
    else:
        await update.message.reply_text("🛡️ Player not found!")
