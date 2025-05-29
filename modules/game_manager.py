class GameManager:
    def __init__(self, player_manager=None, bag_manager=None, shop_manager=None, black_market_manager=None,
                 resource_manager=None, progression_manager=None, achievement_manager=None, friend_manager=None,
                 alliance_manager=None, premium_manager=None):
        self.player_manager = player_manager
        self.bag_manager = bag_manager
        self.shop_manager = shop_manager
        self.black_market_manager = black_market_manager
        self.resource_manager = resource_manager
        self.progression_manager = progression_manager
        self.achievement_manager = achievement_manager
        self.friend_manager = friend_manager
        self.alliance_manager = alliance_manager
        self.premium_manager = premium_manager 