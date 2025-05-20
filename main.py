"""
Main application file for SkyHustle 2
Sets up and runs the Telegram bot
"""

import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.game_handler import GameHandler
from config.game_config import BOT_TOKEN
from config.alliance_config import ALLIANCE_SETTINGS
from modules.player_manager import PlayerManager
from modules.bag_manager import BagManager
from modules.shop_manager import ShopManager
from modules.black_market_manager import BlackMarketManager
from handlers.shop_commands import shop, blackmarket, bag, shop_callback, blackmarket_callback, bag_callback
from handlers.premium_commands import buy, buy_callback, successful_payment

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize game handler
game_handler = GameHandler()

async def start(update, context):
    """Handle the /start command"""
    await game_handler.handle_start(update, context)

async def help(update, context):
    """Handle the /help command"""
    await game_handler.handle_help(update, context)

async def status(update, context):
    """Handle the /status command"""
    await game_handler.handle_status(update, context)

async def build(update, context):
    """Handle the /build command"""
    await game_handler.handle_build(update, context)

async def train(update, context):
    """Handle the /train command"""
    await game_handler.handle_train(update, context)

async def research(update, context):
    """Handle the /research command"""
    await game_handler.handle_research(update, context)

async def attack(update, context):
    """Handle the /attack command"""
    await game_handler.handle_attack(update, context)

async def alliance(update, context):
    """Handle the /alliance command"""
    await game_handler.handle_alliance(update, context)

async def quest(update, context):
    """Handle the /quest command"""
    await game_handler.handle_quest(update, context)

async def market(update, context):
    """Handle the /market command"""
    await game_handler.handle_market(update, context)

async def achievements(update, context):
    """Handle the /achievements command"""
    await game_handler.handle_achievements(update, context)

async def daily(update, context):
    """Handle the /daily command"""
    await game_handler.handle_daily_reward(update, context)

async def name(update, context):
    """Handle the /name command"""
    await game_handler.handle_name(update, context)

async def profile(update, context):
    """Handle the /profile command"""
    await game_handler.handle_profile(update, context)

async def leaderboard(update, context):
    """Handle the /leaderboard command"""
    await game_handler.handle_leaderboard(update, context)

async def tutorial(update, context):
    """Handle the /tutorial command"""
    await game_handler.handle_tutorial(update, context)

async def callback(update, context):
    """Handle callback queries"""
    await game_handler.handle_callback(update, context)

async def friends(update, context):
    """Handle the /friends command"""
    await game_handler.handle_friends(update, context)

async def add_friend(update, context):
    """Handle the /add_friend command"""
    await game_handler.handle_add_friend(update, context)

async def chat(update, context):
    """Handle the /chat command"""
    await game_handler.handle_chat(update, context)

async def block(update, context):
    """Handle the /block command"""
    await game_handler.handle_block(update, context)

async def unblock(update, context):
    """Handle the /unblock command"""
    await game_handler.handle_unblock(update, context)

async def level(update, context):
    """Handle the /level command"""
    await game_handler.handle_level(update, context)

async def skills(update, context):
    """Handle the /skills command"""
    await game_handler.handle_skills(update, context)

async def prestige(update, context):
    """Handle the /prestige command"""
    await game_handler.handle_prestige(update, context)

# Alliance command handlers
async def create_alliance(update, context):
    """Handle the /create_alliance command"""
    await game_handler.handle_create_alliance(update, context)

async def join_alliance(update, context):
    """Handle the /join_alliance command"""
    await game_handler.handle_join_alliance(update, context)

async def alliance_chat(update, context):
    """Handle the /alliance_chat command"""
    await game_handler.handle_alliance_chat(update, context)

async def alliance_donate(update, context):
    """Handle the /alliance_donate command"""
    await game_handler.handle_alliance_donate(update, context)

async def alliance_war(update, context):
    """Handle the /alliance_war command"""
    await game_handler.handle_alliance_war(update, context)

async def alliance_manage(update, context):
    """Handle the /alliance_manage command"""
    await game_handler.handle_alliance_manage(update, context)

async def alliance_list(update, context):
    """Handle the /alliance_list command"""
    await game_handler.handle_alliance_list(update, context)

async def alliance_info(update, context):
    """Handle the /alliance_info command"""
    await game_handler.handle_alliance_info(update, context)

async def alliance_promote(update, context):
    """Handle the /alliance_promote command"""
    await game_handler.handle_alliance_promote(update, context)

async def alliance_demote(update, context):
    """Handle the /alliance_demote command"""
    await game_handler.handle_alliance_demote(update, context)

async def alliance_transfer(update, context):
    """Handle the /alliance_transfer command"""
    await game_handler.handle_alliance_transfer(update, context)

async def alliance_requests(update, context):
    """Handle the /alliance_requests command"""
    await game_handler.handle_alliance_requests(update, context)

async def alliance_war_rankings(update, context):
    """Handle the /alliance_war_rankings command"""
    await game_handler.handle_alliance_war_rankings(update, context)

async def alliance_benefits(update, context):
    """Handle the /alliance_benefits command"""
    await game_handler.handle_alliance_benefits(update, context)

async def alliance_perks(update, context):
    """Handle the /alliance_perks command"""
    await game_handler.handle_alliance_perks(update, context)

async def alliance_resources(update, context):
    """Handle the /alliance_resources command"""
    await game_handler.handle_alliance_resources(update, context)

async def alliance_research(update, context):
    """Handle the /alliance_research command"""
    await game_handler.handle_alliance_research(update, context)

async def alliance_diplomacy(update, context):
    """Handle the /alliance_diplomacy command"""
    await game_handler.handle_alliance_diplomacy(update, context)

def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("build", build))
    application.add_handler(CommandHandler("train", train))
    application.add_handler(CommandHandler("research", research))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("alliance", alliance))
    application.add_handler(CommandHandler("quest", quest))
    application.add_handler(CommandHandler("market", market))
    application.add_handler(CommandHandler("achievements", achievements))
    application.add_handler(CommandHandler("daily", daily))
    application.add_handler(CommandHandler("name", name))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("tutorial", tutorial))
    application.add_handler(CommandHandler("friends", friends))
    application.add_handler(CommandHandler("add_friend", add_friend))
    application.add_handler(CommandHandler("chat", chat))
    application.add_handler(CommandHandler("block", block))
    application.add_handler(CommandHandler("unblock", unblock))
    application.add_handler(CommandHandler("level", level))
    application.add_handler(CommandHandler("skills", skills))
    application.add_handler(CommandHandler("prestige", prestige))

    # Add alliance command handlers
    application.add_handler(CommandHandler("create_alliance", create_alliance))
    application.add_handler(CommandHandler("join_alliance", join_alliance))
    application.add_handler(CommandHandler("alliance_chat", alliance_chat))
    application.add_handler(CommandHandler("alliance_donate", alliance_donate))
    application.add_handler(CommandHandler("alliance_war", alliance_war))
    application.add_handler(CommandHandler("alliance_manage", alliance_manage))
    application.add_handler(CommandHandler("alliance_list", alliance_list))
    application.add_handler(CommandHandler("alliance_info", alliance_info))
    application.add_handler(CommandHandler("alliance_promote", alliance_promote))
    application.add_handler(CommandHandler("alliance_demote", alliance_demote))
    application.add_handler(CommandHandler("alliance_transfer", alliance_transfer))
    application.add_handler(CommandHandler("alliance_requests", alliance_requests))
    application.add_handler(CommandHandler("alliance_war_rankings", alliance_war_rankings))
    application.add_handler(CommandHandler("alliance_benefits", alliance_benefits))
    application.add_handler(CommandHandler("alliance_perks", alliance_perks))
    application.add_handler(CommandHandler("alliance_resources", alliance_resources))
    application.add_handler(CommandHandler("alliance_research", alliance_research))
    application.add_handler(CommandHandler("alliance_diplomacy", alliance_diplomacy))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(callback))

    # Register new commands
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("blackmarket", blackmarket))
    application.add_handler(CommandHandler("bag", bag))
    application.add_handler(CommandHandler("buy", buy))

    # Register callback query handlers
    application.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_buy_"))
    application.add_handler(CallbackQueryHandler(blackmarket_callback, pattern="^blackmarket_buy_"))
    application.add_handler(CallbackQueryHandler(bag_callback, pattern="^bag_use_"))
    application.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_pack_"))

    # Register payment handler
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Update /help command to include new commands
    # (Assuming you have a help handler, add these lines to the help message)
    # /shop - Buy items with resources
    # /blackmarket - Buy rare items with HustleCoins
    # /bag - View and use your items
    # /buy - Purchase HustleCoins (premium currency)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main() 