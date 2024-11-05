from copy import deepcopy
from operator import itemgetter
import random
from typing import List

import numpy as np
from app.LogicEntities.Context import Context
from app.LogicEntities.Efficiency import Efficiency
from app.LogicEntities.Event import Event
from app.LogicEntities.Modifiers import Product, Project, Resource
from app.LogicEntities.Player import Player
from app.main import context

#Only controls the game logic when is the player's turn
class PlayerGame():
    def __init__(self, player:Player):
        self.journey_days_limit = 360
        self.journey_month_limit = 13
        self.journey_dices_number = 5
        self.current_dice_roll:list[int] = []
        self.current_dice_result:int = 0
        self.context:Context = context #TODO: GET CONTEXTO FROM GAME
        self.player:Player = player
        self.event_manager:EventManager = EventManager(self.player)
        self.time_manager:TimeManager = TimeManager(self.player)
        self.player_state:str|None = 'playing' #"broke", "playing", "finished"
        self.turn_state:str|None = 'end' #end, playing
    
    def is_player_turn(self):
        return self.turn_state == "playing"
        
    def load_player_data(self):
        self.player.get_legacy(self.time_manager.current_month)
        self.player.update_products_thriving_state()
    
    def start_game_journey(self):
        # random.seed(0)
        # np.random.seed(0)
        self.begin_turn()
        self.launch_new_journey_actions()
        # while not self.is_journey_finished() and self.player_state == "playing":
        #     self.turn_play()
    def submit_plan(self, actions:dict[str,list]):
        if self.turn_state == "playing":
            actual_month = self.time_manager.current_month
            if actions.get("products"):
                for product_id in actions.get("products"):
                    self.player.buy_product(product_id, actual_month)
            if actions.get("projects"):
                for project_id in actions.get("projects"):
                    self.player.buy_project(project_id, actual_month, actual_month + 1)
            if actions.get("resources"):
                for resource_id in actions.get("resources"):
                    self.player.hire_resource(resource_id, actual_month, actual_month)
        else:
            print("No puedes hacer acciones en este turno")
    
    def begin_turn(self):
        self.turn_state = "playing"
    
    def end_turn(self):
        self.turn_state = "end"
    
    def turn_play(self):
        self.proceed_journey()
        self.end_turn() 
    
    def launch_new_month_actions(self):
        if self.time_manager.is_new_month():
            self.time_manager.start_new_month()
            self.player.pay_salaries()
            self.event_manager.notify_payed_salaries()
            self.player.get_products_from_projects(self.time_manager.finished_projects, self.time_manager.current_month)
            self.player.get_products_from_resources(self.time_manager.finished_resources, self.time_manager.current_month)
            self.player.update_products_thriving_state()
            self.launch_buy_modifiers_actions()
            self.time_manager.first_turn_in_month = False
    
    def launch_new_journey_actions(self):
        if self.time_manager.is_new_month():
            self.time_manager.start_new_month()
            #self.launch_buy_modifiers_actions()
            self.time_manager.first_turn_in_month = False
            
    
    def sort_steps_to_advance(self):
        dices, steps = self.player.throw_dices(self.journey_dices_number)
        self.current_dice_roll = dices
        self.current_dice_result = steps
        self.time_manager.advance_day(steps)
        
    def proceed_journey(self)->None:
        self.sort_steps_to_advance()
        self.launch_new_month_actions()
        if not self.time_manager.is_weekend() and not self.is_journey_finished():
            self.time_manager.notify_current_day_in_month()
            self.time_manager.notify_current_day_of_week()
            self.launch_event_flow()
        if self.time_manager.is_weekend():
            self.time_manager.notify_current_day_in_month()
            self.time_manager.notify_current_day_of_week()
            self.time_manager.notify_weekend()
        if not self.is_journey_finished():
            self.event_manager.notify_event_end()
        if self.is_journey_finished():
            self.handle_finish_journey()

    def launch_event_flow(self):
        event_level = self.get_board_field_number()
        self.event_manager.set_event_level(event_level)
        self.event_manager.notify_event_level()
        event = self.event_manager.take_random_event(self.time_manager.current_trimester)
        self.event_manager.set_challenger_event(event)
        required_efficiencies = self.event_manager.get_required_efficiencies()
        self.event_manager.notify_required_own_eficiency_points()
        
        #Also sets the chosen_efficiency within the event_manager
        self.event_manager.choose_efficiency_by_max_strength_points(required_efficiencies)
        self.event_manager.notify_chosen_efficiency_data()
        
        #get modifiers that gather requirements to grant points
        current_enabled_modifiers:dict[str,list] = self.event_manager.enabled_modifiers()
        self.event_manager.notify_enabled_modifiers(current_enabled_modifiers)
        
        #get data to pass the event challenge
        possible_total_strength_points, possible_modifiers_points=self.event_manager.soft_possible_efficiency_strength_points_calculation(current_enabled_modifiers)
        
        #Event Challenge
        #Challenge Phase 1: Evaluate if won or loose challenge with the difference between efficiency points and the required points
        if not self.event_manager.pass_event_challenge_phase_1(possible_total_strength_points):
            dices, risk_points = self.event_manager.launch_failed_event_challenge_phase_1_actions()
            
            #Challenge Phase 2: Evaluate if won or loose challenge with the risk points
            if not self.event_manager.pass_event_challenge_phase_2(risk_points, possible_modifiers_points):
                self.event_manager.launch_failed_event_challenge_phase_2_actions()
            else:
                self.event_manager.launch_pass_event_challenge_phase_2_actions(current_enabled_modifiers)    
        else:
            self.event_manager.launch_pass_event_challenge_phase_1_actions()            
        
    def get_board_field_number(self)->int:
        board_context = self.context.board.reshape(-1)
        field = board_context[self.time_manager.current_day - 1]
        return field
    
    def is_journey_finished(self)->bool:
        if self.time_manager.journey_reached_end(self.journey_limit_days) or self.time_manager.check_month_limit():
            return True
        elif self.player_state == "broke":
            return True
        return False   
    
    def handle_finish_journey(self):
        if self.time_manager.journey_reached_end(self.journey_limit_days):
            self.player_state = "finished"
            self.finish_player_game()
        elif self.player_state == "broke":
            self.finish_player_game()
        else:
            self.player_state = "playing"

    def finish_player_game(self):
        if self.player_state == "finished":
            return print('Sobrevisviste el año, !Felicidades!')
        elif self.player_state == "broke":
            return print('Te quedaste sin dinero, !Has perdido!')
        else:
            return print('No has terminado el juego')
        
    def launch_buy_modifiers_actions(self):
        if self.player.first_turn_in_month:
            print("Estas en el primer turno del mes, puedes comprar productos, proyectos y recursos. ¿Quieres comprar algo?")
            wanna_buy = input("Si/No")
            wanna_buy = wanna_buy.lower() == "si"
            while wanna_buy:
                purchase = input("¿Que te gustaria comprar? (product, project, resource, nothing)")
                purchase = purchase.lower()
                if purchase == "nothing":
                    print(self.player.display_modifier(self.player.products.values(), "product"))
                    print(self.player.display_modifier(self.player.projects.values(), "project"))
                    print(self.player.display_modifier(self.player.resources.values(), "resource"))                
                    wanna_buy = False
                elif purchase == "product":
                    product_id = input("¿Que producto te gustaria comprar?")
                    # TODO make this dummy proof (only integers are allowed)
                    self.wanna_buy_product_actions(str(product_id))
                elif purchase == "project":
                    project_id = input("¿Que proyecto te gustaria comprar?")
                    self.wanna_buy_project_actions(str(project_id))
                elif purchase == "resource":
                    resource_id = input("¿Que recurso te gustaria comprar?")
                    self.wanna_buy_resource_actions(str(resource_id))
                else:
                    print("por favor, elige una opcion valida")
                    continue
        else:
            print("No estas en el primer turno del mes, no puedes comprar nada")
            
    def wanna_buy_nothing_actions(self):
        print(self.player.display_modifier(self.player.products.values(), "product"))
        print(self.player.display_modifier(self.player.projects.values(), "project"))
        print(self.player.display_modifier(self.player.resources.values(), "resource"))
    
    def wanna_buy_product_actions(self, product_id:str):
        self.player.buy_product(product_id)
        
    def wanna_buy_project_actions(self, project_id:str):
        self.player.buy_project(str(project_id))
    
    def wanna_buy_resource_actions(self, resource_id:str):
        self.player.hire_resource(str(resource_id))
            
            

class EventManager:
    def __init__(self, player:Player) -> None:
        self.player:Player | None = player
        self.event:Event | None = None
        self.chosen_efficiency:Efficiency | None = None
        self.event_level:int|None = None
        
    
    #Va a ir a efficiency
    @property        
    def enabled_modifiers(self, event:Event) -> dict[str,list]:
        enabled_products = [product for product in self.chosen_efficiency.get_enabled_products(list(self.player.products.values())) if product.ID in event.modifiable_products]
        enabled_projects = [project for project in self.chosen_efficiency.get_enabled_projects(list(self.player.projects.values()), self.player.month) if project.ID in event.modifiable_projects]
        enabled_resources = [resource for resource in self.chosen_efficiency.get_enabled_resources(list(self.player.resources.values())) if resource.ID in event.modifiable_resources]
        
        return {
            "enabled_products": enabled_products,
            "enabled_projects": enabled_projects,
            "enabled_resources": enabled_resources
        }    

    def take_random_event(self, current_trimester:int)->Event:
        possible_events = [
            event_id for event_id, event in context.EVENTS.items() if event.appear_first_in_trimester <= current_trimester
        ]
        random_event_id = random.choice(possible_events)
        event = deepcopy(context.EVENTS.get(random_event_id))
        return event   
    
    def set_event_level(self, event_level:int):
        self.event.level = event_level
        self.event_level = event_level
    
    def get_required_efficiencies(self)->list[Efficiency]:
        required_efficiencies_ids = self.event.required_efficiencies
        required_efficiencies = itemgetter(*required_efficiencies_ids)(self.player.efficiencies)
        return required_efficiencies
    
    def choose_efficiency_by_max_strength_points(self, required_efficiencies:List[Efficiency])->None:
        max_strength_points = max([efficiency.points for efficiency in required_efficiencies])
        chosen_efficiency = filter(lambda eff: eff.points == max_strength_points, required_efficiencies)
        chosen_efficiency = list(chosen_efficiency)[0]
        self.set_chosen_efficiency(chosen_efficiency)
    
    def possible_modifiers_points_granted(self, event:Event, enabled_modifiers:dict[str,list]):
        #Calculate possible points to grant
        enabled_products = enabled_modifiers['enabled_products']
        enabled_projects = enabled_modifiers['enabled_projects']
        enable_resources = enabled_modifiers['enabled_resources']
        product_points = sum([self.chosen_efficiency.points_by_event_level(product.points_to_grant,event.level,'product') for product in enabled_products])
        project_points = sum([self.chosen_efficiency.points_by_event_level(project.points_to_grant, event.level, 'project') for project in enabled_projects])
        resource_points = sum([self.chosen_efficiency.points_by_event_level(resource.points_to_grant, event.level, 'resource') for resource in enable_resources])
        return product_points, project_points, resource_points

    def possible_modifiers_points_sum_to_be_granted(self, modifiers_points:tuple[int,int,int])->int:
        return sum(modifiers_points)
    
    def possible_efficiency_points_to_be_granted(self, possible_modifiers_points:int, efficiency_strength_points:int)->int:
        possible_points = possible_modifiers_points+efficiency_strength_points
        return possible_points
        
    def soft_possible_efficiency_strength_points_calculation(self, current_enabled_modifiers:dict[str, list]):
        product_pts, project_pts, resources_pts = self.possible_modifiers_points_granted(self.event, current_enabled_modifiers)
        self.event_manager.notify_possible_modifiers_points_granted((product_pts, project_pts, resources_pts))
        possible_modifiers_points=self.possible_modifiers_points_sum_to_be_granted((product_pts, project_pts, resources_pts))
        possible_total_strength_points=self. possible_efficiency_points_to_be_granted(possible_modifiers_points, self.chosen_efficiency.points)
        self.notify_possible_points_to_be_granted(possible_total_strength_points)
        return possible_total_strength_points, possible_modifiers_points
    
    def pass_event_challenge_phase_1(self, possible_efficiency_strength_points:int):
        pass_challenge_with_points_difference = self.chosen_efficiency.check_enough_points_to_pass(self.event.level,possible_efficiency_strength_points)
        return pass_challenge_with_points_difference
    
    def launch_pass_event_challenge_phase_1_actions(self):
        self.notify_phase_1_challenge_success()
        self.player.apply_challenge_result(self.event.result_failure)
    
    def launch_failed_event_challenge_phase_1_actions(self):
        self.notify_phase_1_challenge_failed()
        dices, risk_points = self.player.throw_dices(self.event_level)
        self.notify_dice_roll_result(dices=dices, sum_number=risk_points)
        self.notify_dice_number_to_risk_points()
        return dices, risk_points
        
    def notify_risk_points(self, risk_points:int):
        return print(f"El numero de puntos de riesgo es {risk_points}")
        
    def notify_phase_1_challenge_failed(self):
        return print(f"La eficiencia no paso la 1era prueba, el evento ha terminado.")
    
    def notify_phase_1_challenge_success(self):
        return print(f"La eficiencia paso la 1era prueba, se procede a la 2da prueba. Se han otorgado {self.event.result_success[0]} puntos y {self.event.result_success[1]} dolares")
    
    def pass_event_challenge_phase_2(self, risk_level:int, modifiers_points:int):
        return self.chosen_efficiency.challenge_efficiency(risk_level, modifiers_points)
    
    def launch_pass_event_challenge_phase_2_actions(self, enabled_modifiers:dict[str,list]):
        enabled_products = enabled_modifiers['enabled_products']
        enabled_projects = enabled_modifiers['enabled_projects']
        enabled_resources = enabled_modifiers['enabled_resources']
        self.notify_phase_2_challenge_success()
        self.update_efficiencies_with_granted_points(enabled_products, enabled_projects, enabled_resources)
        self.player.apply_challenge_result(self.event.result_success)
    
    def launch_failed_event_challenge_phase_2_actions(self):
        self.notify_phase_2_challenge_failed()
        self.player.apply_challenge_result(self.event.result_failure)
        
    
    def notify_phase_2_challenge_failed(self):
        return print(f"La eficiencia no paso la 2da prueba, el evento ha terminado. Se han quitado {self.event.result_failure[0]} puntos y {self.event.result_failure[1]} dolares")

    def notify_phase_2_challenge_success(self):
        return print(f"La eficiencia paso la 2da prueba, el evento ha terminado. Se han otorgado {self.event.result_success[0]} puntos y {self.event.result_success[1]} dolares")
    
    def set_chosen_efficiency(self, efficiency:Efficiency):
        self.chosen_efficiency = efficiency
        
    def set_challenger_event(self, event:Event):
        self.event = event
    
    #Logic to give the efficiency the points the player's modifiers can grant when passing the event's challenge
    def update_efficiencies_with_granted_points(self,enabled_products:list[Product], enabled_projects:list[Project], enabled_resources:list[Resource]):
        for product in enabled_products:
            self.chosen_efficiency.update_by_product(product, 'event')(self.event_level)
        for project in enabled_projects:
            self.chosen_efficiency.update_by_project(project, self.event_level)
        for resource in enabled_resources:
            self.chosen_efficiency.update_by_resource(resource, self.event_level)
        
    def notify_event_level(self):
        return print(f"El nivel del evento es {self.event_level}")
    
    def notify_dice_roll_result(self, dices:List[int], sum_number:int):
        return print(f"El resultado del lanzamiento de dados es {dices} que suman: {sum_number}")
    
    def notify_dice_number_to_risk_points(self):
        return print(f"Se deben lanzar {self.event_level} dados para saber cuantos puntos de riesgo se van a obtener")
    
    def notify_payed_salaries(self):
        return print(f"Este nuevo mes se han pagado {self.player.salaries_to_pay}$ en los salarios de los recursos")
    
    def notify_event_end(self):
        return print("El evento ha terminado")
    
    def notify_required_own_eficiency_points(self, required_efficiencies:List[Efficiency]):
        data:dict[str,int] = {}
        for efficiency in required_efficiencies:
            data[efficiency.name] = efficiency.points
        return print(f"Estos son los puntos de tus eficiencias que son retadas por el evento: {', '.join([f'{key}: {value}' for key, value in data.items()])}") 
    
    def notify_chosen_efficiency_data(self):
        return print(f"La eficiencia escogida es {self.chosen_efficiency.name} porque es la que tiene mas puntos.")
    
    def notify_enabled_modifiers(self, enabled_modifiers:dict[str,list]):
        print(f"Estos son los productos, proyectos y recursos que pueden ser modificados por el evento:")
        print(f"Enabled products: {[product.name for product in enabled_modifiers['enabled_products']]}")
        print(f"Enabled projects: {[project.name for project in enabled_modifiers['enabled_projects']]}")
        print(f"Enabled resources: {[resource.name for resource in enabled_modifiers['enabled_resources']]}")

    def notify_possible_modifiers_points_granted(self, modifiers_points:tuple[int,int,int]):
        print(f"Estos son los puntos que se pueden otorgar por los modificadores:")
        print(f"Puntos por productos: {modifiers_points[0]}")
        print(f"Puntos por proyectos: {modifiers_points[1]}")
        print(f"Puntos por recursos: {modifiers_points[2]}")
            
    def notify_possible_points_to_be_granted(self, points:int):
        print(f"Se pueden otorgar {points} puntos en total. (Sumando los posibles puntos de los modificadores y los puntos de fortaleza de las eficiencias)")
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
    def current_day_of_week(self):
        return self.current_day % 7
    
    @property
    def current_day_in_month(self):
        return (self.current_day % 30) + 1 #originally wasn't +1
    
    @property
    def current_trimester(self):
        return np.ceil(self.current_month / 3)
    
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
    
    # def update_current_month(self):
    #     self.old_month = self.current_month
        
    def start_new_month(self):
        self.old_month = self.current_month
        
    def is_weekend(self):
        return self.current_day_of_week in [6, 0]
    
    def day_of_week(self):
        days = {
            0: "Lunes",
            1: "Martes",
            2: "Miercoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sabado",
            6: "Domingo"
        }
        return days[self.current_day_of_week]
    
    def journey_reached_end(self, limit_days:int):
        return self.current_day >= limit_days
    
    def check_month_limit(self):
        return self.current_month >= self.max_running_projects
    
    def notify_current_day_in_month(self):
        return print(f"Estas en el {self.current_day_in_month} / {self.current_month}")
    
    def notify_current_day_of_week(self):
        return f"Estas en {self.day_of_week()}"
    
    def notify_weekend(self):
        if self.is_weekend():
            return print(f"Es fin de semana, no te toca ningun evento")
        return print("No es fin de semana")