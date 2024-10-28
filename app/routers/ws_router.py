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
    
    await manager.add_connection(websocket) #Internamente ya hace el accept
    
    try:
        while True:
            player_id = await websocket.receive_text()
            print(f"Player id: {player_id}")
                
            if not player_id:
                await websocket.close()
                
            #El jugador ya se creo por aparte
            db_player = PlayerService().get_player(player_id)
            player = Player(context=context, name=db_player.name, id=db_player.id)
                
            game_session_logic = GameSessionService().get_session_logic(game_id)
            
            if not game_session_logic:
                new_game_session_logic_created = GameSessionService().generate_new_game_session_logic(game_id, game_context=context)
                if not new_game_session_logic_created:
                    raise Exception("Failed to create new game session logic")
                new_game_session_logic = GameSessionService().get_session_logic(game_id)
                new_game_session_logic.add_player(player)
            else:
                game_session_logic.add_player(player)
                
            await manager.broadcast(f"Jugador {player.name} conectado")
   
    except WebSocketDisconnect:
        manager.remove_connection(websocket)
        await manager.broadcast(f"Jugador {player.name} desconectado")
    
    
        