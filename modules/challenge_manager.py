from sheets_service import get_rows, append_row, update_row
from datetime import date

class Challenge:
    def __init__(self, cid, ctype, description, key, value, reward_credits, reward_minerals, reward_energy):
        self.id = cid
        self.type = ctype
        self.description = description
        self.key = key
        self.value = int(value)
        self.reward_credits = int(reward_credits)
        self.reward_minerals = int(reward_minerals)
        self.reward_energy = int(reward_energy)

def load_challenges(ch_type: str):
    """Load active challenges of given type ('daily' or 'weekly')."""
    rows = get_rows("Challenges")
    header, data = rows[0], rows[1:]
    challenges = []
    idx = {col: i for i, col in enumerate(header)}
    for row in data:
        if row[idx['type']].lower() != ch_type:
            continue
        if row[idx['active']].lower() != 'true':
            continue
        challenges.append(Challenge(
            cid=row[idx['challenge_id']],
            ctype=row[idx['type']],
            description=row[idx['description']],
            key=row[idx['requirement_key']],
            value=row[idx['requirement_value']],
            reward_credits=row[idx['reward_credits']],
            reward_minerals=row[idx['reward_minerals']],
            reward_energy=row[idx['reward_energy']],
        ))
    return challenges

def get_player_challenge(uid: str, cid: str):
    """Return (row_index, row) for a player's challenge entry today."""
    rows = get_rows("PlayerChallenges")
    header, data = rows[0], rows[1:]
    today = date.today().isoformat()
    for i, row in enumerate(data, start=1):
        if row[0] == uid and row[1] == cid and row[2] == today:
            return i, row
    return None, None

def update_player_progress(uid: str, ch: Challenge, increment: int = 1):
    """Increment progress and mark complete if threshold reached."""
    today = date.today().isoformat()
    pc_idx, prow = get_player_challenge(uid, ch.id)

    if prow:
        # existing entry: bump progress_count
        prog = int(prow[4] or 0) + increment
        prow[4] = str(prog)
        # if now complete, set date_completed
        if prog >= ch.value and not prow[3]:
            prow[3] = today
        update_row("PlayerChallenges", pc_idx, prow)

    else:
        # new entry: [player_id,challenge_id,date_assigned,date_completed,progress_count,awarded]
        completed = today if increment >= ch.value else ""
        append_row("PlayerChallenges", [
            uid,
            ch.id,
            today,
            completed,
            str(increment),
            ""       # awarded flag
        ])

def award_challenges(uid: str, ch_type: str):
    """Grant rewards for any completed but not yet awarded challenges."""
    challenges = load_challenges(ch_type)
    for ch in challenges:
        pc_idx, prow = get_player_challenge(uid, ch.id)
        # prow[3] = date_completed, prow[5] = awarded flag
        if prow and prow[3] and prow[5] != 'awarded':
            # grant resources
            players = get_rows("Players")
            header, pdata = players[0], players[1:]
            pidx = [r[0] for r in pdata].index(uid) + 1
            row = players[pidx]
            row[3] = str(int(row[3]) + ch.reward_credits)
            row[4] = str(int(row[4]) + ch.reward_minerals)
            row[5] = str(int(row[5]) + ch.reward_energy)
            update_row("Players", pidx, row)
            # mark awarded
            prow[5] = 'awarded'
            update_row("PlayerChallenges", pc_idx, prow)
