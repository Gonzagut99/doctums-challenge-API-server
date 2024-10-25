from app.LogicEntities.Context import Context
from app.LogicEntities.Player import Player
from app.main import context

#Only controls the game logic when is the player's turn
class PlayerGame():
    def __init__(self, player:Player):
        self.context:Context = context
        self.event_manager:EventManager = EventManager()
        self.time_manager:TimeManager = TimeManager()
      
    def launch_event(self):
        self.event_manager.launch_event("game_event", self.context)

class EventManager:
    def __init__(self) -> None:
        self.events = {}
        

class TimeManager:
    def __init__(self) -> None:
        self.current_month = 0
        
    def start_new_month(self):
        self.current_month += 1
        
    def start_new_month(self):
        self.time_manager.start_new_month()