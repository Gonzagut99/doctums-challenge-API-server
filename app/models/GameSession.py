import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel
# from app.models.Player import PlayerModel
from app.utils.uuid import generate_uuid4

if TYPE_CHECKING:
    from app.models.Player import PlayerModel

class GameSessionModelBase(SQLModel):
    created_at: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.now)

class GameSessionModel(GameSessionModelBase, table=True):
    __tablename__ = "gamesessions"
    id: str = Field(default_factory=generate_uuid4, primary_key=True)
    
    players: list["PlayerModel"] = Relationship(back_populates="game_session", sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"})
    
    # __config__ = {
    #     "orm_mode": True,
    #     "allow_population_by_field_name": True
    # }

class GameSessionCreate(GameSessionModelBase):
    pass