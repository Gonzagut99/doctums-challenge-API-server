from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.GameSessionService import GameSessionService
from app.utils.dispatcher_handler import Dispatcher

ws_router = APIRouter(prefix="/ws")


# @ws_router.websocket("/game/create/{game_id}")
# async def create_game_session(websocket: WebSocket, game_id: str):
#     if not game_id :
#         await websocket.close()

#     await websocket.accept()  # Accept the WebSocket connection temporarily

#     # Check if the game session already exists
#     is_game_registered = GameSessionService().get_game_session(game_id)
#     if not is_game_registered:
#         await websocket.send_json({"status": "error", "message": "Game session doesn't exists"})
#         await websocket.close()
#         return

#     # Create a new game session
#     new_game_session_logic_created = GameSessionService().generate_new_game_session_logic(game_id, game_context=context)
#     if not new_game_session_logic_created:
#         await websocket.send_json({"status": "error", "message": "Failed to create game session"})
#         await websocket.close()
#     else:
#         await websocket.send_json({"status": "success", "message": "Game session created successfully"})
#         await websocket.close()  # Close the WebSocket since this endpoint is only for setup


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

    await game_session_logic.manager.add_connection(websocket)
    
    dispatcher = Dispatcher(session=game_session_logic, context=game_session_logic.context)
    try:
        while True:
            data = await websocket.receive_json()
            # Use cached `player` in further processing or disp3atch if needed
            await dispatcher.dispatch(game_id, websocket, data)
            
    except WebSocketDisconnect:
        game_session_logic.manager.remove_connection(websocket)
        await game_session_logic.manager.broadcast(f"Un Jugador se ha desconectado")
    
    
