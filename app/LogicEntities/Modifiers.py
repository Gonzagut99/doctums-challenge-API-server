from dataclasses import dataclass
from typing import List, Tuple, Any

@dataclass
class Modifier:
    name: str
    cost: int
    ID: int
    points_to_grant: int
    purchased_on: int = 0

@dataclass
class Product(Modifier):
    points_to_grant: int = 1
    requirements: List[str] = None
    able_to_grant_points: bool = True
    is_purchased: bool = True

@dataclass
class Project(Modifier):
    points_to_grant: int = 5
    delivered_products: List = None
    able_to_grant_points: bool = True
    start_datum: Any = None
    project_length: int = 3  # standard is 3 months
    remaining_months: int = project_length
    
    def update_remaining_months(self, current_month):
        self.remaining_months = self.project_length - (current_month - self.start_datum)

    def is_finished(self, current_month):
        if current_month - self.project_length > self.start_datum and current_month >= self.start_datum:
            self.remaining_months = 0
            return True
        return False


@dataclass
class Resource(Modifier):
    points_to_grant: int = 3
    developed_products: List = None
    able_to_grant_points: bool = True
    monthly_salary: int = 0
    start_datum: Any = None
    resource_lenght: int = 1
    remaining_time: int = resource_lenght
    
    def update_remaining_time(self, current_month):
        self.remaining_time = self.resource_lenght - (current_month - self.start_datum)
    
    def is_finished(self, current_month):
        if current_month - self.resource_lenght > self.start_datum and current_month >= self.start_datum:
            self.remaining_time = 0
            return True
        return False
    