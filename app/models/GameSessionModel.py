import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from app.utils.uuid import generate_uuid4

class GameSessionModelBase(SQLModel):
    created_at: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.now)

class GameSessionModel(GameSessionModelBase, table=True):
    id: str = Field(default_factory=generate_uuid4, primary_key=True)
    players: List["PlayerModel"] = Relationship(back_populates="game_session")  # type: ignore

class GameSessionCreate(GameSessionModelBase):
    pass