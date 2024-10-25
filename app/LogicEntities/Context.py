
import itertools
import numpy as np
from operator import itemgetter
from app.utils.data_loader import load_products, load_projects, load_resources, load_efficiencies, load_events, load_legacy


class Context:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.PRODUCTS = None
        self.PROJECTS = None
        self. RESOURCES = None
        self. EFFICIENCIES = None
        self.EVENTS = None
        self. LEGACY = None
        self.load_data()
        self.board = self.load_bord()


    def load_data(self):
        data_dir = self.data_dir
        products_path = data_dir.joinpath("products.csv")
        projects_path = data_dir.joinpath("projects.csv")
        resources_path = data_dir.joinpath("resources.csv")
        efficiencies_path = data_dir.joinpath("efficiencies.csv")
        events_path = data_dir.joinpath("events.csv")
        legacy_path = data_dir.joinpath("legacy.csv")

        self.PRODUCTS = load_products(products_path)
        self.PROJECTS = load_projects(projects_path)
        self.RESOURCES = load_resources(resources_path)
        self.EFFICIENCIES = load_efficiencies(efficiencies_path)
        self.EVENTS = load_events(events_path)
        self.LEGACY = load_legacy(legacy_path)
        
        # add modifiers to its respective events according to the required efficiencies
        for event in self.EVENTS.values():
            required_efficiencies = list(itemgetter(*event.required_efficiencies)(self.EFFICIENCIES))            
            
            modifiable_products = [required_efficiency.modifiable_by_products for required_efficiency in required_efficiencies]
            modifiable_projects = [required_efficiency.modifiable_by_projects for required_efficiency in required_efficiencies]
            modifiable_resources = [required_efficiency.modifiable_by_resources for required_efficiency in required_efficiencies]            
            
            event.modifiable_products = list(itertools.chain(*modifiable_products))
            event.modifiable_projects = list(itertools.chain(*modifiable_projects))
            event.modifiable_resources = list(itertools.chain(*modifiable_resources))

    def load_bord(self):
        board_path = self.data_dir.joinpath("board.csv")
        board = []
        with open(board_path) as f:
            content = f.read().splitlines()
            for line in content[1:]: # skip day of month
                board.append(line.split(";")[1:])  # skip month name
        return np.array(board, dtype=int)
