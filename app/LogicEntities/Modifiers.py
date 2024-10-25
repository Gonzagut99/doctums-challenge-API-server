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
    start_datum: Any = None
    able_to_grant_points: bool = True
    project_length: int = 3  # standard is 3 months

    def is_finished(self, actual_month):
        if actual_month - self.project_length > self.start_datum and actual_month >= self.start_datum:
            return True
        return False 


@dataclass
class Resource(Modifier):
    points_to_grant: int = 3
    developed_products: List = None
    able_to_grant_points: bool = True
    monthly_salary: int = 0
    