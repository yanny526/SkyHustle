def find_by_name(alias, players):
    for cid, p in players.items():
        if p["name"].lower() == alias.lower():
            return cid, p
    return None, None
