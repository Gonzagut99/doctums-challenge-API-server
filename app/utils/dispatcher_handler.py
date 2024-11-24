import json
from typing import Dict, Callable, Awaitable
from fastapi import WebSocket


from app.LogicEntities.Context import Context
from app.LogicEntities.Game import GameLogic
from app.LogicEntities.Player import Player
from app.services.PlayerService import PlayerService

class Dispatcher:
    def __init__(self, session: GameLogic, context: Context):
        self.manager = session.manager
        self.context = context
        self.session = session
        self.player = None
        
        self.player_service = PlayerService()
        self.handlers: Dict[str, Callable] = {
            "join": self.handle_join,
            "start_game": self.handle_start_game,
            "turn_order_stage": self.handler_turn_order,
            "start_new_turn": self.handle_player_new_turn,
            "advance_days": self.notify_player_advanced_days,
            #"update_players_positions": self.handle_updated_players_positions,
            "submit_plan": self.handle_submit_plan,
            "turn_event_flow": self.handle_turn_event_flow,
            "next_turn": self.handle_next_turn,
            "ping": self.handle_ping,
            # Add more handlers as needed
        }
    
    async def dispatch(self, game_id: str, websocket: WebSocket, message: dict):
        method = message.get("method")
        handler = self.handlers.get(method)
        
        if handler:
            await handler(game_id, websocket, message)
        else:
            await websocket.send_json({"status": "error", "message": f"Unknown method: {method}"})
    
    async def notify_all_players(self, message: str, exclude_player: Player = None, actual_stage: str = None):
        players_games = self.session.playersgames
        for player_game in players_games:
            if exclude_player and player_game.player == exclude_player:
                continue
            
            await self.manager.send_personal_json({
                "method": "notification",
                "status": "success",
                "message": message,
                actual_stage: True
            }, player_game.player_connection)
    
    async def notify_player_advanced_days(self, game_id: str, websocket: WebSocket, message: dict):
        days = self.session.get_playergame(self.player).current_dice_result
        await self.manager.send_personal_json({
            "method": "days_advanced",
            "status": "success",
            "message": f"Has avanzado {days} días!",
            "has_player_rolled_dices": True
        }, websocket)
        await self.notify_players_positions()
    
    async def notify_players_positions(self):
        players_games = self.session.playersgames
        players_position =  [{
            "playerId": player.player.id,
            "avatarId": player.player.avatar_id,
            "currentDay": player.time_manager.current_day
        } for player in players_games]
        
        days = self.session.get_playergame(self.player).time_manager.current_day
        for player_game in players_games:
            response = {
                "method": "updated_players_positions",
                "status": "success",
                "messgae": f"{self.player.name} ha avanzado {days}",
                "players_position": players_position
            }
            await self.manager.send_personal_json(response, player_game.player_connection)
    
    async def handle_ping(self, game_id: str, websocket: WebSocket, message: dict):
        await websocket.send_json({"method": "keep_alive" ,"status": "success"})

    async def handle_join(self, game_id: str, websocket: WebSocket, message: dict):
        player_id = message.get("player_id")

        if self.player is None:
          db_player = self.player_service.get_player(player_id)
          #Validate if the player belongs to the game session
          if db_player.game_session_id != game_id:
              
              await websocket.send_json({"status": "error", "message": "El jugador no pertenece a la sesión de juego"})
              await websocket.close()
              return
          self.player = Player(context=self.context, name=db_player.name, id=db_player.id, avatar_id=db_player.avatar_id, connection=websocket)
          
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
    
    # 1st stage    
    async def handle_start_game(self, game_id: str, websocket: WebSocket, message: dict):
        if not self.player.is_host:
          await self.manager.send_personal_json({"status": "error", "message": "Only the host can start the game"}, websocket)
          return
        self.session.start_game() #First states settled
        # if self.session.turn_manager.get_current_player() is None:
        #     raise Exception("No current player has been set yet")
        # self.session.turn_manager.launch_first_turn_begin_actions()
        
        #connected_players = self.session.get_players()
        players_games = self.session.playersgames
        # turn_order = self.session.turn_manager.get_turn_order_list()
        current_player = self.session.turn_manager.get_random_player_id_who_hasnt_rolled_dices()
        # Initialize game for all players
        for player_game in players_games:
            response = {
                "method": "start_game",
                "status": "success",
                "message": "¡El juego ha comenzado!",
                "current_turn": current_player,
                "legacy_products": player_game.player.get_products(),
                "player": {
                    "id": player_game.player.id,
                    "name": player_game.player.name,
                    "avatarId": player_game.player.avatar_id,
                    "budget": player_game.player.budget,
                    "score": player_game.player.score,
                    "efficiencies": player_game.player.get_efficiencies(),
                    #"is_first_turn": player_game.time_manager.first_turn_in_month
                    
                },
                "turns_order": [],
                "is_start_game_stage": True
                
            }
            await self.manager.send_personal_json(response, player_game.player_connection)
    
    #2nd stage    
    async def handler_turn_order(self, game_id: str, websocket: WebSocket, message: dict):
        
        self.session.turn_manager.player_rolled_dices(self.player.id)
        
        players_games = self.session.playersgames
        turn_order = self.session.turn_manager.get_turn_order_list()
        first_player_turn = self.session.turn_manager.get_current_player()
        current_player_to_roll = self.session.turn_manager.get_random_player_id_who_hasnt_rolled_dices()
        current_player = self.player
        current_player_turn_results = current_player.turn
        
        
        for player_game in players_games:
            response = {
                "method": "turn_order_stage",
                "status": "success",
                "current_turn": current_player_to_roll,
                "first_player_turn": first_player_turn,
                "message": f"{current_player.name} ha sacado un {current_player_turn_results['total']}" if current_player_to_roll is not None else "Orden Definido!",
                "this_player_turn_results": player_game.player.turn,
                "turns_order": turn_order,
                "is_turn_order_stage": True,
                "is_turn_order_stage_over": self.session.turn_manager.is_turn_order_stage_over()
            }
            await self.manager.send_personal_json(response, player_game.player_connection)
        
    # async def handle_player_first_turn(self, game_id: str, websocket: WebSocket, message: dict):
    #     if self.session.turn_manager.get_current_player() is None:
    #         raise Exception("No current player has been set yet")
    #     self.session.turn_manager.launch_first_turn_begin_actions()
    #     #connected_players = self.session.get_players()
    #     current_player = self.session.turn_manager.get_current_player()

        
    # 1st game step - 3er stage
    async def handle_player_new_turn(self, game_id: str, websocket: WebSocket, message: dict):
        if self.session.turn_manager.get_current_player() is None:
            raise Exception("No current player has been set yet")
        
        #connected_players = self.session.get_players()
        current_player = self.session.turn_manager.get_current_player()
        is_players_turn = current_player is self.player.id
        response:dict
        
        if is_players_turn:
            self.session.turn_manager.proceed_with_new_turn_in_journey(self.session.playersgames)
            playergame = self.session.get_playergame(self.player)
            current_day = playergame.time_manager.current_day
            response = {
                "method": "new_turn_start",
                "status": "success",
                "message": "Avanza en el tablero!", 
                "current_turn": current_player,
                "thrown_dices": playergame.current_dice_roll ,
                "days_advanced": playergame.current_dice_result,
                "time_manager": {
                    "current_day": current_day,
                    "current_day_in_month": playergame.time_manager.current_day_in_month,
                    "current_month": playergame.time_manager.current_month,
                    "is_weekend": playergame.time_manager.is_weekend(),
                    "is_first_turn_in_month": playergame.time_manager.first_turn_in_month,
                    "is_journey_finished": playergame.is_journey_finished(),
                    "is_game_over": playergame.is_game_over(),
                },
                "player": {
                    "id": self.player.id,
                    "products": playergame.get_products_state(),
                    "projects": playergame.get_projects_state(),
                    "resources": playergame.get_resources_state(),
                },
                "is_new_turn_stage": True,
                "is_ready_to_face_event": False if playergame.time_manager.first_turn_in_month or playergame.time_manager.is_weekend() else True
            }
            
            await self.notify_all_players(f"!Turno de {self.player.name}!", exclude_player=self.player, actual_stage="is_new_turn_stage")
            
            
        else:
            response = {
                "method": "player_first_turn",
                "status": "success",
                "message": "Todavia no es tu turno",
                "current_turn": current_player,
            }
        await self.manager.send_personal_json(response, websocket)
        
    #1.5 game step - 3er stage
    # async def handle_updated_players_positions(self, game_id: str, websocket: WebSocket, message: dict):
    #     players_game_sessions = [self.session.get_playergame(player) for player in self.session.get_players()]
    #     players_position =  [{
    #         "playerId": player.player.id,
    #         "avatarId": player.player.avatar_id,
    #         "currentDay": player.time_manager.current_day
    #     } for player in players_game_sessions]
    #     response = {
    #         "method": "updated_players_positions",
    #         "status": "success",
    #         "players_position": players_position
    #     }
    #     await self.manager.broadcast(json.dumps(response))
        
    #2nd step - 4th stage
    async def handle_submit_plan(self, game_id: str, websocket: WebSocket, message: dict):
        actions = message.get("actions")
        #"actions": {
        #     "products": ["10", "11"],
        #     "projects": [],
        #     "resources": []
        # }
        # Process action plan submission
        playergame = self.session.get_playergame(self.player)
        playergame.submit_plan(actions)
        playergame.update_player_products_thriving_state()   
        current_player = self.session.turn_manager.get_current_player()     
        
        response = {
            "method": "submit_plan",
            "status": "success",
            "message": "!Plan de acción enviado! Continuemos con el evento.",
            "current_turn": current_player,
            "bought_modifiers": self.player.get_recently_bought_modifiers(),
            "player": {
                "budget": self.player.budget,
                "products": playergame.get_products_state(),
                "projects": playergame.get_projects_state(),
                "resources": playergame.get_resources_state(),
            },
            "show_modal": True,
            "is_ready_to_face_event": True
        }
        await self.manager.send_personal_json(response, websocket)        
    
    # 3rd step
    async def handle_turn_event_flow(self, game_id: str, websocket: WebSocket, message: dict):
        # Process turn manager
        # Debe de ser llamado cuando el jugador jugara su turno (avanzara dias y manejara su evento)
        # al terminar de jugar su turno acabara y se pasara al siguiente jugador
        # este debe de indicarle al jugador la cantidad de dias que avanzo asi como los dados que ha lanzado
        # que recompensas obtuvo y que eventos ocurrieron 
        # este le estara indicando al jugador los resultados y desarrollo del evento de manera que esten precargados en el cliente
        # se debe terminar el turno del jugador
                
        current_player = self.session.turn_manager.get_current_player()
        is_players_turn = current_player is self.player.id
        response:dict
        if is_players_turn:
            self.session.turn_manager.proceed_with_raimining_turn_actions(self.session.playersgames)
            playergame = self.session.get_playergame(self.player)
            response = {
                "method": "turn_event_flow",
                "status": "success",
                "message": f"¡Has caido en un evento de nivel {playergame.event_manager.event_level}!",
                # "thrown_dices": [4, 3],
                # "days_advanced": 7,
                "current_turn": current_player,
                "event": {
                    "id": playergame.event_manager.event.ID,
                    "level": playergame.event_manager.event_level,
                    "efficiency_chosen":  playergame.event_manager.chosen_efficiency.ID,
                    "pass_first_challenge": playergame.event_manager.has_passed_1st_challenge,
                    "risk_challenge_dices": playergame.event_manager.risk_challenge_dices,
                    "risk_points": playergame.event_manager.risk_points,
                    "pass_second_challenge": playergame.event_manager.has_passed_2nd_challenge,
                    "rewards": {
                        "budget": playergame.event_manager.obtained_budget,
                        "score": playergame.event_manager.obtained_score,
                        "obtained_efficiencies_points": playergame.event_manager.obtained_efficiencies_points,
                    }
                },
                "player": {
                    "score": self.player.score,
                    "budget": self.player.budget,
                    #"resources": self.player.get_resources_state(),
                    #"projects": self.player.get_projects_state(),
                    #"current_day": self.session.time_manager.current_day,
                    "effiencies": self.player.get_efficiencies(),
                    #"has_player_got_broke": False
                },
                "show_event": True,
                "is_ready_to_set_next_turn": True
            }
            
            await self.manager.send_personal_json(response, websocket)
        else:
            response = {
                "method": "turn_event_manager",
                "status": "success",
                "message": "Todavia no es tu turno",
                "current_turn": current_player,
            }
        
    #4th step
    async def handle_next_turn(self, game_id: str, websocket: WebSocket, message: dict):
        # en el metodo turn_event_manager ya estamos culminando lo que es el turno del jugador
        # nosotros deberemos de recibir otra peticion desde el cliente que sera cuando el jugador ya alla terminando su evento 
        # el cual sera por un metodo "next turn" 
        # aqui solo manejaremos una notifcacion broadcast para que los demas jugadores sepan que el turno del jugador ha terminado y quien de que jugador es el siguiente turno
        # el cliente al recibir esta notificacion debera de cambiar el estado de su interfaz para que el jugador pueda jugar su turno
        # asi como bloquear la interfaz de los demas jugadores para que no puedan jugar
        
        # que este metodo solo se enfoque en notificar a los demas jugadores que el turno del jugador ha terminado y que jugador sigue
        # AQUI ES DONDE COMENZARA EL TURNO DEL NUEVO JUGADOR
        # AQUI ES DONDE DEBEREMOS DE REALIZAR LAS ACCIONES DE INICIO DE MES SI ES QUE CORRESPONDE
        # AQUI PODEMOS CARGAR LOS DIAS INTERNAMENTE PARA VALIDAR SI ES QUE EL JUGADOR YA HA PASADO LOS 360 DIAS
        
        players_games = self.session.playersgames
        self.session.turn_manager.advance_turn()
        if self.session.turn_manager.last_turn is not self.session.turn_manager.current_turn_index:
            current_player = self.session.turn_manager.get_current_player()
            for player_game in players_games:
                response = {
                    "method": "next_turn",
                    "status": "success",
                    "message": "¡Un nuevo turno ha comenzado!",
                    "current_turn": current_player,
                    "player": {
                        "is_first_turn": player_game.time_manager.first_turn_in_month,
                        "current_month": player_game.time_manager.current_month,
                    }
                    
                }
                await self.manager.send_personal_json(response, player_game.player_connection)
    
    
        # else:
        #     for player_game in players_games:
        #         response = {
        #             "method": "game_over",
        #             "status": "success",
        #             "message": "¡El juego ha terminado!",
        #             "player": {
        #                 "id": player_game.player.id,
        #                 "score": player_game.player.score,
        #                 "budget": player_game.player.budget,
        #                 "products": player_game.player.get_products_state(),
        #                 "projects": player_game.player.get_projects_state(),
        #                 "resources": player_game.player.get_resources_state(),
        #                 "effiencies": player_game.player.get_efficiencies(),
        #                 "has_player_got_broke": False
        #             }
        #         }
        #         await self.manager.send_personal_json(response, player_game.player_connection)
        
    

    # async def handle_roll_dice(self, game_id: str, websocket: WebSocket, message: dict):
    #     player_id = message.get("playerId")
    #     # Simulate dice roll and movement
    #     dice_result = [4, 3]  # Example roll result
    #     total_advance = sum(dice_result)
    #     response = {
    #         "method": "dice_result",
    #         "playerId": player_id,
    #         "dice": dice_result,
    #         "totalAdvance": total_advance,
    #         "message": f"Player {player_id} rolled the dice and advanced {total_advance} days."
    #     }
    #     await self.manager.broadcast(game_id, response)

