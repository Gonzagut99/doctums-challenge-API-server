from fastapi import APIRouter, status
from app.models.GameSessionModel import GameSessionCreate
from app.services.GameSessionService import GameSessionService

http_router = APIRouter(prefix="/api")

@http_router.post("/games/register", status_code=status.HTTP_201_CREATED)
async def register_game_session():
    # Create and save the new game session
    new_game = GameSessionService().add_game_session(GameSessionCreate())

    
    return {
        "message": "Game session registered successfully",
        "game_id": new_game.id,
    }
