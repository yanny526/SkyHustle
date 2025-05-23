"""
Main application file for SkyHustle 2
Sets up and runs the Telegram bot
"""

import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.game_handler import GameHandler
from config.alliance_config import ALLIANCE_SETTINGS
from modules.player_manager import PlayerManager
from modules.bag_manager import BagManager
from modules.shop_manager import ShopManager
from modules.black_market_manager import BlackMarketManager
from modules.resource_manager import ResourceManager
from modules.progression_manager import ProgressionManager
from handlers.shop_commands import shop, blackmarket, bag, shop_callback, blackmarket_callback, bag_callback
from handlers.premium_commands import buy, buy_callback, successful_payment
from handlers.admin_handler import AdminHandler

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Initialize game handler
game_handler = GameHandler()
admin_handler = AdminHandler()

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

async def admin(update, context):
    """Handle the /admin command"""
    await admin_handler.handle_admin_command(update, context)

async def addadmin(update, context):
    """Handle the /addadmin command"""
    await admin_handler.handle_add_admin(update, context)

async def removeadmin(update, context):
    """Handle the /removeadmin command"""
    await admin_handler.handle_remove_admin(update, context)

async def broadcast(update, context):
    """Handle the /broadcast command"""
    await admin_handler.handle_broadcast(update, context)

async def maintenance(update, context):
    """Handle the /maintenance command"""
    await admin_handler.handle_maintenance(update, context)

async def logs(update, context):
    """Handle the /logs command"""
    await admin_handler.handle_logs(update, context)

async def ban(update, context):
    """Handle the /ban command"""
    await admin_handler.handle_ban(update, context)

async def unban(update, context):
    """Handle the /unban command"""
    await admin_handler.handle_unban(update, context)

async def grant(update, context):
    """Handle the /grant command"""
    await admin_handler.handle_grant(update, context)

async def reset_player(update, context):
    """Handle the /reset_player command"""
    await admin_handler.handle_reset_player(update, context)

async def stats(update, context):
    """Handle the /stats command"""
    await admin_handler.handle_stats(update, context)

async def search_player(update, context):
    """Handle the /search_player command"""
    await admin_handler.handle_search_player(update, context)

async def admin_help(update, context):
    """Handle the /admin_help command"""
    await admin_handler.handle_admin_help(update, context)

def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Initialize managers
    player_manager = PlayerManager()
    bag_manager = BagManager()
    resource_manager = ResourceManager()
    progression_manager = ProgressionManager()
    shop_manager = ShopManager(bag_manager, resource_manager)
    black_market_manager = BlackMarketManager(bag_manager, player_manager)
    
    # Set managers in handler modules
    from handlers.shop_commands import shop_manager as shop_module_manager
    from handlers.shop_commands import black_market_manager as black_market_module_manager
    from handlers.shop_commands import bag_manager as bag_module_manager
    from handlers.shop_commands import player_manager as player_module_manager
    from handlers.premium_commands import player_manager as premium_player_manager
    
    shop_module_manager = shop_manager
    black_market_module_manager = black_market_manager
    bag_module_manager = bag_manager
    player_module_manager = player_manager
    premium_player_manager = player_manager

    # Add error handler
    application.add_error_handler(error_handler)

    # Register command handlers
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

    # Shop and premium commands
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("blackmarket", blackmarket))
    application.add_handler(CommandHandler("bag", bag))
    application.add_handler(CommandHandler("buy", buy))

    # Alliance commands
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

    # Admin commands
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("addadmin", addadmin))
    application.add_handler(CommandHandler("removeadmin", removeadmin))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("maintenance", maintenance))
    application.add_handler(CommandHandler("logs", logs))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CommandHandler("grant", grant))
    application.add_handler(CommandHandler("reset_player", reset_player))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("search_player", search_player))
    application.add_handler(CommandHandler("admin_help", admin_help))

    # Callback query handler
    application.add_handler(CallbackQueryHandler(callback))

    # Register callback query handlers
    application.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_buy_"))
    application.add_handler(CallbackQueryHandler(blackmarket_callback, pattern="^blackmarket_buy_"))
    application.add_handler(CallbackQueryHandler(bag_callback, pattern="^bag_use_"))
    application.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_pack_"))

    # Register payment handler
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Start the Bot
    application.run_polling()

async def error_handler(update, context):
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again later or contact support if the problem persists."
        )

if __name__ == '__main__':
    main() 