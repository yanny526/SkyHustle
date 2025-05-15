import logging
import time
from datetime import datetime
from googleapiclient.errors import HttpError
from sheets_service import get_rows, append_row, update_row
from telegram.constants import ParseMode
from utils.time_utils import format_hhmmss

logger = logging.getLogger(__name__)

# ─── Sheet names ─────────────────────────────────────────────────────────────
BUILDING_DEFS_SHEET = "BuildingDefs"
BUILD_QUEUE_SHEET   = "BuildQueue"       # cols: user_id, building, to_level, start_ts, end_ts
BUILD_DONE_SHEET    = "CompletedBuilds"  # cols: user_id, building, level, completed_ts
PLAYERS_SHEET       = "Players"

# ─── Production-per-level config ─────────────────────────────────────────────
PRODUCTION_PER_LEVEL = {
    "Bank":       ("credits",   10),
    "Mine":       ("minerals",   5),
    "PowerPlant": ("energy",     3),
}

# ─── Internal Helpers ─────────────────────────────────────────────────────────

def _get_completed_rows() -> list[list[str]]:
    try:
        return get_rows(BUILD_DONE_SHEET)[1:]
    except HttpError as e:
        logger.error("Cannot read %s: %s", BUILD_DONE_SHEET, e)
        return []

def get_current_level(user_id: str, key: str) -> int:
    key_l = key.lower()
    return sum(
        1 for r in _get_completed_rows()
        if r[0] == user_id and r[1].lower() == key_l
    )

# ─── Definitions Loader ───────────────────────────────────────────────────────

def get_build_defs() -> dict[str, dict]:
    try:
        rows = get_rows(BUILDING_DEFS_SHEET)
    except HttpError as e:
        logger.error("get_build_defs: cannot read %s: %s", BUILDING_DEFS_SHEET, e)
        return {}
    if len(rows) < 2:
        return {}

    header    = rows[0]
    key_i     = header.index("key")
    name_i    = header.index("name")
    definitions = {}

    for row in rows[1:]:
        if len(row) <= key_i or not row[key_i]:
            continue
        info = dict(zip(header, row))
        k    = row[key_i]
        info["key"]  = k
        info["name"] = row[name_i] or k
        for fld in ("tier","cost_c","cost_m","cost_e","time_sec","slots_required"):
            try:
                info[fld] = int(info.get(fld, 0))
            except:
                info[fld] = 0
        info["prereqs"] = [p.strip() for p in info.get("prereqs","").split(",") if p.strip()]
        definitions[k] = info

    return definitions

# ─── Available Builds ────────────────────────────────────────────────────────

def get_available_builds(user_id: str) -> list[dict]:
    defs = get_build_defs()
    if not defs:
        return []

    # load player resources
    try:
        prow = next(r for r in get_rows(PLAYERS_SHEET)[1:] if r[0] == user_id)
        credits, minerals, energy = map(int, (prow[3], prow[4], prow[5]))
    except:
        credits = minerals = energy = 0

    done_keys = {r[1].lower() for r in _get_completed_rows()}
    out = []

    for info in defs.values():
        key   = info["key"]
        lvl   = get_current_level(user_id, key)
        entry = info.copy()
        entry["level"]      = lvl
        entry["done"]       = key.lower() in done_keys
        entry["locked"]     = any(pr.lower() not in done_keys for pr in entry["prereqs"])
        entry["affordable"] = (
            credits >= entry["cost_c"]
            and minerals >= entry["cost_m"]
            and energy   >= entry["cost_e"]
        )
        out.append(entry)

    return sorted(out, key=lambda x: (x["tier"], x["key"]))

# ─── Start / Queue / Cancel ─────────────────────────────────────────────────

def start_build(user_id: str, key: str) -> bool:
    defs = get_build_defs()
    info = defs.get(key)
    if not info:
        return False

    # deduct resources
    try:
        rows = get_rows(PLAYERS_SHEET)
    except HttpError:
        return False
    header, *pdata = rows
    for idx, row in enumerate(pdata, start=1):
        if row[0] == user_id:
            c, m, e = map(int, (row[3], row[4], row[5]))
            if c < info["cost_c"] or m < info["cost_m"] or e < info["cost_e"]:
                return False
            row[3], row[4], row[5] = (
                str(c - info["cost_c"]),
                str(m - info["cost_m"]),
                str(e - info["cost_e"])
            )
            update_row(PLAYERS_SHEET, idx, row)
            break
    else:
        return False

    # queue it
    to_level = get_current_level(user_id, key) + 1
    now      = time.time()
    end_ts   = now + info["time_sec"]

    append_row(
        BUILD_QUEUE_SHEET,
        [user_id, key, str(to_level), str(now), str(end_ts)]
    )
    return True

def get_build_queue(user_id: str) -> list[dict]:
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError:
        return []
    header, *data = rows

    out = []
    for r in data:
        if len(r) >= 5 and r[0] == user_id:
            out.append({
                "key":      r[1],
                "to_level": int(r[2]),
                "start_ts": float(r[3]),
                "end_ts":   float(r[4]),
            })
    return out

def cancel_build(user_id: str, key: str) -> bool:
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("cancel_build: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return False
    header, *data = rows
    for idx, r in enumerate(data, start=1):
        if len(r) >= 2 and r[0] == user_id and r[1] == key:
            update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))
            return True
    return False

# ─── Batch Completion Job ────────────────────────────────────────────────────

async def complete_build_job(context):
    now = time.time()
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("complete_build_job: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return
    header, *data = rows

    for idx, r in enumerate(data, start=1):
        try:
            end_ts = float(r[4])
        except:
            continue
        if end_ts <= now:
            user_id, key, lvl_str = r[0], r[1], r[2]
            lvl = int(lvl_str)
            iso = datetime.utcnow().isoformat()

            append_row(BUILD_DONE_SHEET, [user_id, key, str(lvl), iso])
            update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))

            # final notification
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🏗️ Build *{key}* complete! Now at level {lvl}.",
                parse_mode=ParseMode.MARKDOWN
            )

# ─── One-off Completion ──────────────────────────────────────────────────────

def _complete_single_build(context):
    job     = context.job
    user_id = job.data["user_id"]
    key     = job.data["key"]
    try:
        # clear queue row & get to_level
        rows = get_rows(BUILD_QUEUE_SHEET)
        header, *data = rows
        to_level = None
        for idx, r in enumerate(data, start=1):
            if len(r) >= 2 and r[0] == user_id and r[1] == key:
                to_level = int(r[2])
                update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))
                break
        if to_level is None:
            to_level = get_current_level(user_id, key)

        iso = datetime.utcnow().isoformat()
        append_row(BUILD_DONE_SHEET, [user_id, key, str(to_level), iso])

        context.bot.send_message(
            chat_id=user_id,
            text=f"🏗️ Build *{key}* complete! Now at level {to_level}.",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error("Error in _complete_single_build for %s/%s: %s", user_id, key, e)

# ─── Inline Progress Updater ─────────────────────────────────────────────────

async def update_build_progress(context):
    """Edit the original build message to show live progress bar."""
    data       = context.job.data
    chat_id    = data["chat_id"]
    message_id = data["message_id"]
    start_ts   = data["start_ts"]
    end_ts     = data["end_ts"]
    name       = data.get("name", data["key"])

    now = time.time()
    if now >= end_ts:
        # done—stop updating
        context.job.schedule_removal()
        return

    pct = (now - start_ts) / (end_ts - start_ts)
    pct = max(0.0, min(pct, 1.0))
    total = 10
    filled = int(pct * total)
    empty  = total - filled
    bar    = "█" * filled + "▁" * empty
    percent = int(pct * 100)
    left    = format_hhmmss(int(end_ts - now))

    text = f"🏗️ Building *{name}* |{bar}| {percent}% — {left} left"
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error("Failed to update build progress for %s: %s", data["key"], e)

def load_pending_builds(app):
    """
    On startup, reload any in-flight builds and schedule completion.
    (Progress bars won’t resume after a crash unless you persist message_ids.)
    """
    now = time.time()
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("load_pending_builds: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return

    header, *data = rows
    for r in data:
        if len(r) < 5:
            continue
        user_id, key, lvl_str, start_s, end_s = r
        try:
            end = float(end_s)
        except:
            continue
        delay = end - now
        if delay <= 0:
            app.job_queue.run_once(_complete_single_build, 0,
                                   data={"user_id": user_id, "key": key})
        else:
            app.job_queue.run_once(_complete_single_build, delay,
                                   data={"user_id": user_id, "key": key})
