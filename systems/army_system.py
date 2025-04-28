# View training status
async def training_status(update, context):
    player_id = str(update.effective_user.id)

    training_queue = google_sheets.load_training_queue(player_id)

    if not training_queue:
        await update.message.reply_text("🛡️ No units currently in training.\nUse /train to start training!")
        return

    now = datetime.datetime.now()
    status_messages = []

    for task_id, task in training_queue.items():
        end_time = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        remaining = end_time - now

        if remaining.total_seconds() <= 0:
            status = f"✅ {task['amount']} {task['unit_name'].capitalize()} ready to claim!"
        else:
            minutes, seconds = divmod(int(remaining.total_seconds()), 60)
            status = f"⏳ {task['amount']} {task['unit_name'].capitalize()} training: {minutes}m {seconds}s remaining."

        status_messages.append(status)

    await update.message.reply_text(
        "🛡️ Training Status:\n\n" +
        "\n".join(status_messages)
    )

# Claim completed training
async def claim_training(update, context):
    player_id = str(update.effective_user.id)

    training_queue = google_sheets.load_training_queue(player_id)
    if not training_queue:
        await update.message.reply_text("🛡️ No completed training to claim!")
        return

    now = datetime.datetime.now()
    claimed_units = {}

    for task_id, task in list(training_queue.items()):
        end_time = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        if now >= end_time:
            claimed_units[task['unit_name']] = claimed_units.get(task['unit_name'], 0) + task['amount']
            google_sheets.delete_training_task(task_id)

    if not claimed_units:
        await update.message.reply_text("⏳ Training still in progress. Please wait until completion.")
        return

    # Update army
    current_army = google_sheets.load_player_army(player_id)
    for unit_name, amount in claimed_units.items():
        current_army[unit_name] = current_army.get(unit_name, 0) + amount
    google_sheets.save_player_army(player_id, current_army)

    # Response message
    claimed_list = [f"🔹 {amount} {unit_name.capitalize()}" for unit_name, amount in claimed_units.items()]

    await update.message.reply_text(
        "🎉 Training Complete! You have claimed:\n\n" +
        "\n".join(claimed_list)
    )
