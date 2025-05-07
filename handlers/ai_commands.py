# handlers/ai_commands.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from modules.ai_manager import (
    initialize_ai_commanders,
    get_ai_commanders,
    simulate_ai_attack
)
from utils.format_utils import section_header, bold

async def ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available AI commanders and handle attacks."""
    initialize_ai_commanders()
    uid = str(update.effective_user.id)
    
    if context.args and context.args[0].lower() == "attack":
        ai_id = context.args[1] if len(context.args) > 1 else None
        if not ai_id:
            return await update.message.reply_text(
                "Usage: `/ai attack <AI_ID>`\nExample: `/ai attack AIDA-1`",
                parse_mode=ParseMode.MARKDOWN
            )
        
        result = simulate_ai_attack(ai_id, uid)
        if result:
            outcome = "victory" if result["result"] == "player_win" else "defeat"
            
            # Build dramatic response
            lines = [
                section_header(f"🤖 AI Combat Report"),
                "",
                f"You engaged *{result['ai_name']}* in battle!",
                f"Your Power: {result['player_power']} ⚔️",
                f"AI Power: {result['ai_power']} ⚔️",
                "",
                f"**Result: {bold(outcome.upper())}!**"
            ]
            
            if outcome == "victory":
                lines.extend([
                    f"Rewards: +{result['credits_change']} Credits! 🎉",
                    "The AI's defenses crumbled before your strategic brilliance!"
                ])
            else:
                lines.extend([
                    f"Loss: {result['credits_change']} Credits. 💔",
                    "The AI's superior tactics overcame your forces. Analyze their strategy and try again!"
                ])
            
            kb = InlineKeyboardMarkup.from_row([
                InlineKeyboardButton("Attack Again", callback_data=f"ai_attack_{ai_id}"),
                InlineKeyboardButton("View AI Opponents", callback_data="ai_list")
            ])
            
            await update.message.reply_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        else:
            await update.message.reply_text(
                "AI attack failed. Try again later.",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    ai_commanders = get_ai_commanders()
    if not ai_commanders:
        await update.message.reply_text("No AI commanders available.")
        return
    
    lines = [
        section_header("🤖 Available AI Commanders 🤖"),
        "",
        "Challenge these AI opponents to test your strategic mettle:",
    ]
    for ai in ai_commanders:
        lines.append(
            f"• *{ai[1]}* (`{ai[0]}`) - "
            f"Resources: {ai[2]}💰/{ai[3]}⛏️/{ai[4]}⚡"
        )
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Attack an AI", callback_data="ai_attack")],
        [InlineKeyboardButton("Help", callback_data="ai_help")]
    ])
    
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

async def ai_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI-related callback queries."""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "ai_list":
        return await ai(update, context)
    
    if data.startswith("ai_attack_"):
        ai_id = data.split("_")[-1]
        # Simulate attack using the ai command with arguments
        context.args = ["attack", ai_id]
        return await ai(update, context)
    
    if data == "ai_attack":
        await query.edit_message_text(
            "Select an AI to attack:\n\n"
            "• `/ai attack AIDA-1` - The Iron Sentinel\n"
            "• `/ai attack AIDA-2` - Vanguard Prime\n"
            "• `/ai attack AIDA-3` - Resource Raider",
            parse_mode=ParseMode.MARKDOWN
        )
    
    if data == "ai_help":
        lines = [
            section_header("🤖 AI Combat Help"),
            "",
            "Challenge AI opponents to hone your combat skills:",
            "",
            "• `/ai` - List available AI commanders",
            "• `/ai attack <AI_ID>` - Engage an AI in battle",
            "",
            "Victory rewards you with credits, while defeat costs you some resources.",
            "Use these battles to test new strategies and unit compositions!"
        ]
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

handler = CommandHandler("ai", ai)
callback_handler = CallbackQueryHandler(ai_button, pattern=r"^ai_")
