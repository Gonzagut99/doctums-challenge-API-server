from copy import deepcopy
import numpy as np
import random
from typing import Tuple

class Player:
    def __init__(self, context=None, id=None, name=None, initial_budget=1000):
        self.id:str|None = id
        self.name:str|None = name
        self.context = context
        self.efficiencies = deepcopy(self.context.EFFICIENCIES)  # standard efficiencies beginning with 0 points
        self.products = dict()
        self.projects = dict()
        self.resources = dict()
        self.budget = initial_budget
        self.score = 0
        self.salaries_to_pay = 0
        self.actual_date = 0  # day stacked (360)
        self._get_legacy()
        self.first_turn_in_month = True

    @property
    def month(self):
        return (self.actual_date // 30) + 1

    @property
    def running_projects(self): 
        return [key for key, value in self.projects.items() if not value.is_finished(self.month)]
    
    @property
    def finished_projects(self): 
        return [key for key, value in self.projects.items() if value.is_finished(self.month)]

    def _get_legacy(self):
        legacy_list = self.context.LEGACY
        legacy_choice = random.choice(legacy_list)
        print('*********************************Productos Inciales - No se lanzo dado***************')
        for item in legacy_choice:
            self._add_legacy_product(item)

            print(f"You have inherited: {self.context.PRODUCTS.get(item).name}")
        print(f"Lista de Productos adquiridos: {self.products.keys()}")
        self.display_efficiencies()
        print('***********************************START GAME*************************************')
    
    def _add_legacy_product(self, product_id):
        product = self.context.PRODUCTS.get(product_id, None)
        name = product.name
        if product_id in self.products.keys():
            print(f"Product {name} is already available")
            return
        purchased_product = deepcopy(product)
        purchased_product.purchased_on = self.month
        purchased_product.is_legacy = True
        self.products[product_id] = purchased_product
        for efficiency in self.efficiencies.values():
            efficiency.start_with_legacy_points(self.products[product_id])
        return

    def budget_enough_for_buying(self, modifier):
        if self.budget < modifier.cost:
            print(f"You dont have enough budget to buy: {modifier.name}")
            return False

        return True

    def _add_product(self, product_id):
        product = self.context.PRODUCTS.get(product_id, None)
        name = product.name
        if product_id in self.products.keys():
            print(f"Product {name} is already available")
            return
        purchased_product = deepcopy(product)
        purchased_product.purchased_on = self.month
        
        is_meeting_requirements, number_of_requirements_needed = self.is_product_meeting_requirements(product)
        self.products[product_id] = purchased_product
        
        if not is_meeting_requirements:
            self.disable_product_thriving(product)
            print(f"Puedes añadir este producto: '{name}', pero no te dara puntos porque te falta tener al menos {number_of_requirements_needed} de estos productos: {product.requirements}")
        else:
            self.enable_product_thriving(product)
        self.update_products_thriving_state()
        print(f"El producto '{name}' ha sido añadido a tu lista de productos adquiridos")
        
        # This is no longer necessary since the points system has been changed
        # for efficiency in self.efficiencies.values():
        #     efficiency.update_by_product(product, self.products)
    
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
        return len(purchased_requirements) >= number_of_requirements_needed,  number_of_requirements_needed
    
    def update_products_thriving_state(self):
        for product in self.products.values():
            is_meeting_requirements, number_of_requirements_needed = self.is_product_meeting_requirements(product)
            if is_meeting_requirements:
                self.enable_product_thriving(product) and print(f"El Producto '{product.name}' ya puede otorgarte puntos porque cumple los requerimientos")
            else:
                self.disable_product_thriving(product) and print(f"Este: '{product.name}' aún no te dara puntos porque te falta tener al menos {number_of_requirements_needed} de estos productos: {product.requirements}")

    def check_month_number_of_purchases(self, modifier_type):
        purchased_modifiers = None

        if modifier_type == "product":
            purchased_modifiers = {
                key: value for key, value in self.products.items() if value.purchased_on == self.month and not value.is_legacy
            }
        elif modifier_type == "project":
            purchased_modifiers = {
                key: value for key, value in self.projects.items() if value.purchased_on == self.month
            }
        elif modifier_type == "resource":
            purchased_modifiers = {
                key: value for key, value in self.resources.items() if value.purchased_on == self.month
            }
        else:
            pass
        return len(purchased_modifiers)

    def buy_product(self, product_id):
        if self.check_month_number_of_purchases("product") >= 5:
            print("You have already purchased 5 products this month, you are not allowed to buy more")
            return
        product = self.context.PRODUCTS.get(product_id, None)
        
        if self.budget_enough_for_buying(product):
            self._add_product(product_id)
            # Todo: print some message if the requirements for the product are not bought
            self.budget -= product.cost
        print(f"Presupuesto restante: {self.budget}")

    def buy_project(self, project_id):
        
        if self.check_month_number_of_purchases("project") >= 1:
            print("You have already bought 1 project this month, you are not allowed to buy more")
            return
        if len(self.running_projects) >= 3:
            print("You are note allowed to run more than 3 projects in parallel")
            return
        project = self.context.PROJECTS.get(project_id, None)
        name = project.name
        if project_id in self.projects.keys():
            print(f"Project {name} is already available")
            return
        if self.budget_enough_for_buying(project):
            bought_project = deepcopy(project)
            bought_project.purchased_on = self.month
            bought_project.start_datum = self.month + 1
            # Todo: check datum --> do you still have time to get the products
            self.projects[project_id] = bought_project
            self.budget -= project.cost
        print(f"Presupuesto restante: {self.budget}")

    def hire_resource(self, resource_id):
        if self.check_month_number_of_purchases("resource") >= 1:
            print("You have already hired 1 resource this month, you are not allowed to buy more")
            return
        resource = self.context.RESOURCES.get(resource_id, None)
        name = resource.name
        if resource_id in self.resources.keys():
            print(f"Resource {name} is already available")
            return
        if not self.budget_enough_for_buying(resource):
            return

        hired_resource = deepcopy(resource)
        hired_resource.purchased_on = self.month
        self.resources[resource_id] = hired_resource
        self.salaries_to_pay += hired_resource.monthly_salary
        self.budget -= resource.cost
        print(f"Presupuesto restante: {self.budget}")

    def pay_salaries(self):
        self.budget -= self.salaries_to_pay
        # TODO: charge salaries after hiring (not in the first month)

    def get_products_from_projects(self):
        for project_id, project in self.projects.items():
            time_passed = self.month - project.start_datum
            if time_passed == project.project_length:
                delivered_products_ids = project.delivered_products
                for product_id in delivered_products_ids:
                    self._add_product(product_id)  # add products and its efficiencies

                # for efficiency in self.efficiencies.values():
                #     efficiency.update_by_project(project)  # add points to efficiency corresponding to the project

    def get_products_from_resources(self):
        last_month = self.month - 1
        purchased_resources_last_month = [
            resource for resource in self.resources.values() if resource.purchased_on == last_month
        ]
        print(f"Has recibido los siguientes productos del recurso {purchased_resources_last_month[0]}: {purchased_resources_last_month[0].developed_products} ")
        
        for resource in purchased_resources_last_month:
            for product_id in resource.developed_products:
                self._add_product(product_id)

            # for efficiency in self.efficiencies.values():
            #     efficiency.update_by_resource(resource)
        

    def throw_dices(self, number):
        dices = np.random.randint(1, 6, size=number)
        return dices, dices.sum()

    def check_efficiencies(self):
        pass

    def apply_challenge_result(self, result: Tuple):
        points, money = result
        self.score += points
        self.budget += money

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


