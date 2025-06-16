
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from modules.chaos_engine import engine
from sheets_service import get_rows

logger = logging.getLogger(__name__)

async def chaos_pre_notice_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Job runs every minute: sends a 1-minute warning before the next Chaos Storm
    (scheduled weekly at Monday 09:00 local) if it's off cooldown.
    """
    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    try:
        rows = get_rows("Players")
    except Exception as e:
        logger.error("ChaosPreNotice: failed to fetch players: %s", e)
        return

    for row in rows[1:]:
        # Parse chat_id
        try:
            chat_id = int(row[0])
        except Exception:
            logger.warning("ChaosPreNotice: invalid chat_id, skipping row: %s", row)
            continue

        # Default timezone to UTC if missing or invalid
        tz_str = row[11] if len(row) > 11 and row[11] else "UTC"
        try:
            local_time = now_utc.astimezone(ZoneInfo(tz_str))
        except Exception as e:
            logger.warning("ChaosPreNotice: invalid timezone '%s', falling back to UTC: %s", tz_str, e)
            local_time = now_utc

        # 1 minute before Monday 09:00 local
        if (
            local_time.weekday() == 0
            and local_time.hour == 8
            and local_time.minute == 59
            and engine.can_trigger()
        ):
            warning = "⚠️ *Chaos Storm Incoming in 1 minute!* ⚡ Brace yourselves!"
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=warning,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception as e:
                logger.error("ChaosPreNotice: failed to send to %s: %s", chat_id, e)

def register_pre_notice_job(application):
    """
    Schedule chaos_pre_notice_job to run every minute.
    Call this in main.py after initializing the application.
    """
    application.job_queue.run_repeating(
        chaos_pre_notice_job,
        interval=60,   # seconds
        first=0        # start immediately
    )
