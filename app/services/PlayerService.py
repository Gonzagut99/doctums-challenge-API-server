from sqlmodel import Session, select
from app.config.database import engine
from app.models.PlayerModel import PlayerModel, PlayerCreate

class PlayerService:
    def __init__(self):
        self.db = engine
        
    def get_players(self):
        with Session(self.db) as session:
            players = session.exec(select(PlayerModel)).all()
            return players

    def get_player(self, player_id)-> PlayerModel | None:
        with Session(self.db) as session:
            player = session.get(PlayerModel, player_id)
            if not player:
                return None
            return player
    
    def add_player(self, player:PlayerCreate) -> PlayerModel:
        with Session(self.db) as session:
            db_player = PlayerModel.model_validate(player)
            session.add(db_player)
            session.commit()
            session.refresh(db_player)
            return db_player

    def delete_player(self, player_id: str):
        with Session(self.db) as session:
            player = session.get(PlayerModel, player_id)
            session.delete(player)
            session.commit()
            return player