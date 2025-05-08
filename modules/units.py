# bot/modules/units.py

class Unit:
    def __init__(self, name, power, cost):
        self.name = name
        self.power = power
        self.cost = cost
        self.count = 0

    def train(self, quantity):
        self.count += quantity

    def to_dict(self):
        return {
            "name": self.name,
            "power": self.power,
            "cost": self.cost,
            "count": self.count
        }