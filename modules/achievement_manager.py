from sheets_service import get_rows, append_row, update_row
from datetime import date
from modules.building_manager import get_building_info

class Achievement:
    def __init__(self, aid, description, key, value, rc, rm, re):
        self.id = aid
        self.description = description
        self.key = key
        self.value = int(value)
        self.reward_credits = int(rc)
        self.reward_minerals = int(rm)
        self.reward_energy = int(re)


def load_achievements():
    """Load all active achievements."""
    rows = get_rows("Achievements")
    header, data = rows[0], rows[1:]
    idx = {col: i for i, col in enumerate(header)}
    out = []
    for r in data:
        if r[idx['active']].lower() != 'true':
            continue
        out.append(Achievement(
            aid=r[idx['achievement_id']],
            description=r[idx['description']],
            key=r[idx['requirement_key']],
            value=r[idx['requirement_value']],
            rc=r[idx['reward_credits']],
            rm=r[idx['reward_minerals']],
            re=r[idx['reward_energy']],
        ))
    return out


def get_player_achievement(uid: str, aid: str):
    """Return (row_index, row) if user already unlocked this achievement."""
    rows = get_rows("PlayerAchievements")
    for i, r in enumerate(rows[1:], start=1):
        if r[0] == uid and r[1] == aid:
            return i, r
    return None, None


def _current_stat(uid: str, key: str) -> int:
    """Compute the user’s current value for a given requirement_key."""
    # Combat log: total attacks or wins
    if key in ('attacks_total', 'attacks_won'):
        log = get_rows('CombatLog')[1:]
        if key == 'attacks_total':
            return sum(1 for r in log if r[0] == uid)
        else:
            return sum(1 for r in log if r[0] == uid and r[3] == 'win')

    # Building level checks
    if key.startswith('build_level_'):
        # e.g. 'build_level_Barracks'
        bname = key.split('_', 2)[2]
        info = get_building_info(uid)
        for btype, lvl in info.items():
            if btype.lower().replace(' ', '') == bname.lower().replace(' ', ''):
                return lvl
        return 0

    # Unit training counts (e.g., infantry_trained)
    if key.endswith('_trained'):
        unit_key = key.replace('_trained', '')
        army_rows = get_rows('Army')[1:]
        return sum(int(r[2]) for r in army_rows if r[0] == uid and r[1] == unit_key)

    # Leaderboard rank
    if key == 'leaderboard_rank':
        # compute ranks
        from modules.leaderboard_manager import get_rank
        return get_rank(uid)

    # Unknown key
    return 0


def check_and_award_achievements(uid: str):
    """
    Check every achievement; if met & not yet unlocked, 
    award resources, record it, and return list of newly unlocked.
    """
    today = date.today().isoformat()
    newly = []

    achs = load_achievements()
    for a in achs:
        idx, prow = get_player_achievement(uid, a.id)
        if prow:
            continue  # already unlocked

        if _current_stat(uid, a.key) < a.value:
            continue

        # Grant rewards
        players = get_rows("Players")
        header, pdata = players[0], players[1:]
        pidx = [r[0] for r in pdata].index(uid) + 1
        row = players[pidx]
        row[3] = str(int(row[3]) + a.reward_credits)
        row[4] = str(int(row[4]) + a.reward_minerals)
        row[5] = str(int(row[5]) + a.reward_energy)
        update_row("Players", pidx, row)

        # Record in PlayerAchievements
        append_row("PlayerAchievements", [uid, a.id, today, "awarded"])

        newly.append(a)

    return newly
