#   handlers/start.py
#   Handles the ,start, ,help, and ,rules commands.

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the ,start command.

    This command is the first interaction a user has with the bot.
    It introduces the game, provides basic instructions, and sets the stage.
    """

    intro_message = (
        "🌌 *Welcome to SkyHustle, Commander!* 🚀\n\n"
        "Centuries from now, you command a base on the resource-rich planet Hyperion.\n"
        "Your mission: Extract valuable ore, build a powerful army, claim territory,\n"
        "and dominate your rivals in the pursuit of ultimate power.\n\n"
        "Here's how to begin your galactic conquest:\n"
        "1.  Set your commander's callsign: `,name <your_alias>`\n"
        "2.  Check your current status: `,status`\n"
        "3.  Start mining operations: `,mine ore 1`\n\n"
        "Use `,help` to see all available commands. The fate of Hyperion is in your hands!\n"
    )
    await update.message.reply_text(intro_message, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the ,help command.

    This command provides a comprehensive list of all available commands
    and their descriptions, serving as a quick reference for players.
    """

    help_message = (
        "📜 *SkyHustle Command Manual* 📜\n\n"
        "*Basic Commands:*\n"
        "  `,start` - Begin your journey, Commander!\n"
        "  `,help` - Access this command manual.\n"
        "  `,rules` - Review the laws of Hyperion.\n\n"
        "*Player Commands:*\n"
        "  `,name <alias>` - Designate your commander's callsign.\n"
        "  `,status` - Display your current base status and resources.\n\n"
        "*Resource Commands:*\n"
        "  `,daily` - Collect your daily resource allocation.\n"
        "  `,mine ore <amount>` - Extract Hyperion ore (consumes energy).\n"
        "  `,missions` - View and undertake daily missions.\n\n"
        "*Army Commands:*\n"
        "  `,forge <unit> <count>` - Construct army units (scout, tank, drone).\n"
        "  `,use <item>` - Deploy a special item from your inventory.\n\n"
        "*Economy Commands:*\n"
        "  `,blackmarket` - Access the Black Market for rare goods.\n"
        "  `,buy <item>` - Purchase an item from the Black Market.\n"
        "  `,unlockbm` - Enable the Black Market (one-time cost).\n\n"
        "*Zone Commands:*\n"
        "  `,claim <zone_name>` - Seize control of a Hyperion zone.\n"
        "  `,map` - Display the current zone ownership.\n\n"
        "*Combat Commands:*\n"
        "  `,attack <target>` - Engage another commander in battle.\n\n"
        "May your strategic prowess lead you to victory!\n"
    )
    await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the ,rules command.

    This command outlines the fundamental principles and guidelines
    that govern conduct within the SkyHustle universe.
    """

    rules_message = (
        "📜 *The Galactic Code of Conduct* 📜\n\n"
        "1.  *Respect the Zones:* Honor the boundaries and ownership of each territory.\n"
        "2.  *Uphold Fair Play:* Refrain from exploiting glitches or using unauthorized tools.\n"
        "3.  *Communicate with Honor:* Engage in respectful discourse with fellow commanders.\n"
        "4.  *Strategic Warfare:* Battles are fought with cunning, but integrity remains paramount.\n"
        "5.  *Zero Tolerance:* Any form of harassment or abuse will result in immediate expulsion.\n\n"
        "Adherence to these tenets ensures a thriving and competitive environment for all.\n"
    )
    await update.message.reply_text(rules_message, parse_mode=ParseMode.MARKDOWN)
