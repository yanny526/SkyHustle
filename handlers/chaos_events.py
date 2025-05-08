# handlers/chaos_events.py

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from modules.chaos_events import create_random_event, ChaosEvent
from utils.format import section_header

active_events = []

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if args and args[0].lower() == "trigger":
        # Create and apply a new random event
        event = create_random_event()
        active_events.append(event)
        event.apply_effect(update.effective_user.id)

        await update.message.reply_text(
            f"{section_header('CHAOS EVENT ACTIVATED', '🌪️')}\n\n"
            f"**{event.name}**\n"
            f"{event.description}\n"
            f"Duration: {event.duration} hours",
            parse_mode="Markdown"
        )
    else:
        # Display active events
        if active_events:
            event_text = ""
            for event in active_events:
                remaining = (event.end_time - datetime.now()).total_seconds() / 3600
                event_text += f"• **{event.name}**: {event.description} (Ends in {remaining:.1f} hours)\n"

            await update.message.reply_text(
                f"{section_header('ACTIVE CHAOS EVENTS', '🌪️')}\n\n"
                f"{event_text}\n"
                "Use /chaos trigger to activate a new event!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"{section_header('NO ACTIVE CHAOS EVENTS', '🌪️')}\n\n"
                "The galaxy is temporarily peaceful...\n"
                "Use /chaos trigger to activate a new event!",
                parse_mode="Markdown"
            )
