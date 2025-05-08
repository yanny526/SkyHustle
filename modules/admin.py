# bot/modules/admin.py

class AdminCommand:
    def __init__(self, name, description, callback):
        self.name = name
        self.description = description
        self.callback = callback

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description
        }

# Define admin commands
admin_commands = [
    AdminCommand("reset_player", "Reset a player's data", lambda uid: f"Player {uid} data reset"),
    AdminCommand("grant_resources", "Grant resources to a player", lambda uid: f"Resources granted to {uid}"),
    AdminCommand("manage_event", "Create or modify game events", lambda uid: f"Event managed by {uid}"),
]
