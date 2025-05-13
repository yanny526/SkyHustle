# modules/research_manager.py

from datetime import datetime
import time
from sheets_service import get_rows, append_row, update_row

# Sheet names
RESEARCH_SHEET = "Research"
QUEUE_SHEET    = "ResearchQueue"
COMPLETED_SHEET = "CompletedResearch"
PLAYERS_SHEET   = "Players"

def load_research_defs():
    """
    Load all tech definitions from the Research sheet.
    Returns a dict mapping tech_key -> tech_info dict.
    """
    rows = get_rows(RESEARCH_SHEET)
    if not rows or len(rows) < 2:
        return {}
    header = rows[0]
    techs = {}
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        info = dict(zip(header, row))
        # parse fields
        info["prereqs"] = [p.strip() for p in info.get("prereqs", "").split(",") if p.strip()]
        info["tier"] = int(info.get("tier", "1"))
        for fld in ("cost_c", "cost_m", "cost_e", "time_sec", "token_cost", "slots_required"):
            info[fld] = int(info.get(fld, "0"))
        info["is_limited"] = str(info.get("is_limited", "")).upper() == "TRUE"
        # parse start/end timestamps if limited
        if info["is_limited"]:
            try:
                info["start_ts"] = datetime.fromisoformat(info["start_ts"])
                info["end_ts"] = datetime.fromisoformat(info["end_ts"])
            except Exception:
                info["start_ts"] = info["end_ts"] = None
        techs[info["key"]] = info
    return techs

def get_player_completed(user_id):
    """Return set of tech keys the player has completed."""
    rows = get_rows(COMPLETED_SHEET)
    completed = {r[1] for r in rows[1:] if r and r[0] == user_id}
    return completed

def get_queue(user_id):
    """
    Return list of dicts for queued research for the user:
    each with keys: key, start_ts (float), end_ts (float).
    """
    rows = get_rows(QUEUE_SHEET)
    queue = []
    for row in rows[1:]:
        if row and row[0] == user_id:
            try:
                queue.append({
                    "key": row[1],
                    "start_ts": float(row[2]),
                    "end_ts": float(row[3]),
                })
            except Exception:
                continue
    return queue

def get_available_research(user_id):
    """
    Return list of tech_info dicts that the user can start:
    - prerequisites met
    - not already completed
    - not currently in queue
    - if limited, current datetime within window
    """
    defs = load_research_defs()
    completed = get_player_completed(user_id)
    queued = {q["key"] for q in get_queue(user_id)}
    now = datetime.utcnow()
    available = []
    for key, info in defs.items():
        # skip already done or in queue
        if key in completed or key in queued:
            continue
        # limited check
        if info["is_limited"]:
            if not (info["start_ts"] and info["end_ts"] and info["start_ts"] <= now <= info["end_ts"]):
                continue
        # prereqs
        if any(pr not in completed for pr in info["prereqs"]):
            continue
        available.append(info)
    # sort by tier then name
    return sorted(available, key=lambda x: (x["tier"], x["name"]))

def start_research(user_id, tech_key):
    """
    Attempt to start research for tech_key:
    - Deduct costs from player's resources
    - Append a row in QUEUE_SHEET with start_ts and end_ts
    Returns True if successfully queued, False otherwise.
    """
    defs = load_research_defs()
    info = defs.get(tech_key)
    if not info:
        return False
    # fetch player row and deduct cost
    players = get_rows(PLAYERS_SHEET)
    header = players[0]
    uid_idx = header.index("user_id")
    cred_idx = header.index("credits")
    min_idx = header.index("minerals")
    eng_idx = header.index("energy")
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == user_id:
            credits = int(row[cred_idx])
            minerals = int(row[min_idx])
            energy = int(row[eng_idx])
            # check resources
            if credits < info["cost_c"] or minerals < info["cost_m"] or energy < info["cost_e"]:
                return False
            # deduct
            row[cred_idx] = str(credits - info["cost_c"])
            row[min_idx] = str(minerals - info["cost_m"])
            row[eng_idx] = str(energy - info["cost_e"])
            update_row(PLAYERS_SHEET, idx, row)
            break
    else:
        return False

    # queue entry
    now = time.time()
    end_ts = now + info["time_sec"]
    append_row(QUEUE_SHEET, [user_id, tech_key, str(int(now)), str(int(end_ts))])
    return True

def complete_research_job(context):
    """
    Job to run periodically: checks QUEUE_SHEET for completed items,
    moves them to COMPLETED_SHEET, and removes or marks them in QUEUE_SHEET.
    """
    now = time.time()
    rows = get_rows(QUEUE_SHEET)
    # header + data
    header = rows[0]
    for idx, row in enumerate(rows[1:], start=2):  # sheet rows start at 1, +1 for header
        try:
            user_id, tech_key, start_s, end_s = row[:4]
            if not end_s or float(end_s) > now:
                continue
            # mark completion
            append_row(COMPLETED_SHEET, [user_id, tech_key, str(int(now))])
            # remove from queue: clear row (overwrite with empty)
            update_row(QUEUE_SHEET, idx-1, [""] * len(header))
        except Exception:
            continue
