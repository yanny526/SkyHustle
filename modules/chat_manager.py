class ChatManager:
    """Minimal stub for ChatManager. Extend with actual chat logic as needed."""
    def __init__(self):
        self.messages = []  # Store chat messages as a list of dicts

    def add_message(self, player_id, name, message):
        self.messages.append({
            'player_id': player_id,
            'name': name,
            'message': message
        })

    def get_messages(self, limit=20):
        """Return the most recent chat messages."""
        return self.messages[-limit:] 