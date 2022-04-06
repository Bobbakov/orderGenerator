# Import libraries -->
import itertools

class agent():
    counter = itertools.count()
    agents = []

    # Initialize agent
    def __init__(self, strategy, **params):
        self.name = next(agent.counter)
        
        # Strategy can be picked from strategies.py or strategies_custum.py
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
            
        agent.agents.append(self)            