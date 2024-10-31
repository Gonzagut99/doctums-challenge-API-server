from typing import Dict, Callable, Awaitable
from fastapi import WebSocket

from app.websockets.ws_manager import ConnectionManager

class Dispatcher:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.handlers: Dict[str, Callable] = {
            "join": self.handle_join,
            "submit_plan": self.handle_submit_plan,
            "roll_dice": self.handle_roll_dice,
            "select_avatar": self.handle_select_avatar,
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
        player_id = message.get("playerId")
        # Add player to game session
        response = {
            "method": "join",
            "status": "success",
            "message": f"Player {player_id} has joined the game!"
        }
        await self.manager.broadcast(game_id, response)

    async def handle_submit_plan(self, game_id: str, websocket: WebSocket, message: dict):
        player_id = message.get("playerId")
        actions = message.get("actions")
        # Process action plan submission
        response = {
            "method": "submit_plan",
            "status": "success",
            "message": f"Plan submitted for player {player_id}"
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

    async def handle_select_avatar(self, game_id: str, websocket: WebSocket, message: dict):
        player_id = message.get("playerId")
        avatar_id = message.get("avatarId")
        # Assign avatar to player
        response = {
            "method": "select_avatar",
            "status": "success",
            "player": {"playerId": player_id, "avatar": avatar_id}
        }
        await self.manager.broadcast(game_id, response)

    async def handle_start_game(self, game_id: str, websocket: WebSocket, message: dict):
        # Initialize game for all players
        response = {
            "method": "start_game",
            "status": "success",
            "message": "The game has started!"
        }
        await self.manager.broadcast(game_id, response)
