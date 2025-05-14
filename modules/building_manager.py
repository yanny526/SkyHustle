import logging
import time
from datetime import datetime
from googleapiclient.errors import HttpError
from sheets_service import get_rows, append_row, update_row

logger = logging.getLogger(__name__)

# Sheet names
BUILD_SHEET       = "Buildings"
BUILD_QUEUE_SHEET = "BuildQueue"
BUILD_DONE_SHEET  = "CompletedBuilds"
PLAYERS_SHEET     = "Players"

def get_build_defs():
    """
    Load building definitions from the Buildings sheet.
    Returns dict of key->info.
    """
    try:
        rows = get_rows(BUILD_SHEET)
    except HttpError as e:
        logger.error("get_build_defs: cannot read %s: %s", BUILD_SHEET, e)
        return {}

    if len(rows) < 2:
        return {}

    header = rows[0]
    defs = {}
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        info = dict(zip(header, row))
        for fld in ("tier","cost_c","cost_m","cost_e","time_sec","slots_required"):
            try:
                info[fld] = int(info.get(fld, "0"))
            except:
                info[fld] = 0
        info["prereqs"] = [p.strip() for p in info.get("prereqs","").split(",") if p.strip()]
        defs[info["key"]] = info
    return defs

def get_available_builds(user_id: str) -> list[dict]:
    """
    Return full list of builds, marking locked/unlocked.
    """
    defs = get_build_defs()
    if not defs:
        return []

    try:
        players = get_rows(PLAYERS_SHEET)
    except HttpError as e:
        logger.error("get_available_builds: cannot read %s: %s", PLAYERS_SHEET, e)
        return []
    header,*rows = players
    row = next((r for r in rows if r[0]==user_id), None)
    if not row:
        return []
    try:
        credits,minerals,energy = map(int, (row[3], row[4], row[5]))
    except:
        credits=minerals=energy=0

    try:
        done = [r[1] for r in get_rows(BUILD_DONE_SHEET)[1:]]
    except HttpError:
        done = []

    out = []
    for info in defs.values():
        info2 = info.copy()
        key = info["key"]
        info2["done"] = key in done
        info2["locked"] = any(pr not in done for pr in info["prereqs"])
        info2["affordable"] = (
            credits>=info["cost_c"]
            and minerals>=info["cost_m"]
            and energy>=info["cost_e"]
        )
        out.append(info2)
    return sorted(out, key=lambda x:(x["tier"], x["key"]))

def start_build(user_id: str, key: str) -> bool:
    """
    Charge resources & queue an upgrade.
    """
    defs = get_build_defs()
    info = defs.get(key)
    if not info:
        return False

    try:
        players = get_rows(PLAYERS_SHEET)
    except HttpError:
        return False
    header,*rows = players
    for idx,row in enumerate(rows, start=1):
        if row[0]==user_id:
            c,m,e = map(int, (row[3], row[4], row[5]))
            if c<info["cost_c"] or m<info["cost_m"] or e<info["cost_e"]:
                return False
            row[3],row[4],row[5] = (
                str(c-info["cost_c"]),
                str(m-info["cost_m"]),
                str(e-info["cost_e"])
            )
            update_row(PLAYERS_SHEET, idx, row)
            break
    else:
        return False

    now = time.time()
    append_row(BUILD_QUEUE_SHEET, [user_id, key, str(now), str(now+info["time_sec"])])
    return True

def get_build_queue(user_id: str) -> list[dict]:
    """
    List pending builds for user.
    """
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError:
        return []
    header,*data = rows
    out = []
    for r in data:
        if len(r)>=4 and r[0]==user_id:
            out.append(dict(
                key=r[1],
                start_ts=float(r[2]),
                end_ts=float(r[3])
            ))
    return out

def cancel_build(user_id: str, key: str) -> bool:
    """
    Remove a pending build from queue.
    """
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("cancel_build: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return False
    header,*data = rows
    for idx,r in enumerate(data, start=1):
        if len(r)>=2 and r[0]==user_id and r[1]==key:
            update_row(BUILD_QUEUE_SHEET, idx, [""]*len(header))
            return True
    return False

def complete_build_job(context):
    """
    Runs every minute to clear finished builds.
    """
    now = time.time()
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("complete_build_job: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return
    header,*data = rows
    for idx,r in enumerate(data, start=1):
        try:
            end_ts = float(r[3])
        except:
            continue
        if end_ts <= now:
            user_id, key = r[0], r[1]
            iso = datetime.utcnow().isoformat()
            append_row(BUILD_DONE_SHEET, [user_id, key, iso])
            update_row(BUILD_QUEUE_SHEET, idx, [""]*len(header))

# ─── New: Crash-Resilience Loader ──────────────────────────────────────────

def _complete_single_build(context):
    """
    One-off completion for a single build job.
    """
    job = context.job
    user_id = job.data["user_id"]
    key     = job.data["key"]

    try:
        # Mark complete
        iso = datetime.utcnow().isoformat()
        append_row(BUILD_DONE_SHEET, [user_id, key, iso])

        # Remove from queue sheet
        rows = get_rows(BUILD_QUEUE_SHEET)
        header,*data = rows
        for idx, r in enumerate(data, start=1):
            if len(r) >= 2 and r[0] == user_id and r[1] == key:
                update_row(BUILD_QUEUE_SHEET, idx, [""]*len(header))
                break

        # (Optional) Notify user
        context.bot.send_message(
            chat_id=user_id,
            text=f"🏗️ Your build *{key}* is now complete!",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error("Error in _complete_single_build for %s/%s: %s", user_id, key, e)

def load_pending_builds(app):
    """
    On bot startup, schedule one-off jobs for any builds still pending.
    """
    now = time.time()
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("load_pending_builds: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return

    header,*data = rows
    for r in data:
        if len(r) < 4:
            continue
        user_id, key = r[0], r[1]
        try:
            end_ts = float(r[3])
        except:
            continue
        delay = end_ts - now
        if delay <= 0:
            # Already overdue: run immediately
            app.job_queue.run_once(_complete_single_build, 0, data={"user_id":user_id,"key":key})
        else:
            app.job_queue.run_once(_complete_single_build, delay, data={"user_id":user_id,"key":key})

