from app.LogicEntities.GameSession import GameSession

class GameSessionLogicContext:
    def __init__(self):
        self.sessions:list[GameSession] = []
        