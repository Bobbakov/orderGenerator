import itertools

class transaction():
    counter = itertools.count()
    history = {}
    historyList = {}
    historyMarketAgent = {}

    # Initialize transaction
    def __init__(self, buyOrder, sellOrder, market, price, quantity):
        market.transaction_counter += 1
        self.id = market.transaction_counter

        # If transaction is buyer initiated --> take buyOrder.datetime == trade time.
        # Else --> take sellOrder.datetime
        self.datetime = max(buyOrder.datetime, sellOrder.datetime)
        self.market = market
        self.buyOrder = buyOrder
        self.sellOrder = sellOrder
        self.price = price
        self.quantity = quantity

        # If first transaction by agent at market --> initialize values
        if not market.id in buyOrder.agent.position.keys():
            buyOrder.agent.position[market.id] = 0
            buyOrder.agent.valueBought[market.id] = 0
            buyOrder.agent.quantityBought[market.id] = 0
            buyOrder.agent.valueSold[market.id] = 0
            buyOrder.agent.quantitySold[market.id] = 0

        if not market.id in sellOrder.agent.position.keys():
            sellOrder.agent.position[market.id] = 0
            sellOrder.agent.valueBought[market.id] = 0
            sellOrder.agent.quantityBought[market.id] = 0
            sellOrder.agent.valueSold[market.id] = 0
            sellOrder.agent.quantitySold[market.id] = 0

        if not market.id in transaction.history.keys():
            transaction.history[market.id] = []
            transaction.historyList[market.id] = []

        if not (market.id, buyOrder.agent.name) in transaction.historyMarketAgent.keys():
            transaction.historyMarketAgent[market.id, buyOrder.agent.name] = []

        if not (market.id, sellOrder.agent.name) in transaction.historyMarketAgent.keys():
            transaction.historyMarketAgent[market.id, sellOrder.agent.name] = []

            # Update values agents at market
        buyOrder.agent.position[market.id] += quantity
        sellOrder.agent.position[market.id] -= quantity
        buyOrder.agent.valueBought[market.id] += price * quantity
        buyOrder.agent.quantityBought[market.id] += quantity
        sellOrder.agent.valueSold[market.id] += price * quantity
        sellOrder.agent.quantitySold[market.id] += quantity

        # Add to transaction history
        transaction.history[market.id].append(self)
        transaction.historyList[market.id].append([self.id, self.datetime.time(), self.price])

        # Add to history agent at market
        transaction.historyMarketAgent[market.id, buyOrder.agent.name].append([self.id,
                                                                               buyOrder.agent.position[market.id],
                                                                               transaction.calculateRprofit(
                                                                                   buyOrder.agent, market)])
        transaction.historyMarketAgent[market.id, sellOrder.agent.name].append([self.id,
                                                                                sellOrder.agent.position[market.id],
                                                                                transaction.calculateRprofit(
                                                                                    sellOrder.agent, market)])

    ###############################################################################
    # TRANSACTION: SUPPORTING FUNCTIONS
    ###############################################################################
    # Display transaction
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {} \t {} \t {}".format(self.id, self.datetime.time(), self.market,
                                                               self.buyOrder.agent.name, self.sellOrder.agent.name,
                                                               self.price, self.quantity)

        # Calculate realized profit agent at market

    def calculateRprofit(agent, market):
        if agent.quantitySold[market.id] > 0:
            askVwap = agent.valueSold[market.id] / agent.quantitySold[market.id]
        else:
            askVwap = 0
        if agent.quantityBought[market.id] > 0:
            bidVwap = agent.valueBought[market.id] / agent.quantityBought[market.id]
        else:
            bidVwap = 0

        q = min(agent.quantitySold[market.id], agent.quantityBought[market.id])
        rp = q * (askVwap - bidVwap)
        return rp

    def transactionDescription(bid, offer, market, price, quantity):
        return print(
            "At market {} - Best bid: {} ({}) Best offer: {} ({}) --> Transaction at: {} ({})".format(market.id,
                                                                                                      bid.price,
                                                                                                      bid.quantity,
                                                                                                      offer.price,
                                                                                                      offer.quantity,
                                                                                                      price, quantity))
