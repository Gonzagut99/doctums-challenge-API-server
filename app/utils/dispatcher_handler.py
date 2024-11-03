import json
from typing import Dict, Callable, Awaitable
from fastapi import WebSocket


from app.LogicEntities.Context import Context
from app.LogicEntities.GameSession import GameSessionLogic
from app.LogicEntities.Player import Player
from app.services.PlayerService import PlayerService
from app.websockets.ws_manager import ConnectionManager

class Dispatcher:
    def __init__(self, session: GameSessionLogic, context: Context):
        self.manager = session.manager
        self.context = context
        self.session = session
        self.player = None
        self.player_service = PlayerService()
        self.handlers: Dict[str, Callable] = {
            "join": self.handle_join,
            "submit_plan": self.handle_submit_plan,
            "roll_dice": self.handle_roll_dice,
            "start_game": self.handle_start_game,
            # Add more handlers as needed
        }
    
    async def dispatch(self, game_id: str, websocket: WebSocket, message: dict):
        method = message.get("method")
        handler = self.handlers.get(method)
        
        if handler:
            await handler(game_id, websocket, message)
        else:
            await websocket.send_json({"status": "error", "message": f"Unknown method: {method}"})

    async def handle_join(self, game_id: str, websocket: WebSocket, message: dict):
        player_id = message.get("player_id")

        if self.player is None:
          db_player = self.player_service.get_player(player_id)
          #Validate if the player belongs to the game session
          if db_player.game_session_id != game_id:
              await websocket.send_json({"status": "error", "message": "El jugador no pertenece a la sesión de juego"})
              await websocket.close()
              return
          self.player = Player(context=self.context, name=db_player.name, id=db_player.id, avatar_id=db_player.avatar_id, connection_port=websocket.client.port)
          if len(self.session.get_players()) == 0:
              self.session.convert_to_host(self.player) # First player to join is the host
          self.session.add_player(self.player)    # Only fetch player from game session once per connection
          
        # Add player to game session
        response = {
            "method": "join",
            "status": "success",
            "message": f"Jugador {self.player.name} se ha unido!",
            "game": {
                #"state": "waiting_for_players",
                "id": game_id,
                "players": [
                    {"id": p.id, "name": p.name, "isHost": p.is_host, "avatarId" : p.avatar_id} for p in self.session.get_players()
                ],
            }
        }
        await self.manager.broadcast(json.dumps(response))
        
    async def handle_start_game(self, game_id: str, websocket: WebSocket, message: dict):
        if not self.player.is_host:
          await self.manager.send_personal_json({"status": "error", "message": "Only the host can start the game"}, websocket)
          return
        self.session.load_players_games()
        connected_players = self.session.get_players()
        # Initialize game for all players
        for player in connected_players:
            response = {
                "method": "start_game",
                "status": "success",
                "message": "The game has started!",
                "player": {
                    "id": player.id,
                    "name": player.name,
                    "avatarId": player.avatar_id
                }
                
            }
            await self.manager.send_message_by_port(response, player.connection_port)


    async def handle_submit_plan(self, game_id: str, websocket: WebSocket, message: dict):
        actions = message.get("actions")
        # Process action plan submission
        response = {
            "method": "submit_plan",
            "status": "success",
            "message": f"Plan submitted for player {self.player.name}"
        }
        await self.manager.broadcast(game_id, response)

    async def handle_roll_dice(self, game_id: str, websocket: WebSocket, message: dict):
        player_id = message.get("playerId")
        # Simulate dice roll and movement
        dice_result = [4, 3]  # Example roll result
        total_advance = sum(dice_result)
        response = {
            "method": "dice_result",
            "playerId": player_id,
            "dice": dice_result,
            "totalAdvance": total_advance,
            "message": f"Player {player_id} rolled the dice and advanced {total_advance} days."
        }
        await self.manager.broadcast(game_id, response)

