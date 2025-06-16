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
        info["prereqs"] = [p.strip() for p in info.get("prereqs", "").split(",") if p.strip()]

        try:
            info["tier"] = int(info.get("tier", "1"))
        except ValueError:
            info["tier"] = 1

        for fld in ("cost_c", "cost_m", "cost_e", "time_sec", "token_cost", "slots_required"):
            try:
                info[fld] = int(info.get(fld, "0"))
            except ValueError:
                info[fld] = 0

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
    Return a list of research definitions the user has unlocked
    by prerequisites and time window, regardless of current resources.
    """
    defs = load_research_defs()
    if not defs:
        return []

    # load what they've already completed
    try:
        completed = [r[1] for r in get_rows(COMPLETED_SHEET)[1:]]
    except Exception:
        completed = []

    now = datetime.utcnow()
    available = []
    for info in defs.values():
        key = info["key"]
        # skip already completed
        if key in completed:
            continue
        # skip outside limited-time window
        if info["is_limited"] and (
           (info.get("start_ts") and now < info["start_ts"]) or
           (info.get("end_ts") and now > info["end_ts"])
        ):
            continue
        # skip if prerequisites not done
        if any(pr not in completed for pr in info["prereqs"]):
            continue

        # now unlocked, regardless of resources
        available.append(info)

    return sorted(available, key=lambda t: (t["tier"], t["key"]))


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
            try:
                credits = int(row[3]); minerals = int(row[4]); energy = int(row[5])
            except Exception:
                return False
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

    now_ts = time.time()
    end_ts = now_ts + info["time_sec"]
    append_row(QUEUE_SHEET, [user_id, key, str(now_ts), str(end_ts)])
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
            "key":      r[1],
            "start_ts": float(r[2]),
            "end_ts":   float(r[3]),
        })
    return queue


def complete_research_job(context):
    """
    Job that moves completed projects from queue to completed sheet.
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
            if float(r[3]) <= now:
                user_id, key = r[0], r[1]
                append_row(COMPLETED_SHEET, [user_id, key, datetime.utcnow().isoformat()])
                update_row(QUEUE_SHEET, idx, [""] * len(header))
        except Exception:
            continue


def cancel_research(user_id: str, key: str) -> bool:
    """
    Cancel a queued research project, refunding costs, then removing it.
    """
    # load queue
    try:
        queue_rows = get_rows(QUEUE_SHEET)
    except HttpError as e:
        logger.error("cancel_research: failed to load '%s': %s", QUEUE_SHEET, e)
        return False

    header_q, *queue_data = queue_rows

    # refund
    defs = load_research_defs()
    info = defs.get(key)
    if info:
        try:
            players = get_rows(PLAYERS_SHEET)
        except HttpError as e:
            logger.error("cancel_research: failed to load '%s' for refund: %s", PLAYERS_SHEET, e)
        else:
            header_p, *players_data = players
            for p_idx, prow in enumerate(players_data, start=1):
                if prow[0] == user_id:
                    try:
                        c = int(prow[3]) + info["cost_c"]
                        m = int(prow[4]) + info["cost_m"]
                        e = int(prow[5]) + info["cost_e"]
                    except Exception:
                        break
                    prow[3], prow[4], prow[5] = str(c), str(m), str(e)
                    update_row(PLAYERS_SHEET, p_idx, prow)
                    break

    # remove queue entry
    for idx, row in enumerate(queue_data, start=1):
        if row and len(row) >= 2 and row[0] == user_id and row[1] == key:
            update_row(QUEUE_SHEET, idx, [""] * len(header_q))
            return True
    return False
