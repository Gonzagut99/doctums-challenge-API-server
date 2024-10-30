from app.LogicEntities.Player import Player

class GameSessionLogic:
    def __init__(self, session_id: str):
        self.session_id:str = session_id
        self.connected_players:list[Player] = []
        self.first_player:Player|None = None
        self.current_player:Player|None = None
        self.next_player:Player|None = None
        self.max_players:int = 4
        self.is_over:bool = False


    def add_player(self, player: Player):
        if len(self.connected_players) == self.max_players:
            raise Exception('Max players reached')
        self.connected_players.append(player)
        if player not in self.connected_players:
            return False
        return True
        
    def get_players(self) -> list[Player]:
        return self.connected_players
    
    def get_current_player(self) -> Player:
        return self.current_player

    def get_first_player(self) -> Player:
        return self.first_player
    
    def get_player(self, player_id: int) -> Player:
        return self.connected_players[player_id]
    
    #After all players have rolled the dice, the player with the highest score will be the first player to play   
    def order_players(self, high_dice_score_player: int):
        self.connected_players = self.connected_players[high_dice_score_player:] + self.connected_players[:high_dice_score_player]
    
    def remove_player(self, player: Player):
        self.connected_players.remove(player)

   