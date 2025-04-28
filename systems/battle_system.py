# battle_system.py

import datetime
from utils import google_sheets
from systems import army_system
from utils.army_combat import calculate_battle_outcome, calculate_battle_rewards

# Attack another player
async def attack(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text("🛡️ Usage: /attack [player_id]\nExample: /attack 12345")
        return

    target_id = args[0]

    # Load both armies
    player_army = google_sheets.load_player_army(player_id)
    target_army = google_sheets.load_player_army(target_id)

    if not player_army:
        await update.message.reply_text("❌ Your army is empty. Train units with /train.")
        return
    if not target_army:
        await update.message.reply_text(f"❌ Player {target_id} has no army. Unable to attack.")
        return

    # Perform combat
    outcome, battle_log = calculate_battle_outcome(player_army, target_army)

    # Compute rewards/penalties
    rewards = calculate_battle_rewards(outcome, player_army, target_army)

    # Record battle in sheet
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    google_sheets.save_battle_result(
        player_id, target_id, outcome, rewards, now_str, battle_log
    )

    # Send detailed report
    await update.message.reply_text(
        f"⚔️ Battle vs {target_id} — {outcome}!\n\n"
        f"🎖️ Rewards: {rewards}\n\n"
        f"📜 Battle Log:\n{battle_log}"
    )

# View battle history
async def battle_status(update, context):
    player_id = str(update.effective_user.id)
    history = google_sheets.load_battle_history(player_id)

    if not history:
        await update.message.reply_text("❌ You have no battle history.")
        return

    lines = []
    for b in history:
        lines.append(
            f"• [{b['date']}] vs {b['target_id']} — {b['outcome']} | Rewards: {b['rewards']}"
        )
    await update.message.reply_text("🛡️ Battle History:\n\n" + "\n".join(lines))

# Spy another player's army
async def spy(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text("🛡️ Usage: /spy [player_id]\nExample: /spy 12345")
        return

    target_id = args[0]
    target_army = google_sheets.load_player_army(target_id)

    if not target_army:
        await update.message.reply_text(f"❌ Player {target_id} has no army to spy on.")
        return

    report = [f"🕵️‍♂️ Spy Report — Player {target_id}:"]
    for unit, qty in target_army.items():
        report.append(f"- {unit.capitalize()}: {qty}")
    await update.message.reply_text("\n".join(report))
