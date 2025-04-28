# timer_system.py

import datetime

# In-memory mining database for players (expandable later to Google Sheets)
player_mining = {}

# Mining speeds (resources per minute)
MINING_SPEEDS = {
    "metal": 100,    # 100 Metal per minute
    "fuel": 60,      # 60 Fuel per minute
    "crystal": 30    # 30 Crystals per minute
}

# Start mining operation
async def start_mining(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        await update.message.reply_text("⛏️ Usage: /mine [resource] [amount]\nExample: /mine metal 1000")
        return

    resource = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("⚡ Amount must be a number.")
        return

    if resource not in MINING_SPEEDS:
        await update.message.reply_text("❌ Invalid resource. Available: metal, fuel, crystal.")
        return

    if player_id in player_mining and player_mining[player_id].get(resource):
        await update.message.reply_text(f"⚡ You are already mining {resource.capitalize()}! Finish or claim it first.")
        return

    # Calculate mining time
    minutes_needed = amount / MINING_SPEEDS[resource]
    mining_time = datetime.timedelta(minutes=minutes_needed)
    end_time = datetime.datetime.now() + mining_time

    # Save mining operation
    if player_id not in player_mining:
        player_mining[player_id] = {}

    player_mining[player_id][resource] = {
        "amount": amount,
        "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
    }

    await update.message.reply_text(
        f"⛏️ Mining Started!\n\n"
        f"Resource: {resource.capitalize()}\n"
        f"Amount: {amount}\n"
        f"Estimated Completion: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

# Check mining status
async def mining_status(update, context):
    player_id = str(update.effective_user.id)

    if player_id not in player_mining or not player_mining[player_id]:
        await update.message.reply_text("❌ No active mining operations.\nUse /mine to start mining!")
        return

    status_messages = []
    now = datetime.datetime.now()

    for resource, details in player_mining[player_id].items():
        end_time = datetime.datetime.strptime(details["end_time"], "%Y-%m-%d %H:%M:%S")
        remaining = end_time - now

        if remaining.total_seconds() <= 0:
            status = f"✅ {resource.capitalize()} mining completed! Ready to claim."
        else:
            minutes, seconds = divmod(int(remaining.total_seconds()), 60)
            status = f"⏳ {resource.capitalize()} mining in progress: {minutes}m {seconds}s remaining."

        status_messages.append(status)

    await update.message.reply_text("\n".join(status_messages))
# Claim mined resources
async def claim_mining(update, context):
    player_id = str(update.effective_user.id)

    if player_id not in player_mining or not player_mining[player_id]:
        await update.message.reply_text("❌ You have no resources ready to claim.")
        return

    claimed_resources = []
    now = datetime.datetime.now()

    to_remove = []

    for resource, details in player_mining[player_id].items():
        end_time = datetime.datetime.strptime(details["end_time"], "%Y-%m-%d %H:%M:%S")
        if now >= end_time:
            claimed_resources.append(f"{details['amount']} {resource.capitalize()}")
            to_remove.append(resource)

    if not claimed_resources:
        await update.message.reply_text("⏳ Mining still in progress. Please wait until completion.")
        return

    # Remove claimed resources from mining list
    for resource in to_remove:
        del player_mining[player_id][resource]

    # If no more mining left, clean up empty player record
    if not player_mining[player_id]:
        del player_mining[player_id]

    # Respond with claim summary
    await update.message.reply_text(
        "🎉 Mining Completed! You have claimed:\n\n" +
        "\n".join(f"🔹 {res}" for res in claimed_resources)
    )

 
