from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.LogicEntities.Player import Player
from app.services.PlayerService import PlayerService
from app.services.GameSessionService import GameSessionService
from app.main import context
from app.utils.dispatcher_handler import Dispatcher
from app.websockets.ws_manager import ConnectionManager

ws_router = APIRouter(prefix="/ws")
manager = ConnectionManager()
dispatcher = Dispatcher(manager=manager)

@ws_router.websocket("/game/create/{game_id}")
async def create_game_session(websocket: WebSocket, game_id: str):
    if not game_id :
        await websocket.close()

    await websocket.accept()  # Accept the WebSocket connection temporarily

    # Check if the game session already exists
    is_game_registered = GameSessionService().get_game_session(game_id)
    if not is_game_registered:
        await websocket.send_json({"status": "error", "message": "Game session doesn't exists"})
        await websocket.close()
        return

    # Create a new game session
    new_game_session_logic_created = GameSessionService().generate_new_game_session_logic(game_id, game_context=context)
    if not new_game_session_logic_created:
        await websocket.send_json({"status": "error", "message": "Failed to create game session"})
        await websocket.close()
    else:
        await websocket.send_json({"status": "success", "message": "Game session created successfully"})
        await websocket.close()  # Close the WebSocket since this endpoint is only for setup


@ws_router.websocket("/game/connect/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    if not game_id :
        await websocket.close()
    
    # Check if the game session exists
    game_session_logic = GameSessionService().get_session_logic(game_id)
    if not game_session_logic:
        await websocket.send_json({"status": "error", "message": "Game session does not exist"})
        await websocket.close()
        return
    
    await manager.add_connection(websocket)
    
    # Initialize player variable outside the loop
    player = None

    try:
        while True:
            data = await websocket.receive_json()
            player_id = data.get("player_id")

            # Only fetch player from game session once per connection
            if player is None:
                db_player = PlayerService().get_player(player_id)
                #Validate if the player belongs to the game session
                if db_player.game_session_id != game_id:
                    await websocket.send_json({"status": "error", "message": "Player does not belong to the game session"})
                    await websocket.close()
                    return
                player = Player(context=context, name=db_player.name, id=db_player.id)
                game_session_logic.add_player(player)
            
            # Use cached `player` in further processing or dispatch if needed
            #await dispatcher.dispatch(game_id, websocket, data)
            
    except WebSocketDisconnect:
        manager.remove_connection(websocket)
        await manager.broadcast(f"Un Jugador se ha desconectado")
    
    
