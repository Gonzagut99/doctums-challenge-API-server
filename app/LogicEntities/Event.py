from dataclasses import dataclass
from typing import List, Tuple, Any
from app.LogicEntities.Efficiency import Efficiency


@dataclass
class Event:
    description: str
    appear_first_in_trimester: int
    required_efficiencies: List
    result_success: Tuple
    result_failure: Tuple
    modifiable_products: List = None #[...eficiency1.modifiable_by_products, ...eficiency2.modifiable_by_products]
    modifiable_projects: List = None
    modifiable_resources: List = None
    ID: int = None
    level: int = None

