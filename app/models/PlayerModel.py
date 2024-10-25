
import datetime

from sqlmodel import Field, SQLModel

from app.utils.uuid import generate_uuid4

class PlayerModelBase(SQLModel):
    name: str | None = Field(min_length=10, max_length=50, default=None)
    score: int | None = Field(default=0)
    remaining_budget: int | None = Field(default=0)
    created_at: datetime.datetime | None = Field(default=datetime.datetime.now)
    updated_at: datetime.datetime | None = Field(default=datetime.datetime.now)
    game_session_id: str = Field(default=None, foreign_key="gameSessionModel.id") 

class PlayerModel(PlayerModelBase, table=True):
    id: str = Field(default=generate_uuid4(), primary_key=True)
    game_session: "GameSessionModel" | None = Field(default=None, back_populates="players") # type: ignore

class PlayerCreate(PlayerModelBase):
    pass
