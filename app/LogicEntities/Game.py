#Tal vez podriamos hacer un patron observe para que el game se suscriba a los eventos que le interesan
from app.LogicEntities.GameSession import GameSessionLogic
from app.LogicEntities.Player import Player
from app.LogicEntities.PlayerGame import PlayerGame

class GameLogic(GameSessionLogic):
    def __init__(self, context, session_id):
        super().__init__(session_id) 
        self.context = context
        self.playersgames: list[PlayerGame] = []
        self.turn_manager = TurnManager(self.connected_players)
        self.is_first_general_turn = False
        self.isOver = True
        
    def load_players_games(self):
        self.playersgames = [PlayerGame(player=player) for player in self.connected_players]
        for playergame in self.playersgames:
            playergame.load_player_data()

    def get_playergame(self, player: Player) -> PlayerGame:
        return next(playergame for playergame in self.playersgames if playergame.player == player)
    
    def set_game_initial_state(self):
        self.load_players_games()
        self.isOver = False
        self.is_first_general_turn = True
        self.turn_manager.set_turn_order()
        
    def start_game(self):
        self.set_game_initial_state()
    
    # #First turn of the session and first player turn
    # def start_current_turn_first_turn(self):
    #     if self.turn_manager.get_current_player() is None:
    #         raise Exception("No current player has been set yet")
    #     self.turn_manager.launch_first_turn_begin_actions(self.playersgames)
    
    # #After submitting first turn action plan
    # def continue_with_first_general_turn(self):
    #     self.turn_manager.launch_first_turn_actions(self.playersgames)
        
    # # After previous turn has been finished to update current turn
    # def proceed_with_next_turn(self):
    #     self.turn_manager.advance_turn()
    #     self.turn_manager.launch_current_turn_actions(self.playersgames)
    
    # #After current turn has advanced and been updated
    # def start_new_turn(self):
    #     self.turn_manager.launch_current_turn_begin_actions(self.playersgames)
    
    # #After submitting standard action plan
    # def continue_with_current_turn(self):
    #     self.turn_manager.launch_current_turn_actions(self.playersgames)
    
    # def play(self):
    #     self.proceed_with_next_turn()

    # def start_month_turns(self):
    #     self.current_player = self.first_player

    # def next_player(self):
    #     current_index = self.connected_players.index(self.current_player)
    #     next_index = (current_index + 1) % len(self.players)
    #     self.current_player = self.connected_players[next_index]

    # def play(self, playerGame: PlayerGame):
    #     while not playerGame.is_journey_finished():
    #         self.game.play(self.current_player)
    #         # self.next_player()
    #     print('Game over!')

class TurnManager:
    def __init__(self, connected_players: list[Player]):
        """
        Initialize the TurnManager with a list of player IDs in the order they will take their turns.
        
        Args:
            player_ids (List[str]): List of player IDs in the desired turn order.
        """
        self.first_player = str | None
        self.current_player = str | None
        self.connected_players = connected_players
        self.player_order: list[str] = []  # A fixed order of players based on player IDs
        self.player_detailed_list: list[dict] = []  # A fixed order of players based on player IDs
        self.current_turn_index = 0     # Index of the current player in the turn order
        self.turn_direction = 1         # Used to manage turn order direction (1 = forward, -1 = backward)
        self.last_turn:int = 0
    
    def get_turn_order_list(self):
        return self.player_detailed_list
    
    # Se llaman una vez para cada jugador que comienza el juego    
    # def launch_first_turn_begin_actions(self, playersgames: list[PlayerGame]):
    #     for playergame in playersgames:
    #         if playergame.player.id == self.get_current_player():
    #             playergame.set_first_turn()
    #             playergame.start_game_journey()
    #         else:
    #             raise Exception("It is not the turn of this player")
                
    # def launch_after_planning_first_turn_actions(self, playersgames: list[PlayerGame]):
    #     for playergame in playersgames:
    #         if playergame.player.id == self.get_current_player():
    #             playergame.begin_regular_turn() #After rolling the dices the first turn can end up in a new month
    
    # # If the prevouss process above ends up in a new month, we should wait 'til the player goes through the planning phase again, in any case, at the end, we call this method
    # def proceed_with_remaining_first_turn_actions(self, playersgames: list[PlayerGame]):
    #     for playergame in playersgames:
    #         if playergame.player.id == self.get_current_player():
    #             playergame.resume_turn()      
    
    # Execute 1st step
    # Called when any other turn after the first one is finished           
    def proceed_with_new_turn_in_journey(self, playersgames: list[PlayerGame]):
        for playergame in playersgames:
            if playergame.player.id == self.get_current_player():
                playergame.begin_turn()

    # 2nd step is directly applied to the player game
    
    # Execute 3rd step
    # Se llama para continuar un turno cualquiera
    def proceed_with_raimining_turn_actions(self, playersgames: list[PlayerGame]):
        for playergame in playersgames:
            if playergame.player.id == self.get_current_player():
                playergame.resume_turn()
    
    def _roll_dices_for_order_players(self, players: list[Player]):
        """
        Sets the turn order based on dice rolls of each player.
        Players with the highest dice roll sum go first.
        
        Args:
            players (List[Player]): List of Player objects.
        """
        # Roll dice for each player and store their total roll with their ID
        for player in players:
            dices, total = player.throw_dices(2) #2 dices
            self.player_detailed_list.append({"playerId": player.id,"name": player.name, "dices": dices.tolist(), "total": int(total)})
        
    def _sort_player_order(self, players: list[Player]):
        self._roll_dices_for_order_players(players)        
        # Sort players by dice roll total in descending order because the highest score normally goes at the end(highest roll goes first)
        self.player_detailed_list = sorted(self.player_detailed_list, key=lambda x: x["total"], reverse=True)
        
    def set_turn_order(self):
        self._sort_player_order(self.connected_players)
        # Set player_order based on sorted player IDs
        self.player_order = [ordered_player["playerId"] for ordered_player in self.player_detailed_list]
        self.current_turn_index = 0  # Reset to the start of the new turn order
        self.current_player = self.player_order[self.current_turn_index]
        
    def get_current_player(self) -> str:
        if self.current_player is None:
            raise Exception("No current player has been set yet")
        """Return the player ID of the current player's turn."""
        return self.player_order[self.current_turn_index]

    def advance_turn(self):
        """
        Move to the next player’s turn in the order.
        Wrap around if reaching the end of the player list.
        """
        self.last_turn = self.current_turn_index
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