
import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field,Relationship, SQLModel

from app.utils.uuid import generate_uuid4


class PlayerModelBase(SQLModel):
    name: Optional[str] = Field(min_length=10, max_length=50, default=None)
    score: Optional[int]  = Field(default=0)
    remaining_budget: int  = Field(default=0)
    created_at: Optional[datetime.datetime] = Field(default=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = Field(default=datetime.datetime.now)
    game_session_id: str = Field(default=None, foreign_key="gamesessionmodel.id") 

class PlayerModel(PlayerModelBase, table=True):
    id: str = Field(default=generate_uuid4(), primary_key=True)
    game_session:  Optional["GameSessionModel"]  = Relationship(back_populates="players") # type: ignore 

class PlayerCreate(PlayerModelBase):
    pass
