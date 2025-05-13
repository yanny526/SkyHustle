import logging
import time
from datetime import datetime
from googleapiclient.errors import HttpError
from sheets_service import get_rows, append_row, update_row

logger = logging.getLogger(__name__)

# Sheet names
RESEARCH_SHEET    = "Research"
QUEUE_SHEET       = "ResearchQueue"
COMPLETED_SHEET   = "CompletedResearch"
PLAYERS_SHEET     = "Players"


def load_research_defs():
    """
    Load all tech definitions from the Research sheet.
    Returns a dict mapping tech_key -> tech_info dict.
    """
    try:
        rows = get_rows(RESEARCH_SHEET)
    except HttpError as e:
        logger.error("load_research_defs: failed to load '%s' sheet: %s", RESEARCH_SHEET, e)
        return {}

    if not rows or len(rows) < 2:
        return {}

    header = rows[0]
    techs = {}
    for row in rows[1:]:
        if not row or not row[0]:
            continue

        info = dict(zip(header, row))
        # parse prerequisites
        info["prereqs"] = [p.strip() for p in info.get("prereqs", "").split(",") if p.strip()]

        # parse tier
        try:
            info["tier"] = int(info.get("tier", "1"))
        except ValueError:
            info["tier"] = 1

        # parse cost/time fields
        for fld in ("cost_c", "cost_m", "cost_e", "time_sec", "token_cost", "slots_required"):
            try:
                info[fld] = int(info.get(fld, "0"))
            except ValueError:
                info[fld] = 0

        # handle limited-time tech
        info["is_limited"] = str(info.get("is_limited", "")).upper() == "TRUE"
        if info["is_limited"]:
            try:
                info["start_ts"] = datetime.fromisoformat(info.get("start_ts", ""))
                info["end_ts"]   = datetime.fromisoformat(info.get("end_ts", ""))
            except Exception:
                info["start_ts"] = None
                info["end_ts"]   = None

        techs[info["key"]] = info

    return techs


def get_available_research(user_id: str) -> list[dict]:
    """
    Return a list of research definitions the user can start,
    based on resources, prerequisites, and (optional) time window.
    """
    defs = load_research_defs()
    if not defs:
        return []

    try:
        players = get_rows(PLAYERS_SHEET)
    except HttpError as e:
        logger.error("get_available_research: failed to load '%s' sheet: %s", PLAYERS_SHEET, e)
        return []

    header, *rows = players
    user_row = next((r for r in rows if r[0] == user_id), None)
    if not user_row:
        return []

    try:
        credits = int(user_row[3])
        minerals = int(user_row[4])
        energy = int(user_row[5])
    except Exception:
        credits = minerals = energy = 0

    try:
        completed = [r[1] for r in get_rows(COMPLETED_SHEET)[1:]]
    except HttpError:
        completed = []

    available = []
    now = datetime.utcnow()
    for info in defs.values():
        key = info["key"]
        if key in completed:
            continue
        # limited-time check
        if info["is_limited"] and (
           (info.get("start_ts") and now < info["start_ts"]) or
           (info.get("end_ts") and now > info["end_ts"])
        ):
            continue
        # prerequisites
        if any(pr not in completed for pr in info["prereqs"]):
            continue
        # resources
        if credits < info["cost_c"] or minerals < info["cost_m"] or energy < info["cost_e"]:
            continue
        available.append(info)

    return available


def start_research(user_id: str, key: str) -> bool:
    """
    Attempt to queue a research project for the user.
    Returns True on success, False otherwise.
    """
    defs = load_research_defs()
    info = defs.get(key)
    if not info:
        return False

    try:
        players = get_rows(PLAYERS_SHEET)
    except HttpError:
        return False

    header, *rows = players
    for idx, row in enumerate(rows, start=1):
        if row[0] == user_id:
            credits = int(row[3]); minerals = int(row[4]); energy = int(row[5])
            if (credits < info["cost_c"] or
                minerals < info["cost_m"] or
                energy < info["cost_e"]):
                return False
            row[3] = str(credits - info["cost_c"])
            row[4] = str(minerals - info["cost_m"])
            row[5] = str(energy - info["cost_e"])
            update_row(PLAYERS_SHEET, idx, row)
            break
    else:
        return False

    now = time.time()
    end_ts = now + info["time_sec"]
    append_row(QUEUE_SHEET, [user_id, key, str(now), str(end_ts)])
    return True


def get_queue(user_id: str) -> list[dict]:
    """
    Return the list of pending research projects for the user.
    """
    try:
        rows = get_rows(QUEUE_SHEET)
    except HttpError:
        return []

    header, *data = rows
    queue = []
    for r in data:
        if not r or r[0] != user_id:
            continue
        queue.append({
            "key": r[1],
            "start_ts": float(r[2]),
            "end_ts": float(r[3]),
        })
    return queue


def complete_research_job(context):
    """
    Job that runs periodically to move completed projects
    from queue to completed sheet.
    """
    now = time.time()
    try:
        rows = get_rows(QUEUE_SHEET)
    except HttpError as e:
        logger.error("complete_research_job: failed to load '%s': %s", QUEUE_SHEET, e)
        return

    header, *data = rows
    for idx, r in enumerate(data, start=1):
        try:
            end_ts = float(r[3])
        except Exception:
            continue
        if end_ts <= now:
            user_id, key = r[0], r[1]
            ts_iso = datetime.utcnow().isoformat()
            append_row(COMPLETED_SHEET, [user_id, key, ts_iso])
            # blank out finished entry
            update_row(QUEUE_SHEET, idx, [""] * len(header))


def cancel_research(user_id: str, key: str) -> bool:
    """
    Cancel a queued research project for the user.
    Returns True if found & removed, False otherwise.
    """
    try:
        rows = get_rows(QUEUE_SHEET)
    except HttpError as e:
        logger.error("cancel_research: failed to load '%s': %s", QUEUE_SHEET, e)
        return False

    header, *data = rows
    for idx, r in enumerate(data, start=1):
        if r[0] == user_id and r[1] == key:
            update_row(QUEUE_SHEET, idx, [""] * len(header))
            return True
    return False
