from copy import deepcopy
from operator import itemgetter
import random
from typing import List

from fastapi import WebSocket
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
        self.time_manager:TimeManager = TimeManager(self.player)
        self.event_manager:EventManager = EventManager(self.player, self.time_manager)
        self.player_state:str|None = 'playing' #"broke", "playing", "finished"
        self.turn_state:str|None = 'end' #end, playing
        self.player_connection: WebSocket = self.player.connection
        # self.is_first_turn:bool = False
    
    # def set_first_turn(self):
    #     self.is_first_turn = True
    
    def is_player_turn(self):
        return self.turn_state == "playing"
        
    def load_player_data(self):
        self.player.get_legacy(self.time_manager.current_month)
        self.player.update_products_thriving_state()
    
    def end_turn(self):
        self.turn_state = "end"
        
    def is_player_able_to_play(self):
        if self.is_journey_finished() or self.is_game_over():
            return False
        return True
    
    def get_player_stats(self):
        player = self.player
        current_month = self.time_manager.current_month if self.time_manager.current_month != 0 else 1
        current_day = self.time_manager.current_day_in_month if self.time_manager.current_day_in_month != 0 else 1 
        formated_month = f"{current_day:02d}/{current_month:02d}"
        return  {
                "playerId": player.id,
                "avatarId": player.avatar_id,
                "name": player.name,
                "total": player.turn["total"],
                "budget": player.budget,
                "score": player.score,
                "date": formated_month 

            }
        
    # def begin_first_turn(self):
    #     self.turn_state = "playing"

    #1st Step
    # def begin_regular_turn:
    def begin_turn(self):
        self.turn_state = "playing"
        #Since player will never surpass more than month it is possible to run the same logic in every  type of turn
        self.sort_steps_to_advance()
        # Time control
        if not self.time_manager.is_weekend() and self.is_player_able_to_play():
            self.time_manager.notify_current_day_in_month()
            self.time_manager.notify_current_day_of_week()
            #We only sent data to player if he can do any action
        if self.time_manager.is_weekend():
            self.time_manager.notify_current_day_in_month()
            self.time_manager.notify_current_day_of_week()
            self.time_manager.notify_weekend()
        if self.is_player_able_to_play():
            # Only when journey is not finished or player hasn't lost, can the new month actions be launched
            self.launch_new_month_actions()
        if not self.is_player_able_to_play():
            self.handle_finish_journey()     
    
    # def start_game_journey(self):
    #     # random.seed(0)
    #     # np.random.seed(0)
    #     if self.is_first_turn:
    #         self.begin_first_turn()
    #         self.launch_new_journey_actions()
    #     # while not self.is_journey_finished() and self.player_state == "playing":
    #     #     self.turn_play()
    
    # def launch_new_journey_actions(self):
    #     if self.time_manager.is_new_month():
    #         self.time_manager.start_new_month()
    #         self.is_first_turn = False
    #         self.time_manager.first_turn_in_month = False
            #Then the player must decide if he wants to buy products, projects or resources

    #Continues journey in future turns
    # Called by the dispatcher after the first player turn and when beginning a new turn
    # def proceed_journey(self):
    #     self.begin_turn()

    #2nd step
    #Called by the dispatcher after the player has submitted his action plan      
    def submit_plan(self, actions:dict[str,list]):
        if self.turn_state == "playing":
            actual_month = self.time_manager.current_month
            if actions.get("products"):
                for product_id in actions.get("products"):
                    self.player.buy_product(product_id, actual_month)
            if actions.get("projects"):
                for project_id in actions.get("projects"):
                    # self.player.buy_project(project_id, actual_month, actual_month + 1)
                    self.player.buy_project(project_id, actual_month, actual_month)
            if actions.get("resources"):
                for resource_id in actions.get("resources"):
                    self.player.hire_resource(resource_id, actual_month, actual_month)
        else:
            print("No puedes hacer acciones en este turno")
    
    #3rd step
    #Called by the dispatcher after the player has submitted his action plan
    def resume_turn(self):
        self.execute_eventflow()
        self.event_manager.notify_event_end()
        self.end_turn()   

    
    def launch_new_month_actions(self):
        if self.time_manager.is_new_month():
            self.time_manager.start_new_month()
            self.player.pay_salaries()
            self.event_manager.notify_payed_salaries()
            self.player.get_products_from_projects(self.time_manager.finished_projects, self.time_manager.current_month)
            self.player.get_products_from_resources(self.time_manager.finished_resources, self.time_manager.current_month)
            self.player.update_products_thriving_state()
            self.update_projects_time()
            self.update_resources_time()
            #self.launch_buy_modifiers_actions()
            
    def sort_steps_to_advance(self):
        dices, steps = self.player.throw_dices(self.journey_dices_number)
        self.current_dice_roll = dices.tolist()
        self.current_dice_result = steps
        self.time_manager.advance_day(steps)
        
    def execute_eventflow(self)->None:
        if self.turn_state == "end":
            raise Exception("It's not the player's turn")
        #Time control
        if not self.time_manager.is_weekend() and self.is_player_able_to_play():
            self.launch_event_flow()

    def launch_event_flow(self):
        event_level = self.get_board_field_number()
        self.event_manager.set_event_level(event_level)
        self.event_manager.notify_event_level()
        event = self.event_manager.take_random_event(self.time_manager.current_trimester)
        self.event_manager.set_challenger_event(event)
        required_efficiencies = self.event_manager.get_required_efficiencies()
       # self.event_manager.notify_required_own_eficiency_points()
        
        #Also sets the chosen_efficiency within the event_manager
        self.event_manager.choose_efficiency_by_max_strength_points(required_efficiencies)
        self.event_manager.notify_chosen_efficiency_data()
        
        #get modifiers that gather requirements to grant points
        current_enabled_modifiers:dict[str,list] = self.event_manager.enabled_modifiers(event)
        self.event_manager.notify_enabled_modifiers(current_enabled_modifiers)
        
        #get data to pass the event challenge
        possible_total_strength_points, possible_modifiers_points=self.event_manager.soft_possible_efficiency_strength_points_calculation(current_enabled_modifiers)
        
        #Event Challenge
        #Challenge Phase 1: Evaluate if won or loose challenge with the difference between efficiency points and the required points
        if not self.event_manager.pass_event_challenge_phase_1(possible_total_strength_points):
            self.event_manager.has_passed_1st_challenge = False
            dices, risk_points = self.event_manager.launch_failed_event_challenge_phase_1_actions()
            self.event_manager.risk_challenge_dices = dices
            self.event_manager.risk_points = risk_points
            
            #Challenge Phase 2: Evaluate if won or loose challenge with the risk points
            if not self.event_manager.pass_event_challenge_phase_2(risk_points, possible_modifiers_points):
                self.event_manager.has_passed_2nd_challenge = False
                self.event_manager.launch_failed_event_challenge_phase_2_actions()
            else:
                self.event_manager.has_passed_2nd_challenge = True
                self.event_manager.launch_pass_event_challenge_phase_2_actions(current_enabled_modifiers)   
                self.event_manager.set_chosen_efficiency_rewarded_points(possible_modifiers_points)
        else:
            self.event_manager.has_passed_1st_challenge = True
            self.event_manager.launch_pass_event_challenge_phase_1_actions(current_enabled_modifiers)  
            self.event_manager.set_chosen_efficiency_rewarded_points(possible_modifiers_points)          
        
    def get_board_field_number(self)->int:
        board_context = self.context.board.reshape(-1)
        field = board_context[self.time_manager.current_day - 1]
        return int(field)
    
    def is_journey_finished(self)->bool:
        if self.time_manager.journey_reached_end(self.journey_days_limit):
            return True
        elif self.player_state == "broke":
            return True
        return False
    
    def is_game_over(self) -> bool:
        if self.player_state == "broke":
            return True
        return False
    
    def handle_finish_journey(self):
        if self.time_manager.journey_reached_end(self.journey_days_limit):
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
        
    def update_projects_time(self):
        #all projects not in finished projects
        for project in self.player.projects.values():
            if not project.is_finished(self.time_manager.current_month):
                project.update_remaining_months(self.time_manager.current_month)
    
    def update_resources_time(self):
        for resource in self.player.resources.values():
            if not resource.is_finished(self.time_manager.current_month):
                resource.update_remaining_time(self.time_manager.current_month)
                
    def update_player_products_thriving_state(self):
        self.player.update_products_thriving_state()
                
    def get_products_state(self):
        product_state_list = [] 
        for product in self.player.products.values():
            _ , purchased_requirements = self.player.is_product_meeting_requirements(product)
            product_state_list.append({
                "product_id": product.ID,
                "is_enabled": product.able_to_grant_points,
                "purchased_requirements": purchased_requirements
            })
        return product_state_list

    def get_projects_state(self):
        #return project_id and remaining_time to finish
        list_projects = []
        for project in self.player.projects.values():
            list_projects.append({
                "project_id": project.ID,
                "remaining_time": self.time_manager.get_project_remaining_time(project)
            })
        return list_projects
        
    def get_resources_state(self):
        list_resources = []
        for resource in self.player.resources.values():
            list_resources.append({
                "resource_id": resource.ID,
                "remaining_time": self.time_manager.get_resource_remaining_time(resource)
            }) 
        return list_resources
            
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
        return (self.current_day % 30) #originally wasn't +1
    
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

    def journey_reached_end(self, limit_days:int):
        return self.current_day >= limit_days
    
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
    
    def check_month_limit(self):
        return self.current_month >= self.max_running_projects
    
    def get_project_remaining_time(self, project:Project):
        return project.start_datum + project.project_length - self.current_month
    
    def get_resource_remaining_time(self, resource:Resource):
        return resource.start_datum + resource.resource_lenght - self.current_month
    
    def notify_current_day_in_month(self):
        return print(f"Estas en el {self.current_day_in_month} / {self.current_month}")
    
    def notify_current_day_of_week(self):
        return f"Estas en {self.day_of_week()}"
    
    def notify_weekend(self):
        if self.is_weekend():
            return print(f"Es fin de semana, no te toca ningun evento")
        return print("No es fin de semana")  

class EventManager:
    def __init__(self, player:Player, time_manager:TimeManager) -> None:
        self.player:Player | None = player
        self.time_manager:TimeManager = time_manager
        self.event:Event | None = None
        self.chosen_efficiency:Efficiency | None = None
        self.event_level:int|None = None
        self.has_passed_1st_challenge:bool = False
        self.has_passed_2nd_challenge:bool = False
        self.risk_challenge_dices:list[int] = []
        self.risk_points:int = 0
        self.obtained_score:int = 0
        self.obtained_budget:int = 0
        self.obtained_efficiencies_points:int = 0
    
    #Va a ir a efficiency
    def enabled_modifiers(self, event:Event) -> dict[str,list]:
        enabled_products = [product for product in self.chosen_efficiency.get_enabled_products(list(self.player.products.values())) if product.ID in event.modifiable_products]
        enabled_projects = [project for project in self.chosen_efficiency.get_enabled_projects(list(self.player.projects.values()), self.time_manager.current_month) if project.ID in event.modifiable_projects]
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
    
    def possible_modifiers_points_granted(self, event_level:int, enabled_modifiers:dict[str,list]):
        #Calculate possible points to grant
        enabled_products = enabled_modifiers['enabled_products']
        enabled_projects = enabled_modifiers['enabled_projects']
        enable_resources = enabled_modifiers['enabled_resources']
        product_points = sum([self.chosen_efficiency.points_by_event_level(product.points_to_grant,event_level,'product') for product in enabled_products])
        project_points = sum([self.chosen_efficiency.points_by_event_level(project.points_to_grant, event_level, 'project') for project in enabled_projects])
        resource_points = sum([self.chosen_efficiency.points_by_event_level(resource.points_to_grant, event_level, 'resource') for resource in enable_resources])
        return product_points, project_points, resource_points

    def possible_modifiers_points_sum_to_be_granted(self, modifiers_points:tuple[int,int,int])->int:
        return sum(modifiers_points)
    
    def possible_efficiency_points_to_be_granted(self, possible_modifiers_points:int, efficiency_strength_points:int)->int:
        possible_points = possible_modifiers_points+efficiency_strength_points
        return possible_points
        
    def soft_possible_efficiency_strength_points_calculation(self, current_enabled_modifiers:dict[str, list]):
        product_pts, project_pts, resources_pts = self.possible_modifiers_points_granted(self.event_level, current_enabled_modifiers)
        #self.event_manager.notify_possible_modifiers_points_granted((product_pts, project_pts, resources_pts))
        possible_modifiers_points=self.possible_modifiers_points_sum_to_be_granted((product_pts, project_pts, resources_pts))
        possible_total_strength_points=self. possible_efficiency_points_to_be_granted(possible_modifiers_points, self.chosen_efficiency.points)
        #self.notify_possible_points_to_be_granted(possible_total_strength_points)
        return possible_total_strength_points, possible_modifiers_points
    
    def pass_event_challenge_phase_1(self, possible_efficiency_strength_points:int):
        pass_challenge_with_points_difference = self.chosen_efficiency.check_enough_points_to_pass(self.event_level,possible_efficiency_strength_points)
        return pass_challenge_with_points_difference
    
    def launch_pass_event_challenge_phase_1_actions(self, enabled_modifiers:dict[str,list]):
        enabled_products = enabled_modifiers['enabled_products']
        enabled_projects = enabled_modifiers['enabled_projects']
        enabled_resources = enabled_modifiers['enabled_resources']
        self.notify_phase_1_challenge_success()
        self.update_efficiencies_with_granted_points(enabled_products, enabled_projects, enabled_resources)
        self.player.apply_challenge_result(self.event.result_success, 'success')
        self.set_event_rewards(self.event.result_success[0], self.event.result_success[1])
    
    def launch_failed_event_challenge_phase_1_actions(self):
        self.notify_phase_1_challenge_failed()
        dices, risk_points = self.player.throw_dices(self.event_level)
        self.notify_dice_roll_result(dices=dices, sum_number=risk_points)
        self.notify_dice_number_to_risk_points()
        #IMPIRTANT: It is not necessary to update rewarded points because that is define in the 2nd phase of the challenge
        return dices.tolist(), risk_points
        
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
        self.player.apply_challenge_result(self.event.result_success, 'success')
        self.set_event_rewards(self.event.result_success[0], self.event.result_success[1])
    
    def launch_failed_event_challenge_phase_2_actions(self):
        self.notify_phase_2_challenge_failed()
        self.player.apply_challenge_result(self.event.result_failure, "fail")
        self.set_event_punishment(self.event.result_failure[0], self.event.result_failure[1])
        
    
    def notify_phase_2_challenge_failed(self):
        return print(f"La eficiencia no paso la 2da prueba, el evento ha terminado. Se han quitado {self.event.result_failure[0]} puntos y {self.event.result_failure[1]} dolares")

    def notify_phase_2_challenge_success(self):
        return print(f"La eficiencia paso la 2da prueba, el evento ha terminado. Se han otorgado {self.event.result_success[0]} puntos y {self.event.result_success[1]} dolares")
    
    def set_event_rewards(self, obtained_score:int, obtained_budget:int):
        self.obtained_score = obtained_score
        self.obtained_budget = obtained_budget
        
    def set_event_punishment(self, taken_score:int, taken_budget:int):
        self.obtained_score = taken_score
        self.obtained_budget = taken_budget
        
    def set_chosen_efficiency_rewarded_points(self, points:int):
        self.obtained_efficiencies_points = points
    
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

