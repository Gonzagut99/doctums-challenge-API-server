#Tal vez podriamos hacer un patron observe para que el game se suscriba a los eventos que le interesan
from app.LogicEntities.GameSession import GameSessionLogic
from app.LogicEntities.PlayerGame import PlayerGame

class GameLogic(GameSessionLogic):
    def __init__(self):
        super()
        self.playersgames: list[PlayerGame] = []
        
    def load_players_games(self):
        self.playersgames = [PlayerGame(player=player) for player in self.connected_players]
    
    def start_game(self, high_dice_score_player: int):
        self.order_players(high_dice_score_player)
        self.first_player = self.connected_players[0]

    def start_month_turns(self):
        self.current_player = self.first_player

    def next_player(self):
        current_index = self.connected_players.index(self.current_player)
        next_index = (current_index + 1) % len(self.players)
        self.current_player = self.connected_players[next_index]

    def play(self):
        while not self.game.is_over():
            self.game.play(self.current_player)
            self.next_player()
        print('Game over!')

class TurnManager:
    def __init__(self):
        self.current_turn = 0
        self.current_month = 0

    def start_new_month(self):
        self.current_month += 1

    def start_new_turn(self):
        self.current_turn += 1

    def get_current_month(self):
        return self.current_month

    def get_current_turn(self):
        return self.current_turn

    def get_current_player(self):
        return self.playersgames[self.current_turn % len(self.playersgames)]

    def get_current_player_id(self):
        return self.current_turn % len(self.playersgames)