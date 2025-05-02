# modules/resource_manager.py

import time
from sheets_service import get_rows, update_row

# Resource production rates per level
MINERALS_PER_LEVEL_PER_HOUR = 20  # per mine level
ENERGY_PER_LEVEL_PER_HOUR = 10    # per power plant level

def tick_resources(user_id: str) -> dict:
    """
    Calculate and update resources for `user_id` based on time elapsed
    since last tick (stored in Players.last_seen).
    Returns dict with 'minerals' and 'energy' added.
    """
    # Fetch players data
    players = get_rows('Players')
    header, *rows = players

    # Find player row
    for idx, row in enumerate(rows, start=1):
        if row[0] == user_id:
            prow = row.copy()
            prow_idx = idx
            break
    else:
        raise ValueError(f"User {user_id} not found in Players sheet")

    # Extract current values
    last_seen = float(prow[6])
    minerals = int(prow[4])
    energy = int(prow[5])

    now = time.time()
    elapsed = now - last_seen
    if elapsed < 60:
        return {'minerals': 0, 'energy': 0}

    # Fetch building levels
    buildings = get_rows('Buildings')
    _, *b_rows = buildings
    total_mine_levels = sum(int(r[2]) for r in b_rows
                            if r[0] == user_id and r[1] == 'Mine')
    total_pp_levels   = sum(int(r[2]) for r in b_rows
                            if r[0] == user_id and r[1] == 'Power Plant')

    # Hourly production
    minerals_per_hr = total_mine_levels * MINERALS_PER_LEVEL_PER_HOUR
    energy_per_hr   = total_pp_levels * ENERGY_PER_LEVEL_PER_HOUR

    # Calculate increments
    hours = elapsed / 3600
    add_minerals = int(minerals_per_hr * hours)
    add_energy   = int(energy_per_hr * hours)

    # Update sheet if needed
    if add_minerals or add_energy:
        prow[4] = str(minerals + add_minerals)
        prow[5] = str(energy + add_energy)
        prow[6] = str(int(now))
        update_row('Players', prow_idx, prow)

    return {'minerals': add_minerals, 'energy': add_energy}
