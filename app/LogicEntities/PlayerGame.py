from typing import List
from app.LogicEntities.Context import Context
from app.LogicEntities.Modifiers import Project, Resource
from app.LogicEntities.Player import Player
from app.main import context

#Only controls the game logic when is the player's turn
class PlayerGame():
    def __init__(self, player:Player):
        self.context:Context = context
        self.player:Player = player
        self.event_manager:EventManager = EventManager()
        self.time_manager:TimeManager = TimeManager(self.player)
        
    def launch_cell_event(self):
        self.event_manager.launch_event("game_event", self.context)
    
    def launch_new_month_actions(self):
        if self.time_manager.is_new_month():
            self.time_manager.start_new_month()
            self.player.pay_salaries()
            self.player.get_products_from_projects(self.time_manager.finished_projects, self.time_manager.current_month)
            self.player.get_products_from_resources(self.time_manager.finished_resources, self.time_manager.current_month)
            self.player.update_products_thriving_state()
            

class EventManager:
    def __init__(self) -> None:
        self.events = {}
        

class TimeManager:
    def __init__(self, player:Player) -> None:
        self.player = player
        self.current_day = 0
        self.old_month = 0
        self.first_turn_in_month = True
        self.max_running_projects = 3
    
    @property
    def current_month(self):
        return (self.current_day // 30) + 1
    
    @property
    def running_projects(self): 
        return [key for key, value in self.player.projects.items() if not value.is_finished(self.current_month)]
    
    @property
    def finished_projects(self) -> List[Project]: 
        return [value for key, value in self.player.projects.items() if value.is_finished(self.current_month)]
    
    @property
    def finished_resources(self) -> List[Resource]: 
        return [value for key, value in self.player.resources.items() if value.is_finished(self.current_month)]

    def advance_day(self, days: int):
        """Advance the current day by a given number of days."""
        self.current_day += days
        
    def is_new_month(self):
        self.first_turn_in_month = self.current_month > self.old_month
        return self.first_turn_in_month
        
    def start_new_month(self):
        self.old_month += 1