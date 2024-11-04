#Tal vez podriamos hacer un patron observe para que el game se suscriba a los eventos que le interesan
from app.LogicEntities.GameSession import GameSessionLogic
from app.LogicEntities.Player import Player
from app.LogicEntities.PlayerGame import PlayerGame

class GameLogic(GameSessionLogic):
    def __init__(self, context, session_id):
        super().__init__(session_id) 
        self.context = context
        self.playersgames: list[PlayerGame] = []
        self.turn_manager = TurnManager()
        
    def load_players_games(self):
        self.playersgames = [PlayerGame(player=player) for player in self.connected_players]
        for playergame in self.playersgames:
            playergame.load_player_data()
    
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
        """
        Initialize the TurnManager with a list of player IDs in the order they will take their turns.
        
        Args:
            player_ids (List[str]): List of player IDs in the desired turn order.
        """
        self.player_order: list[str] = []  # A fixed order of players based on player IDs
        self.player_detailed_list: list[dict] = []  # A fixed order of players based on player IDs
        self.current_turn_index = 0     # Index of the current player in the turn order
        self.turn_direction = 1         # Used to manage turn order direction (1 = forward, -1 = backward)
    
    def get_turn_order_list(self):
        return self.player_detailed_list

        
    def set_turn_order(self, players: list[Player]):
        """
        Sets the turn order based on dice rolls of each player.
        Players with the highest dice roll sum go first.
        
        Args:
            players (List[Player]): List of Player objects.
        """
        # Roll dice for each player and store their total roll with their ID
        roll_results = []
        
        for player in players:
            dices, total = player.throw_dices(5)
            roll_results.append((player.id, total))
            self.player_detailed_list.append({"playerId": player.id,"name": player.name, "dices": dices.tolist(), "total": int(total)})

        # Sort players by dice roll total in descending order (highest roll goes first)
        sorted_players = sorted(roll_results, key=lambda x: x[1], reverse=True)

        # Set player_order based on sorted player IDs
        self.player_order = [player_id for player_id, _ in sorted_players]
        self.current_turn_index = 0  # Reset to the start of the new turn order
    
    

    def get_current_player(self) -> str:
        """Return the player ID of the current player's turn."""
        return self.player_order[self.current_turn_index]

    def get_next_player(self) -> str:
        """
        Calculate and return the player ID of the next player in the turn order.
        This doesn't advance the turn; it just previews the next player.
        """
        next_index = (self.current_turn_index + self.turn_direction) % len(self.player_order)
        return self.player_order[next_index]

    def advance_turn(self):
        """
        Move to the next player’s turn in the order.
        Wrap around if reaching the end of the player list.
        """
        self.current_turn_index = (self.current_turn_index + self.turn_direction) % len(self.player_order)

    def skip_turn(self):
        """
        Skip the turn for the next player.
        The `advance_turn` method is called twice to move to the subsequent player.
        """
        self.advance_turn()  # Skip to the next player
        self.advance_turn()  # Move to the player after the next

    def reverse_turn_order(self):
        """
        Reverse the direction of turns. This can be useful for special game events.
        """
        self.turn_direction *= -1

    def reset_turns(self):
        """
        Reset to the beginning of the turn order.
        Useful at the start of a new game or a new round.
        """
        self.current_turn_index = 0
        self.turn_direction = 1  # Default direction is forward