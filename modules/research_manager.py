# Patched modules/research_manager.py with error handling for load_research_defs

patched_research_manager = """
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
    \"""
    Load all tech definitions from the Research sheet.
    Returns a dict mapping tech_key -> tech_info dict.
    \"""
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
        # parse fields
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
        # parse start/end timestamps if limited
        if info["is_limited"]:
            try:
                info["start_ts"] = datetime.fromisoformat(info.get("start_ts", ""))
                info["end_ts"]   = datetime.fromisoformat(info.get("end_ts", ""))
            except Exception:
                info["start_ts"] = None
                info["end_ts"]   = None
        techs[info["key"]] = info
    return techs

# ... rest of file unchanged ...
"""

# Write patched file to disk
with open('/mnt/data/research_manager_patched.py', 'w') as f:
    f.write(patched_research_manager)

"/mnt/data/research_manager_patched.py"
