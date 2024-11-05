from typing import Sequence
from sqlmodel import Session, select
from app.config.database import engine
from app.models.GameSession import GameSessionModel, GameSessionCreate
from app.LogicEntities.GameSession import GameSessionLogic
from app.LogicEntities.Game import GameLogic
from app.main import gameSessions

class GameSessionService:
    def __init__(self):
        self.db = engine
        self.gameSessions = gameSessions.sessions
        
    #HTTP methods
        
    def get_game_session(self, game_id: str) -> GameSessionModel | None:
        with Session(self.db) as session:
            game = session.get(GameSessionModel, game_id)
            if not game:
                return None
            return game

    def get_game_sessions(self) -> Sequence[GameSessionModel]:
        with Session(self.db) as session:
            games = session.exec(select(GameSessionModel)).all()
            return games

    def add_game_session(self, game: GameSessionCreate) -> GameSessionModel:
        with Session(self.db) as session:
            db_game = GameSessionModel.model_validate(game)
            session.add(db_game)
            session.commit()
            session.refresh(db_game) 
            return db_game
        
    def delete_game_session(self, game_id: str) -> GameSessionModel | None:
        with Session(self.db) as session:
            game = session.get(GameSessionModel, game_id)
            if not game:
                return None
            session.delete(game)
            session.commit()
            return game
        
    
    #Logic/Memory methods
    
    def generate_new_game_session_logic(self, game_id:str, game_context) -> bool:
        game = self.get_game_session(game_id)
        if not game:
            return None
        new_game = GameLogic(context=game_context, session_id=game_id)
        self.gameSessions.append(new_game)
        if new_game not in self.gameSessions:
            return False
        return True
    
    def get_session_logic(self, game_id:str) -> GameSessionLogic:
        game = next((game for game in self.gameSessions if game.session_id == game_id), None)
        return game
    
    def delete_game_session_logic(self, game_id:str) -> bool:
        for game in self.gameSessions:
            if game.session_id == game_id:
                self.gameSessions.remove(game)
                return True
        return False
    
    # def delete_player(self, game_id: str) -> bool:
    #     with Session(self.db) as session:
    #         game = session.get(GameSessionModel, game_id)
    #         game.players
    #         session.delete(game)
    #         session.commit()
    #         return game
        