from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.LogicEntities.Player import Player
from app.services.PlayerService import PlayerService
from app.services.GameSessionService import GameSessionService
from app.main import manager, context

ws_router = APIRouter(prefix="/ws")

@ws_router.websocket("/game/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    if not game_id:
        await websocket.close()
    #Se comienza la sesion del juego
    game = GameSessionService().get_game_session(game_id)
    
    if not game:
        await websocket.close()     
    
    player_id = await websocket.receive_text()
    print(f"Player id: {player_id}")
        
    if not player_id:
        await websocket.close()
    
    await manager.add_connection(websocket) #Internamente ya hace el accept
        
    #El jugador ya se creo por aparte
    db_player = PlayerService().get_player(player_id)
    player = Player(context=context, name=db_player.name, id=db_player.id)
        
    #
    game_session_logic = GameSessionService().get_session_logic(game_id)
    game_session_logic.add_player(player)
        
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Nuevo jugador conectado: {data}")
    except WebSocketDisconnect:
        manager.remove_connection(websocket)
        await manager.broadcast(f"Jugador {data} desconectado")
    
    
        