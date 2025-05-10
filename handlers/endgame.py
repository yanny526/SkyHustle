# handlers/endgame.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.endgame import endgame_challenges
from utils.format import section_header
from modules.player import Player

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args

    player_data = load_player_data(uid)
    player_power = calculate_power(uid)  # Implement this function based on your game logic

    if not args:
        kb = []
        for i, challenge in enumerate(endgame_challenges):
            status = "✅ Completed" if challenge.completed else "❌ Not Completed"
            kb.append([InlineKeyboardButton(f"{challenge.name} - {status}", callback_data=f"challenge_{i}")])

        kb.append([InlineKeyboardButton("Close", callback_data="close")])

        await update.message.reply_text(
            f"{section_header('ENDGAME CHALLENGES', '🎯')}\n\n"
            "Test your might against these ultimate challenges:\n\n" +
            "\n".join([f"{i+1}. {challenge.name}: Difficulty {challenge.difficulty}⭐ - Reward: {challenge.reward['skybucks']} SkyBucks" for i, challenge in enumerate(endgame_challenges)]),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    challenge_id = args[0]
    if challenge_id.isdigit() and 0 <= int(challenge_id) < len(endgame_challenges):
        challenge = endgame_challenges[int(challenge_id)]

        if challenge.completed:
            await update.message.reply_text(
                f"✅ *Challenge Already Completed* ✅\n\n"
                f"You have already conquered: {challenge.name}",
                parse_mode="Markdown"
            )
            return

        # Attempt the challenge
        success = challenge.attempt(player_power)
        if success:
            # Apply rewards
            player_data["credits"] += challenge.reward["credits"]
            player_data["minerals"] += challenge.reward["minerals"]
            player_data["skybucks"] += challenge.reward["skybucks"]
            save_player_data(uid, player_data)

            await update.message.reply_text(
                f"🎯 *Challenge Completed!* 🎯\n\n"
                f"You've defeated {challenge.name}!\n"
                f"Rewards:\n"
                f"Credits: +{challenge.reward['credits']}💰\n"
                f"Minerals: +{challenge.reward['minerals']}⛏️\n"
                f"SkyBucks: +{challenge.reward['skybucks']}💎",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ *Challenge Failed* ❌\n\n"
                f"You were unable to defeat {challenge.name}.\n"
                f"Try again after strengthening your forces!",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "Invalid challenge ID. Use /endgame to see available challenges.",
            parse_mode="Markdown"
        )
