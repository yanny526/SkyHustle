import datetime

from utils import google_sheets
from utils.army_combat import calculate_battle_outcome, calculate_battle_rewards
from utils.ui_helpers import render_status_panel


# ── Attack another player ─────────────────────────────────────────────────────
async def attack(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text(
            "🛡️ Usage: /attack [player_id]\n"
            "Example: /attack 12345\n\n"
            + render_status_panel(player_id)
        )
        return

    target_id = args[0]

    # Load both armies
    player_army = google_sheets.load_player_army(player_id)
    target_army = google_sheets.load_player_army(target_id)

    if not player_army:
        await update.message.reply_text(
            "❌ Your army is empty. Train units with /train.\n\n"
            + render_status_panel(player_id)
        )
        return

    if not target_army:
        await update.message.reply_text(
            f"❌ Player {target_id} has no army. Unable to attack.\n\n"
            + render_status_panel(player_id)
        )
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

    # Send detailed report + status panel
    msg = (
        f"⚔️ Battle vs {target_id} — {outcome}!\n\n"
        f"🎖️ Rewards: {rewards}\n\n"
        f"📜 Battle Log:\n{battle_log}\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)


# ── View battle history ───────────────────────────────────────────────────────
async def battle_status(update, context):
    player_id = str(update.effective_user.id)
    history = google_sheets.load_battle_history(player_id)

    if not history:
        await update.message.reply_text(
            "❌ You have no battle history.\n\n"
            + render_status_panel(player_id)
        )
        return

    lines = [
        f"• [{b['date']}] vs {b['target_id']} — {b['outcome']} | Rewards: {b['rewards']}"
        for b in history
    ]
    msg = (
        "🛡️ Battle History:\n\n"
        + "\n".join(lines)
        + "\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)


# ── Spy another player's army ────────────────────────────────────────────────
async def spy(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text(
            "🛡️ Usage: /spy [player_id]\n"
            "Example: /spy 12345\n\n"
            + render_status_panel(player_id)
        )
        return

    target_id = args[0]
    target_army = google_sheets.load_player_army(target_id)

    if not target_army:
        await update.message.reply_text(
            f"❌ Player {target_id} has no army to spy on.\n\n"
            + render_status_panel(player_id)
        )
        return

    report_lines = [f"🕵️‍♂️ Spy Report — Player {target_id}:"]
    for unit, qty in target_army.items():
        report_lines.append(f"- {unit.capitalize()}: {qty}")
    report_lines.append("")  # blank line before panel
    report_lines.append(render_status_panel(player_id))

    await update.message.reply_text("\n".join(report_lines))
