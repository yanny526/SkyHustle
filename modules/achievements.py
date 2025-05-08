# bot/modules/achievements.py

class Achievement:
    def __init__(self, name, description, reward):
        self.name = name
        self.description = description
        self.reward = reward
        self.unlocked = False

    def unlock(self):
        self.unlocked = True

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "reward": self.reward,
            "unlocked": self.unlocked
        }
