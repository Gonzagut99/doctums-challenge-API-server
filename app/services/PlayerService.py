from typing import Sequence
from fastapi.exceptions import ResponseValidationError
from pydantic import ValidationError
from sqlmodel import Session, select
from app.config.database import engine
from app.models.Player import PlayerModel, PlayerCreate, PlayerUpdate

class PlayerService:
    def __init__(self):
        self.db = engine
        
    def get_players(self) -> Sequence[PlayerModel]:
        with Session(self.db) as session:
            players = session.exec(select(PlayerModel)).all()
            return players

    def get_player(self, player_id:str)-> PlayerModel | None:
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
    
    def update_player(self, player_id: str, player: PlayerUpdate) -> PlayerModel | None:
        with Session(self.db) as session:
            update_data = PlayerModel.model_validate(player)
            db_player = session.get(PlayerModel, player_id)
            if not db_player:
                return None
            update_data = player.model_dump()
            
            for key, value in update_data.items():
                setattr(db_player, key, value)
            session.add(db_player)
            session.commit()
            session.refresh(db_player)
            return db_player

    def delete_player(self, player_id: str) -> PlayerModel | None:
        with Session(self.db) as session:
            player = session.get(PlayerModel, player_id)
            if not player:
                return None
            session.delete(player)
            session.commit()
            return player