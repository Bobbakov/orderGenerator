# Import libraries -->
import itertools

# Initialize variables -->
counter = itertools.count()
agents = []

class create_agent():
    # Initialize agent
    def __init__(self, strategy, **params):
        self.name = next(counter)
        
        # Strategy can be picked from strategies.py
        self.strategy = strategy
        self.params = params

        # STARTS WITH EMPTY VALUES
        self.position = {}
        self.running_profit = {}
        self.value_bought = {}
        self.quantity_bought = {}
        self.value_sold = {}
        self.quantity_sold = {}
        self.stop = {}
            
        agents.append(self)            