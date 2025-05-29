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

    def start_game(self, player_id):
        # Check if player exists, if not, create them
        player = self.player_manager.get_player(player_id)
        if player:
            return {'success': True, 'message': 'Welcome back!'}
        else:
            result = self.player_manager.create_player(player_id)
            if result.get('success'):
                return {'success': True, 'message': 'Game started!'}
            else:
                return {'success': False, 'message': result.get('message', 'Could not start game.')} 