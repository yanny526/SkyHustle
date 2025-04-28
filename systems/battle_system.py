# Battle system
# battle_system.py

import random
from utils import google_sheets
from systems import army_system
from utils.army_combat import calculate_battle_outcome

# Attack another player
async def attack(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text("🛡️ Usage: /attack [player_id]\nExample: /attack 12345")
        return

    target_id = args[0]

    # Load player's and target's armies
    player_army = google_sheets.load_player_army(player_id)
    target_army = google_sheets.load_player_army(target_id)

    if not player_army:
        await update.message.reply_text("❌ Your army is empty.\nTrain units using /train.")
        return

    if not target_army:
        await update.message.reply_text(f"❌ Player {target_id} has no army. Unable to attack.")
        return

    # Calculate battle outcome
    outcome = calculate_battle_outcome(player_army, target_army)

    # Save battle result to Google Sheets (e.g., victory, defeat)
    google_sheets.save_battle_result(player_id, target_id, outcome)

    # Respond with battle result
    await update.message.reply_text(f"⚔️ Battle Outcome: {outcome}")
    
# View battle status (past battles or ongoing)
async def battle_status(update, context):
    player_id = str(update.effective_user.id)

    # Load player's battle history
    battle_history = google_sheets.load_battle_history(player_id)

    if not battle_history:
        await update.message.reply_text("❌ No recent battles.")
        return

    history_messages = []
    for battle in battle_history:
        history_messages.append(
            f"🔹 Target: {battle['target_id']} - Outcome: {battle['outcome']} - Date: {battle['date']}"
        )

    await update.message.reply_text("🛡️ Your Battle History:\n\n" + "\n".join(history_messages))

# Spy on another player's army
async def spy(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text("🛡️ Usage: /spy [player_id]\nExample: /spy 12345")
        return

    target_id = args[0]

    # Load the target's army details
    target_army = google_sheets.load_player_army(target_id)

    if not target_army:
        await update.message.reply_text(f"❌ Player {target_id} has no army to spy on.")
        return

    spy_report = f"🕵️‍♂️ Spy Report on Player {target_id}:\n"
    for unit, count in target_army.items():
        spy_report += f"🔹 {unit.capitalize()}: {count} units\n"

    await update.message.reply_text(spy_report)
