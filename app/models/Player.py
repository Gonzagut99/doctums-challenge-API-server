
import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field,Relationship, SQLModel
from app.utils.uuid import generate_uuid4

if TYPE_CHECKING:
    from app.models.GameSession import GameSessionModel

class PlayerModelBase(SQLModel):
    name: Optional[str] = Field(min_length=3, max_length=50, default=None)
    avatar_id: Optional[int] =  Field(default=1)
    score: Optional[int]  = Field(default=0)
    remaining_budget: Optional[int]  = Field(default=0)
    created_at: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.now)
    game_session_id: Optional[str] = Field(default=None, min_length=36, max_length=36, foreign_key="gamesessions.id") 

class PlayerModel(PlayerModelBase, table=True):
    __tablename__ = "players"
    id: Optional[str] = Field(default_factory=generate_uuid4, primary_key=True)
    
    game_session: "GameSessionModel" = Relationship(back_populates="players", sa_relationship_kwargs=dict(lazy="selectin"))
    
    # model_config = {
    #     "orm_mode": True,
    #     "allow_population_by_field_name": True
    # }

class PlayerCreate(PlayerModelBase):
    pass

class PlayerUpdate(PlayerModelBase):
    pass