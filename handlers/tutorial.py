# handlers/tutorial.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.format import section_header

tutorial_steps = [
    {
        "title": "Welcome to SkyHustle",
        "content": "Welcome, Commander! SkyHustle is a strategic war game where you command a military base and engage in combat with other players."
    },
    {
        "title": "Core Commands",
        "content": "Here are the core commands to get started:\n\n"
                   "/status - View your base status\n"
                   "/build - Construct buildings\n"
                   "/train - Train units\n"
                   "/attack - Attack other players"
    },
    {
        "title": "Building Your Base",
        "content": "Use /build to construct essential buildings:\n\n"
                   "Barracks - Train infantry\n"
                   "Factory - Produce tanks\n"
                   "Research Lab - Unlock advanced technology"
    },
    {
        "title": "Training Units",
        "content": "Use /train to recruit units:\n\n"
                   "Infantry - Basic troops (low cost, low power)\n"
                   "Tanks - Armored units (moderate cost, moderate power)\n"
                   "Artillery - Long-range units (high cost, high power)"
    },
    {
        "title": "Engaging in Combat",
        "content": "Use /attack to engage other players in battle:\n\n"
                   "Victory earns you resources and experience\n"
                   "Defeat costs you resources\n"
                   "Use strategy and upgrade your units to improve your chances"
    },
    {
        "title": "Progressing in the Game",
        "content": "Earn experience to level up and unlock new abilities\n"
                   "Complete daily missions for rewards\n"
                   "Join alliances to cooperate with other players"
    },
    {
        "title": "Using Premium Features",
        "content": "Earn or purchase SkyBucks to access premium content:\n\n"
                   "/blackmarket - Purchase special items\n"
                   "/faction - Join exclusive factions\n"
                   "/endgame - Unlock challenging campaigns"
    },
    {
        "title": "Stay Updated",
        "content": "Check for daily events with /events\n"
                   "Claim daily rewards with /daily\n"
                   "Stay informed about game updates and new features"
    }
]

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    uid = str(update.effective_user.id)

    if not args:
        kb = [[InlineKeyboardButton(f"Step {i+1}: {step['title']}", callback_data=f"tutorial_{i}")] for i, step in enumerate(tutorial_steps)]
        kb.append([InlineKeyboardButton("Close", callback_data="close")])

        await update.message.reply_text(
            f"{section_header('GAME TUTORIAL', '📚')}\n\n"
            "Learn the basics of SkyHustle:\n\n" +
            "\n".join([f"{i+1}. {step['title']}" for i, step in enumerate(tutorial_steps)]),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    step_id = args[0]
    if step_id.isdigit() and 0 <= int(step_id) < len(tutorial_steps):
        step = tutorial_steps[int(step_id)]
        kb = [
            [InlineKeyboardButton("Previous", callback_data=f"tutorial_prev_{step_id}"),
             InlineKeyboardButton("Next", callback_data=f"tutorial_next_{step_id}")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ]

        await update.message.reply_text(
            f"{section_header(step['title'], '📚')}\n\n"
            f"{step['content']}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        await update.message.reply_text(
            "Invalid tutorial step. Use /tutorial to see all steps.",
            parse_mode="Markdown"
        )
