from typing import List
from app.LogicEntities.Context import Context
from app.LogicEntities.Modifiers import Resource
from app.LogicEntities.Player import Player
from app.main import context

#Only controls the game logic when is the player's turn
class PlayerGame():
    def __init__(self, player:Player):
        self.context:Context = context
        self.player:Player = player
        self.event_manager:EventManager = EventManager()
        self.time_manager:TimeManager = TimeManager(self.player)
        self.old_month:int = 0 
        
      
    def launch_cell_event(self):
        self.event_manager.launch_event("game_event", self.context)
    
    def launch_new_month_actions(self):
        if self.time_manager.is_new_month():
            self.time_manager.start_new_month()
            self.player.pay_salaries()
            self.player.get_products_from_modifiers()
            #TODO: launch products update thriving states
            

class EventManager:
    def __init__(self) -> None:
        self.events = {}
        

class TimeManager:
    def __init__(self, player:Player) -> None:
        self.player = player
        self.current_month = 0
        self.first_turn_in_month = True
        
    def is_new_month(self):
        self.first_turn_in_month = self.player.month > self.current_month
        return self.first_turn_in_month
    
        
    def start_new_month(self):
        self.current_month += 1