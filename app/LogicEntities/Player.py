from copy import deepcopy
from fastapi import WebSocket
import numpy as np
import random
from typing import List, Tuple

from app.LogicEntities.Context import Context
from app.LogicEntities.Efficiency import Efficiency
from app.LogicEntities.Modifiers import  Product, Project, Resource

class Player:
    def __init__(self, context:Context=None, id=None, name=None, avatar_id:int = 1 , initial_budget=100000, connection =None):
        self.id:str|None = id
        self.name:str|None = name
        self.context:Context|None = context
        self.efficiencies:dict[str,Efficiency] = deepcopy(self.context.EFFICIENCIES)  # standard efficiencies beginning with 0 points
        self.products:dict[str,Product] = dict()
        self.projects:dict[str,Project] = dict()
        self.resources:dict[str,Resource] = dict()
        self.turn:dict[str, str] = dict()
        self.budget = initial_budget
        self.score = 0
        self.salaries_to_pay = 0
        self.is_host = False
        self.avatar_id = avatar_id
        self.recently_bought_modifiers = dict()
        self.connection:WebSocket | None = connection
        
    def get_products(self):
        #get only all products name
        return [p for p in self.products.keys()]

    
    def _add_legacy_product(self, product_id, actual_month:int):
        product = self.context.PRODUCTS.get(product_id, None)
        name = product.name
        if product_id in self.products.keys():
            print(f"Product {name} is already available")
            return
        purchased_product = deepcopy(product)
        purchased_product.purchased_on = actual_month
        purchased_product.is_purchased = False
        self.products[product_id] = purchased_product
        for efficiency in self.efficiencies.values():
            efficiency.start_with_legacy_points(self.products[product_id])
        return

    def budget_enough_for_buying(self, modifier):
        if self.budget < modifier.cost:
            print(f"You dont have enough budget to buy: {modifier.name}")
            return False

        return True
    
    def get_recently_bought_modifiers(self):
        modifiers = deepcopy(self.recently_bought_modifiers)
        self.recently_bought_modifiers.clear()
        return modifiers
    
    def add_recently_bought_modifier(self, modifier, modifier_id): 
        if self.recently_bought_modifiers.get(modifier, None) is None:
            self.recently_bought_modifiers[modifier] = [modifier_id]
        else:
            self.recently_bought_modifiers[modifier].append(modifier_id)
            
    # def get_products_state(self):
    #     product_state_list = [] 
    #     for product in self.products.values():
    #         _ , purchased_requirements = self.is_product_meeting_requirements(product)
    #         product_state_list.append({
    #             "product_id": product.ID,
    #             "is_enabled": product.able_to_grant_points,
    #             "purchased_requirements": [p.ID for p in purchased_requirements]
    #         })
    #     return product_state_list

    # def get_projects_state(self):
    #     #return project_id and remaining_time to finish
    #     list_projects = []
    #     for project in self.projects.values():
    #         list_projects.append({
    #             "project_id": project.ID,
    #             "remaining_time": self.time_manager.get_project_remaining_time(project)
    #         })
        
    # def get_resources_state(self):
    #     list_resources = []
    #     for resource in self.resources.values():
    #         list_resources.append({
    #             "resource_id": resource.ID,
    #             "remaining_time": self.time_manager.get_resource_remaining_time(resource)
    #         })     
        

    def _add_product(self, product_id, actual_month):
        product = self.context.PRODUCTS.get(product_id, None)
        name = product.name
        if product_id in self.products.keys():
            print(f"Product {name} is already available")
            return
        else:
            self.add_recently_bought_modifier("products", product_id)
        purchased_product = deepcopy(product)
        purchased_product.purchased_on = actual_month
        
        is_meeting_requirements, purchased_requirements = self.is_product_meeting_requirements(product)
        self.products[product_id] = purchased_product
        
        if not is_meeting_requirements:
            self.disable_product_thriving(product)
            # print(f"Puedes añadir este producto: '{name}', pero no te dara puntos porque te falta tener al menos {number_of_requirements_needed} de estos productos: {product.requirements}")
        else:
            self.enable_product_thriving(product)
        self.update_products_thriving_state()
        # print(f"El producto '{name}' ha sido añadido a tu lista de productos adquiridos")
        
        # This is no longer necessary since the points system has been changed
        # for efficiency in self.efficiencies.values():
        #     efficiency.update_by_product(product, self.products)]
        
    def get_legacy(self, actual_month:int):
        legacy_list = self.context.LEGACY
        legacy_choice = random.choice(legacy_list)
        for item in legacy_choice:
            self._add_legacy_product(item, actual_month)
        # self.display_efficiencies()
    
    # When meeting the product requirements the product is able to grant points        
    def enable_product_thriving(self, product):
        if product.ID in self.products.keys():
            self.products[product.ID].able_to_grant_points = True
        return self.products[product.ID].able_to_grant_points
    
    # When not meeting the product requirements the product is not able to grant points        
    def disable_product_thriving(self, product):
        if product.ID in self.products.keys():
            self.products[product.ID].able_to_grant_points = False
            return self.products[product.ID].able_to_grant_points
        else:
            print(f"El producto con ID '{product.ID}' no existe en el diccionario.")
            return False
    
    # Check if the product is able to grant points
    def is_product_meeting_requirements(self, product):
        # Key: length of the requirements for the product
        # Value: number of requirements that need to be purchased to get whole benefits
        requirements_dict = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3}
        product_requirements = product.requirements
        purchased_requirements = [
            requirement for requirement in product_requirements if requirement in self.products
        ]
        #number_of_requirements_needed = requirements_dict.get(len(product_requirements), 0)
        number_of_requirements_needed = requirements_dict.get(len(product_requirements), 4)
        
        return len(purchased_requirements) >= number_of_requirements_needed,  purchased_requirements
    
    def update_products_thriving_state(self):
        for product in self.products.values():
            is_meeting_requirements, purchased_requirements = self.is_product_meeting_requirements(product)
            if is_meeting_requirements:
                self.enable_product_thriving(product) and print(f"El Producto '{product.name}' ya puede otorgarte puntos porque cumple los requerimientos")
            else:
                self.disable_product_thriving(product) 
                #print(f"Este: '{product.name}' aún no te dara puntos porque te falta tener al menos {number_of_requirements_needed} de estos productos: {product.requirements}")

    def check_month_number_of_purchases(self, modifier_type, month_to_check:int):
        purchased_modifiers = None

        if modifier_type == "product":
            purchased_modifiers = {
                key: value for key, value in self.products.items() if value.purchased_on == month_to_check and value.is_purchased
            }
        elif modifier_type == "project":
            purchased_modifiers = {
                key: value for key, value in self.projects.items() if value.purchased_on == month_to_check
            }
        elif modifier_type == "resource":
            purchased_modifiers = {
                key: value for key, value in self.resources.items() if value.purchased_on == month_to_check
            }
        else:
            pass
        return len(purchased_modifiers)

    def buy_product(self, product_id, actual_month):
        if self.check_month_number_of_purchases("product", actual_month) >= 5:
            print("You have already purchased 5 products this month, you are not allowed to buy more")
            return
        product = self.context.PRODUCTS.get(product_id, None)
        
        if self.budget_enough_for_buying(product):
            self._add_product(product_id, actual_month)
            # Todo: print some message if the requirements for the product are not bought
            self.budget -= product.cost

    def buy_project(self, project_id, actual_month, month_to_start):
        
        if self.check_month_number_of_purchases("project", actual_month) >= 1:
            print("You have already bought 1 project this month, you are not allowed to buy more")
            return
        
        #This validation must be perform by TimeManager
        # if len(self.running_projects) >= 3:
        #     print("You are note allowed to run more than 3 projects in parallel")
        #     return
        project = self.context.PROJECTS.get(project_id, None)
        name = project.name
        if project_id in self.projects.keys():
            print(f"Project {name} is already available")
            return
        else:
            self.add_recently_bought_modifier("projects", project_id)
        if self.budget_enough_for_buying(project):
            bought_project = deepcopy(project)
            bought_project.purchased_on = actual_month
            bought_project.start_datum = month_to_start
            # Todo: check datum --> do you still have time to get the products
            self.projects[project_id] = bought_project
            self.budget -= project.cost
        print(f"Presupuesto restante: {self.budget}")

    def hire_resource(self, resource_id, actual_month, month_to_start):
        if self.check_month_number_of_purchases("resource", actual_month) >= 1:
            print("You have already hired 1 resource this month, you are not allowed to buy more")
            return
        resource = self.context.RESOURCES.get(resource_id, None)
        name = resource.name
        if resource_id in self.resources.keys():
            print(f"Resource {name} is already available")
            return
        else:
            self.add_recently_bought_modifier("resources", resource_id)
        if not self.budget_enough_for_buying(resource):
            return

        hired_resource = deepcopy(resource)
        hired_resource.purchased_on = actual_month
        hired_resource.start_datum = month_to_start
        self.resources[resource_id] = hired_resource
        self.salaries_to_pay += hired_resource.monthly_salary
        self.budget -= resource.cost
        print(f"Presupuesto restante: {self.budget}")

    def pay_salaries(self):
        self.budget -= self.salaries_to_pay

    def get_products_from_projects(self, finished_projects: List[Project], actual_month: int):
        for project in finished_projects:
            for product_id in project.delivered_products:
                self._add_product(product_id, actual_month)

    def get_products_from_resources(self, finished_resources: List[Resource], actual_month: int):        
        for resource in finished_resources:
            for product_id in resource.developed_products:
                self._add_product(product_id, actual_month)

            # for efficiency in self.efficiencies.values():
            #     efficiency.update_by_resource(resource)
        

    def throw_dices(self, number:int) -> Tuple[np.ndarray, int]:
        dices = np.random.randint(1, 6, size=number)
        return dices, int(dices.sum())

    def check_efficiencies(self):
        pass

    def apply_challenge_result(self, result: Tuple, state:str):
        points, money = result
        self.score += points
        self.budget += money
        # if state == "success":
        #     self.score += points
        #     self.budget += money
        # elif state == "fail":
        #     self.budget -= money
        #     self.score -= points
            


    def display_modifier(self, list_modifiers, modifier_type):
        print(f"Modifier: {modifier_type}")
        for modifier in list_modifiers:
            print(f"{modifier.ID}: {modifier.name}")
            print(f"Purchased on: {modifier.purchased_on} for: {modifier.cost} dollars.")
        print("--------------------------------------------------------------------")

    def display_efficiencies(self):
        print(f"Actual value of efficiencies")
        for efficiency in self.efficiencies.values():
            print(f"{efficiency.name}: {efficiency.points}")

    def get_efficiencies(self):
        #get only all efficiencies id and points
        return {efficiency.ID: efficiency.points for efficiency in self.efficiencies.values()}


