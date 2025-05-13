# handlers/chaos_pre_notice.py

from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from sheets_service import get_rows
from modules.chaos_storms_manager import can_trigger
from datetime import datetime
from zoneinfo import ZoneInfo

async def chaos_pre_notice_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Repeating job: send 1-minute warning before Chaos Storm in each user's local time.
    """
    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    players = get_rows("Players")

    for row in players[1:]:
        try:
            chat_id = int(row[0])
            tz_str = row[11]  # 'timezone' in column L (0-indexed 11)
            local = now_utc.astimezone(ZoneInfo(tz_str))

            # If it's Monday 08:59 local and a storm is due
            if local.weekday() == 0 and local.hour == 8 and local.minute == 59 and can_trigger():
                warning = "⚠️ *Chaos Storm Incoming in 1 minute!* ⚡ Brace yourselves!"
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=warning,
                    parse_mode=ParseMode.MARKDOWN,
                )
        except Exception:
            continue
