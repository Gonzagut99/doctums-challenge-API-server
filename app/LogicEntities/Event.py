from dataclasses import dataclass
from typing import List, Tuple, Any
from app.LogicEntities.Efficiency import Efficiency


@dataclass
class Event:
    description: str
    appear_first_in_trimester: int
    required_efficiencies: list
    result_success: Tuple
    result_failure: Tuple
    modifiable_products: list[str] = None #[...eficiency1.modifiable_by_products, ...eficiency2.modifiable_by_products]
    modifiable_projects: list[str] = None
    modifiable_resources: list[str] = None
    ID: int = None
    level: int = None

