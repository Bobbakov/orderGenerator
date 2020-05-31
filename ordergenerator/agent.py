import itertools

from .transaction import transaction

class agent():
    counter = itertools.count()
    agents = []

    # Initialize agent
    def __init__(self, strategy, **params):
        self.name = next(agent.counter)
        self.strategy = strategy
        self.params = params

        # STARTS WITH EMPTY VALUES
        self.position = {}
        self.runningProfit = {}

        self.valueBought = {}
        self.quantityBought = {}
        self.valueSold = {}
        self.quantitySold = {}

        self.stop = {}

        agent.agents.append(self)

    # If price has been printed in market --> return last price. Else --> return mid price
    def getLastPriceOrElse(market):
        if market.id in transaction.history.keys():
            p = transaction.history[market.id][-1].price
        else:
            p = (market.maxprice - market.minprice) / 2
        return p
