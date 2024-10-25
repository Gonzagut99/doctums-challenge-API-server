from sqlmodel import Session, select
from app.LogicEntities.GameSession import GameSessionLogic
from app.config.database import engine
from app.models.GameSessionModel import GameSessionModel, GameSessionCreate
from app.main import gameSessions

class GameSessionService:
    def __init__(self):
        self.db = engine
        
    def get_game_session(self, game_id: str) -> GameSessionModel:
        with Session(self.db) as session:
            game = session.get(GameSessionModel, game_id)
            return game

    def get_game_sessions(self) -> list[GameSessionModel]:
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
    
    def generate_new_game_session_logic(self, game_id:str) -> bool:
        game = self.get_game_session(game_id)
        if not game:
            return None
        new_game = GameSessionLogic()
        gameSessions.append(new_game)
        if new_game not in gameSessions:
            return False
        return True
    
    def get_session_logic(self, game_id:str) -> GameSessionLogic:
        for game in gameSessions:
            if game.game.id == game_id:
                return game
        return None
    
    def delete_game_session(self, game_id: str) -> bool:
        with Session(self.db) as session:
            game = session.get(GameSessionModel, game_id)
            session.delete(game)
            session.commit()
            return 
    
    def delete_game_session_logic(self, game_id:str) -> bool:
        for game in gameSessions:
            if game.game.id == game_id:
                gameSessions.remove(game)
                return True
        return False
    
    # def delete_player(self, game_id: str) -> bool:
    #     with Session(self.db) as session:
    #         game = session.get(GameSessionModel, game_id)
    #         game.players
    #         session.delete(game)
    #         session.commit()
    #         return game
        