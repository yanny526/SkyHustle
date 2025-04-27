from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import utils.db as db

# Define research costs per level
RESEARCH_COSTS = {
    "miningspeed": 500,    # Gold per level
    "armystrength": 1000,
    "defenseboost": 800,
    "spypower": 1200
}

async def research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Invest in research technologies."""
    telegram_id = update.effective_user.id
    if len(context.args) != 2:
        return await update.message.reply_text("🧬 Usage: /research <technology> <levels>")

    tech_type = context.args[0].lower()
    try:
        levels = int(context.args[1])
    except ValueError:
        return await update.message.reply_text("🧬 Please specify a valid number of levels!")

    if tech_type not in RESEARCH_COSTS:
        return await update.message.reply_text("🧬 Invalid technology! Options: miningspeed, armystrength, defenseboost, spypower")

    player_data = db.get_player_data(telegram_id)
    if not player_data:
        return await update.message.reply_text("🧬 You must /start first!")

    # Calculate total cost
    total_cost = RESEARCH_COSTS[tech_type] * levels

    # Check resources
    if player_data['Gold'] < total_cost:
        return await update.message.reply_text("🧬 You don't have enough Gold to research this many levels!")

    # Deduct resources
    db.update_player_resources(telegram_id, gold_delta=-total_cost)

    # Update research tree
    if not db.get_research(telegram_id):
        db.create_research(telegram_id)

    if tech_type == "miningspeed":
        db.update_research(telegram_id, mining_speed_delta=levels)
    elif tech_type == "armystrength":
        db.update_research(telegram_id, army_strength_delta=levels)
    elif tech_type == "defenseboost":
        db.update_research(telegram_id, defense_boost_delta=levels)
    elif tech_type == "spypower":
        db.update_research(telegram_id, spy_power_delta=levels)

    await update.message.reply_text(f"🧬 Successfully researched {levels} level(s) of {tech_type}!")

async def tech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View current research tree."""
    telegram_id = update.effective_user.id
    research_data = db.get_research(telegram_id)

    if not research_data:
        return await update.message.reply_text("🧬 You have no research yet. Use /research to start upgrading!")

    text = (
        f"🧬 Your Research Tree:\n\n"
        f"⛏️ Mining Speed: {research_data['MiningSpeed']}\n"
        f"🪖 Army Strength: {research_data['ArmyStrength']}\n"
        f"🛡️ Defense Boost: {research_data['DefenseBoost']}\n"
        f"🛰️ Spy Power: {research_data['SpyPower']}"
    )
    await update.message.reply_text(text)
