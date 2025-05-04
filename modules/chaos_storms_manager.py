import random
from sheets_service import get_rows, update_row

# Define five Chaos Storms (3 destructive, 2 beneficial)
STORMS = [
    {
        'id': 'ember_rain',
        'name': 'Ember Rain',
        'emoji': '🌋',
        'story': (
            'Dark ember rain scorches your mineral caches,\n'
            'burning away 100 Minerals from every commander.'
        ),
        'delta': {'minerals': -100}
    },
    {
        'id': 'silver_gale',
        'name': 'Silver Gale',
        'emoji': '🍃',
        'story': (
            'A refreshing silver gale revitalizes everyone’s energy,\n'
            'granting +150 Energy to all.'
        ),
        'delta': {'energy': +150}
    },
    {
        'id': 'ruinsquake',
        'name': 'Ruinsquake',
        'emoji': '🏚️',
        'story': (
            'Tremors shake your base foundations,\n'
            'costing 100 Credits from each commander.'
        ),
        'delta': {'credits': -100}
    },
    {
        'id': 'golden_sunrise',
        'name': 'Golden Sunrise',
        'emoji': '🌅',
        'story': (
            'A golden sunrise bathes the land,\n'
            'bestowing +200 Minerals to every commander.'
        ),
        'delta': {'minerals': +200}
    },
    {
        'id': 'voidstorm',
        'name': 'Voidstorm',
        'emoji': '🌀',
        'story': (
            'An unnatural voidstorm rips through,\n'
            'siphoning 50 Energy and 50 Credits from all.'
        ),
        'delta': {'energy': -50, 'credits': -50}
    },
]

def get_random_storm():
    """Pick one of the five storms at random."""
    return random.choice(STORMS)

def apply_storm(storm):
    """
    Apply the storm's resource changes to every player
    in the Players sheet.
    """
    players = get_rows('Players')
    for idx, row in enumerate(players[1:], start=1):
        credits = int(row[3])
        minerals = int(row[4])
        energy = int(row[5])

        # Apply deltas, ensuring no negatives
        d = storm['delta']
        credits = max(0, credits + d.get('credits', 0))
        minerals = max(0, minerals + d.get('minerals', 0))
        energy = max(0, energy + d.get('energy', 0))

        row[3], row[4], row[5] = str(credits), str(minerals), str(energy)
        update_row('Players', idx, row)
