# bot/modules/alliance.py

class Alliance:
    def __init__(self, name, leader_id):
        self.name = name
        self.leader_id = leader_id
        self.members = [leader_id]
        self.rank = 1
        self.total_power = 0

    def add_member(self, player_id):
        self.members.append(player_id)

    def remove_member(self, player_id):
        if player_id in self.members:
            self.members.remove(player_id)

    def update_power(self, player_power):
        self.total_power += player_power

    def to_dict(self):
        return {
            "name": self.name,
            "leader_id": self.leader_id,
            "members": self.members,
            "rank": self.rank,
            "total_power": self.total_power
        }
