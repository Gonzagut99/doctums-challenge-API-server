import datetime
from sqlmodel import Field, Relationship, SQLModel

from app.utils.uuid import generate_uuid4

class GameSessionModelBase(SQLModel):
    #name: str | None = Field(min_length=10, max_length=50, default=None)
    created_at: datetime.datetime | None = Field(default=datetime.datetime.now)
    updated_at: datetime.datetime | None = Field(default=datetime.datetime.now)
    
class GameSessionModel(GameSessionModelBase, table=True):
    id: str = Field(default=generate_uuid4(), primary_key=True)
    players: list["PlayerModel"]|None = Relationship(back_populates="game_session") # type: ignore
    
class GameSessionCreate(GameSessionModelBase):
    pass
    