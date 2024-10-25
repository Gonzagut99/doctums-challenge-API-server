from app.LogicEntities.GameSession import GameSessionLogic

class GameSessionLogicContext:
    def __init__(self):
        self.sessions:list[GameSessionLogic] = []
        