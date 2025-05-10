# bot/modules/buildings.py

class Building:
    def __init__(self, name, level=1, production_rate=0):
        self.name = name
        self.level = level
        self.production_rate = production_rate

    def upgrade(self):
        self.level += 1
        self.production_rate *= 1.5  # Increase production by 50% per level

    def to_dict(self):
        return {
            "name": self.name,
            "level": self.level,
            "production_rate": self.production_rate
        }