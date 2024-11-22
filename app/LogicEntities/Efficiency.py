from dataclasses import dataclass
from typing import List, Tuple, Any
import numpy as np

from app.LogicEntities.Modifiers import Product, Project, Resource

@dataclass
class Efficiency:
    name: str
    modifiable_by_products: list[str]
    modifiable_by_projects: list[str]
    modifiable_by_resources: list[str]
    points: int = None
    ID: int = None
    max_points: int = 36

    @property
    def number_of_products_modifiers(self):
        return len(self.modifiable_by_products)

    @property
    def number_of_projects_modifiers(self):
        length = len(self.modifiable_by_projects)
        return length if length > 0 else None

    @property
    def number_of_resources_modifiers(self):
        length = len(self.modifiable_by_resources)
        return length if length > 0 else None
    
    def start_with_legacy_points(self, legacy_product):
        self.update_by_product(legacy_product, "legacy")()
        #print(f"La eficiencia '{self.ID}' empieza con {self.points} puntos")
    
    def get_enabled_products(self, purchased_products):
        products = [product for product in purchased_products if product.ID in self.modifiable_by_products]
        return filter(lambda product: product.able_to_grant_points, products)
    
    def get_enabled_projects(self, purchased_projects, current_month):
        projects = [project for project in purchased_projects if project.ID in self.modifiable_by_projects ]
        # return filter(lambda project: not project.is_finished(current_month), projects) #TODO: Implement this in future versions
        return projects
        
    def get_enabled_resources(self, purchased_resources):
        resources = [resource for resource in purchased_resources if resource.ID in self.modifiable_by_resources]
        return resources
    
    # 1era prueba de eficiencia
    def check_enough_points_to_pass(self, event_level, tentative_effciency_strength_points):
        enough_points_by_efficiency_level = {
            1: 6,
            2: 12,
            3: 18,
            4: 24,
            5: 30,
            6: 36
        }
        if tentative_effciency_strength_points >= enough_points_by_efficiency_level[event_level]:
            print(f"Tienes {tentative_effciency_strength_points} puntos")
            print(f"La eficiencia paso la 1era prueba para un evento de nivel {event_level}, tiene {tentative_effciency_strength_points} puntos, necesitas {enough_points_by_efficiency_level[event_level]} puntos")
            return True
        else:
            print(f"Tienes {tentative_effciency_strength_points} puntos")
            print(f"La eficiencia '{self.ID}' no tiene suficientes puntos para superar la 1era prueba para un evento de nivel {event_level}, necesitas al menos {enough_points_by_efficiency_level[event_level]} puntos")
            return False
    
    def _multiply_points(self, points, multiplier):
        return points * multiplier
    
    def points_by_event_level (self, points, event_level, modifier:str):
        product_points_by_level = {
            1: 5,
            2: 4,
            3: 3,
            4: 2,
            5: 1,
            6: 1
        }
        project_points_by_level = {
            1: 2,
            2: 2,
            3: 1,
            4: 1,
            5: 1,
            6: 1
        }
        resource_points_by_level = {
            1: 3,
            2: 3,
            3: 2,
            4: 2,
            5: 1,
            6: 1
        }
        if modifier == "product":
            return self._multiply_points(points, product_points_by_level[event_level])
        elif modifier == "project":
            return self._multiply_points(points, project_points_by_level[event_level])
        elif modifier == "resource":
            return self._multiply_points(points, resource_points_by_level[event_level])
        else:
            return points
        

# Add points because oh faving products when certain events happen
    def update_by_product(self, product:Product, function_type: str):
        def legacy_function():
            if product.ID in self.modifiable_by_products:
                #At the beginning the legacy products inherit the point multplied by 5
                granted_points = self._multiply_points(product.points_to_grant, 5)
                self._add_points(granted_points)
            else:
                return
        
        def event_function(event_level:int):
            if product.ID in self.modifiable_by_products:
                granted_points = self.points_by_event_level(product.points_to_grant, event_level, "product")
                self._add_points(granted_points)
            else:
                return
        
        # def granted_by_modifier_function(product):
        #     if product.ID in self.modifiable_by_products:
        #         granted_points = product.points_to_grant
        #         self._add_points(granted_points)
        #     else:
        #         return
        
        functions = {
            'legacy': legacy_function,
            'event': event_function,
            #'granted_by_modifier': granted_by_modifier_function
        }
        
        return functions.get(function_type)
      
    # If we have the projects in the bag, add points to efficiency 
    def update_by_project(self, project:Project, event_level):
        if not self.number_of_projects_modifiers:
            return
        if project.ID in self.modifiable_by_projects:
            granted_points = self.points_by_event_level(project.points_to_grant, event_level, "project")
            self._add_points(granted_points)

    # If we have the resources in the bag, add points to efficiency 
    def update_by_resource(self, resource:Resource, event_level):
        if not self.number_of_resources_modifiers:
            return
        if resource.ID in self.modifiable_by_resources:
            granted_points = self.points_by_event_level(resource.points_to_grant, event_level, "resource")
            self._add_points(granted_points)
    
    # Prueba de riesgo
    def challenge_efficiency(self, risk_points:int, modifiers_points:int):
        if self.points+modifiers_points >= risk_points:
            return True
        return False
    
    def _add_points(self, granted_points):
        if self.points+granted_points <= self.max_points:
            self.points += granted_points
        else:
            self.points = self.max_points
        # print(f"La eficiencia '{self.ID}' tiene ahora {self.points} puntos")   