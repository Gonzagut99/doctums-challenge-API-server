from fastapi import APIRouter, Path, status, HTTPException
from app.models.GameSession import GameSessionCreate, GameSessionModel
from app.routers.http.ResponseModel import ResponseModel
from app.services.GameSessionService import GameSessionService
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.utils.error_handlers import handle_404exception

game_http_router = APIRouter(prefix="/api/game")
service = GameSessionService()

@game_http_router.post("/create", status_code=status.HTTP_201_CREATED, tags=["game"], response_model=GameSessionModel)
async def create_game_session()-> JSONResponse:
    # Create and save the new game session
    new_game = service.add_game_session(GameSessionCreate())
    players = new_game.players
    new_game = new_game.model_dump()
    new_game["players"] = players
    
    return JSONResponse(
        content=ResponseModel(
            message="Game session created successfully",
            data=jsonable_encoder(new_game),
            code=status.HTTP_201_CREATED,
        ).get_serialized_response(),
        status_code=status.HTTP_201_CREATED
    )

@game_http_router.get("/all", status_code=status.HTTP_200_OK, tags=["game"], response_model=list[GameSessionModel])
async def get_game_sessions():
    games = service.get_game_sessions()
    players = []
    for game in games:
        players.append(game.players)
    games = [game.model_dump() for game in games]
    games = [{**game, 'players': players[i]} for i, game in enumerate(games)]
    return JSONResponse(
        content=ResponseModel(
            message="Game sessions retrieved successfully",
            data=jsonable_encoder(games),
            code=status.HTTP_200_OK,
        ).get_serialized_response(),
        status_code=status.HTTP_200_OK
    )

@game_http_router.get("/{id}", status_code=status.HTTP_200_OK, tags=["game"], response_model=GameSessionModel)
async def get_game_session(id:str = Path(min_length=36, max_length=36)):
    game = service.get_game_session(id)
    if not game:
        return handle_404exception(HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found"))
    players = game.players
    game = game.model_dump()
    game["players"] = players
    return JSONResponse(
        content=ResponseModel(
            message="Game session retrieved successfully",
            data=jsonable_encoder(game),
            code=status.HTTP_200_OK,
        ).get_serialized_response(),
        status_code=status.HTTP_200_OK
    )
    
@game_http_router.delete("/{id}", status_code=status.HTTP_200_OK, tags=["game"], response_model=GameSessionModel)
async def delete_game_session(id:str = Path(min_length=36, max_length=36)):
    game = service.delete_game_session(id)
    if not game:
        return handle_404exception(HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found"))
    return JSONResponse(
        content=ResponseModel(
            message="Game session deleted successfully",
            data=jsonable_encoder(game),
            code=status.HTTP_200_OK,
        ).get_serialized_response(),
        status_code=status.HTTP_200_OK
    )




