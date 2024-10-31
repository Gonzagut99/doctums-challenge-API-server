from typing import Sequence
from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from fastapi.responses import JSONResponse
from app.models.Player import PlayerModel, PlayerCreate, PlayerUpdate
from app.routers.http.ResponseModel import ResponseModel
from app.services.PlayerService import PlayerService
from fastapi.encoders import jsonable_encoder

from app.utils.error_handlers import handle_404exception

player_http_router = APIRouter(prefix="/api/player")

service = PlayerService()

@player_http_router.get("/all", response_model=Sequence[PlayerModel], tags=["players"], status_code=status.HTTP_200_OK)
def get_players() -> JSONResponse:
    players = service.get_players()
    games = []
    for player in players:
        games.append(player.game_session)
    players = [player.model_dump() for player in players]
    players = [{**player, 'games_session': games[i]} for i, player in enumerate(players)]
    
    return JSONResponse(
        content=ResponseModel(
            message="Players retrieved successfully",
            data=jsonable_encoder(players),
            code=status.HTTP_200_OK,
        ).get_serialized_response(),
        status_code=status.HTTP_200_OK
    )


@player_http_router.post("/create", response_model=PlayerModel, tags=["players"], status_code=status.HTTP_201_CREATED)
def add_player(
    response:Response,
    player:PlayerCreate
) -> JSONResponse:
    new_player = service.add_player(player)
    game = new_player.game_session
    new_player = new_player.model_dump()
    new_player["games_session"] = game
    response.set_cookie(key="player_id", value=new_player["id"])
    return JSONResponse(
        content=ResponseModel(
            message="Player created successfully",
            data=jsonable_encoder(new_player),
            code=status.HTTP_201_CREATED,
        ).get_serialized_response(),
        status_code=status.HTTP_201_CREATED
    )

@player_http_router.get("/{id}", response_model=PlayerModel, tags=["players"], status_code=status.HTTP_200_OK)
def read_item(
    id: str = Path(min_length=36, max_length=36),
) -> JSONResponse:
    player = service.get_player(id)
    if not player: 
        return handle_404exception(HTTPException(status_code=404, detail="Player not found"))
    game = player.game_session
    player = player.model_dump()
    player["games_session"] = game
    return JSONResponse(
        content=ResponseModel(
            message="Player retrieved successfully",
            data=jsonable_encoder(player),
            code=status.HTTP_200_OK,
        ).get_serialized_response(),
        status_code=status.HTTP_200_OK
    )
    
@player_http_router.put("/{id}", response_model=PlayerModel, tags=["players"], status_code=status.HTTP_200_OK)
def update_item(
    player: PlayerUpdate,
    id: str = Path(min_length=36, max_length=36)
) -> JSONResponse:
    player = service.update_player(id, player)
    if not player:
        return handle_404exception(HTTPException(status_code=404, detail="Player not found"))
    game = player.game_session
    player = player.model_dump()
    player["games_session"] = game
    return JSONResponse(
        content=ResponseModel(
            message="Player updated successfully",
            data=jsonable_encoder(player),
            code=status.HTTP_200_OK,
        ).get_serialized_response(),
        status_code=status.HTTP_200_OK
    )

@player_http_router.delete("/{id}", response_model=PlayerModel, tags=["players"], status_code=status.HTTP_200_OK)
def delete_item(
    id: str = Path(min_length=36, max_length=36),
) -> JSONResponse:
    player = service.delete_player(id)
    if not player:
        return handle_404exception(HTTPException(status_code=404, detail="Player not found"))
    return JSONResponse(
        content=ResponseModel(
            message="Player deleted successfully",
            data=jsonable_encoder(player),
            code=status.HTTP_200_OK,
        ).get_serialized_response(),
        status_code=status.HTTP_200_OK
    )