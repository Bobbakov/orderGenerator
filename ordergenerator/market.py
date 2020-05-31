import itertools
import random
import numpy as np
import operator
from matplotlib import pyplot as plt
import pandas as pd
import time

from .agent import agent
from .order import order
from .strategy import strategies
from .transaction import transaction

class market():
    counter = itertools.count()
    markets = []

    # Initialize market
    def __init__(self, minprice = 1, maxprice = 100, ticksize = 0.05, minquantity = 1, maxquantity = 10):
        self.id = next(market.counter)
        self.transaction_counter = 0
        self.minprice = minprice
        self.maxprice = maxprice
        self.ticksize = ticksize
        self.minquantity = minquantity
        self.maxquantity = maxquantity

        market.markets.append(self)

        # Initialize agents
        self.agents = []

        # Make sure simulations start from same feed --> that way they can be easily compared
        random.seed(100)
        np.random.seed(100)

    # Start agents sending in orders to market(s)
    def orderGenerator(self, n = 1000, clearAt = 10000, printOrderbook = False, sleeptime = 0, all_markets = False):
        c = 1

        # For each iteration
        for o in range(int(n)):
            # For each market
            if all_markets:
                for m in market.markets:
                    # For each agent
                    for a in m.agents:
                        # Take strategy agent
                        strategyAgent = strategies.strategiesDict[a.strategy]["strategy"]

                        # Keep track of last transaction printed
                        if self.id in transaction.history.keys():
                            lastTransactionId = transaction.history[self.id][-1].id
                        else:
                            lastTransactionId = -1

                        # If strategy == simpleArbitrage --> number of markets should be 2.
                        if (a.strategy == "simpleArbitrage"):
                            if (len(market.markets) == 2):
                                m1, m2 = market.markets
                                strategyAgent(a, m1, m2)
                        else:
                            strategyAgent(a, m)

                        if printOrderbook:
                            self.printOrderbook(lastTransactionId)

                            # Slow down printing orderbook
                            time.sleep(float(sleeptime))

                            # If we only generate orders for this market
            else:
                # For each agent
                for a in self.agents:
                    # Take strategy agent
                    strategyAgent = strategies.strategiesDict[a.strategy]["strategy"]

                    # Keep track of last transaction printed
                    if self.id in transaction.history.keys():
                        lastTransactionId = transaction.history[self.id][-1].id
                    else:
                        lastTransactionId = -1

                    # If strategy == simpleArbitrage --> number of markets should be 2.
                    if (a.strategy == "simpleArbitrage"):
                        if (len(market.markets) == 2):
                            m1, m2 = market.markets
                            strategyAgent(a, m1, m2)
                    else:
                        strategyAgent(a, self)

                    if printOrderbook:
                        self.printOrderbook(lastTransactionId)

                        # Slow down printing orderbook
                        time.sleep(float(sleeptime))

                c += 1

                # Clear orderbook at fixed intervals
                if (c % clearAt == 0):
                    self.clear()

    def test(self, n = 1000):
        a1 = agent("randomLogNormal", buy_probability = 0.5)
        a2 = agent("bestBidOffer")
        # a3 = agent("randomLogNormal")
        # a4 = agent("bestBidOffer")
        # a5 = agent("bestBidOffer")
        # agents = [a1, a2, a3, a4, a5]
        agents = [a1, a2]
        self.addAgents(agents)
        self.orderGenerator(n, printOrderbook = False, sleeptime = 0)

    # Initiate a healthy or normal market
    def healthy(self):
        a1 = agent("randomLogNormal", buy_probability = 0.50)
        a2 = agent("bestBidOffer")
        a3 = agent("randomLogNormal")
        a4 = agent("bestBidOffer")
        a5 = agent("bestBidOffer")
        agents = [a1, a2, a3, a4, a5]
        self.addAgents(agents)

    # Initiate a stressed market (= high volatility)
    def stressed(self):
        a1 = agent("randomLogNormal")
        a2 = agent("randomLogNormal")
        a3 = agent("randomLogNormal")
        a4 = agent("randomLogNormal")
        a5 = agent("randomLogNormal")
        agents = [a1, a2, a3, a4, a5]
        self.addAgents(agents)

    # Initiate a trending (up) market
    def trendUp(self):
        a1 = agent("randomLogNormal", buy_probability = 0.55)
        a2 = agent("bestBidOffer")
        a3 = agent("randomLogNormal")
        a4 = agent("bestBidOffer")
        a5 = agent("bestBidOffer")
        agents = [a1, a2, a3, a4, a5]
        self.addAgents(agents)

    # Initiate a trending (down) market
    def trendDown(self):
        a1 = agent("randomLogNormal", buy_probability = 0.45)
        a2 = agent("bestBidOffer")
        a3 = agent("randomLogNormal")
        a4 = agent("bestBidOffer")
        a5 = agent("bestBidOffer")
        agents = [a1, a2, a3, a4, a5]
        self.addAgents(agents)

    ###############################################################################
    # MARKET: SUPPORTING FUNCTIONS
    ###############################################################################
    def __str__(self):
        return "{}".format(self.id)

        # Add your agents to the market

    def addAgents(self, agents):
        for a in agents:
            self.agents.append(a)

            # Empty active orders

    def clear(self):
        order.activeBuyOrders[self.id] = []
        order.activeSellOrders[self.id] = []

    # Get last order
    def getLastOrder(self):
        # If market has been activated --> get last order
        if self.id in order.historyIntialOrder.keys():
            lastOrderDictId = max(order.historyIntialOrder[self.id].keys())
            lastOrder = order.historyIntialOrder[self.id][lastOrderDictId]
        # Else --> return 0
        else:
            lastOrder = 0

        return lastOrder

    # Print last transactions
    def printLastTransactions(self, lastTransactionId, number_transactions = 5):
        if self.id in transaction.history.keys():
            for t in transaction.history[self.id][-number_transactions:]:
                if t.id > lastTransactionId:
                    print("--> Trade at price {} (quantity = {})".format(t.price, t.quantity))
                    # last_transaction_id = x.id

    def printOrderbook(self, lastTransactionId = -1):
        last_order = market.getLastOrder(self)

        # Print last order
        print("Last order: \n{} with price {} (quantity = {})".format(last_order["side"], last_order["price"],
                                                                      last_order["quantity"]))

        # Print last transactions
        market.printLastTransactions(self, lastTransactionId)

        # Print orderbook
        self.showOrderbook()

        # Plot price over time

    def plotPrice(self, skip_transactions = 20, first = 0, last = 999999):
        df = pd.DataFrame(transaction.historyList[self.id], columns = ["id", "time", "price"])
        df = df[["id", "price"]]
        df = df[(df["id"] > first) & (df["id"] < last)]
        df = df[df["id"] > skip_transactions]
        df = df.set_index("id")

        return df.plot()

        # Plot price over time on all markets in one graph

    def plotPriceAllMarkets(self, skip_transactions = 20, first = 0, last = 999999):
        for m in market.markets:
            df = pd.DataFrame(transaction.historyList[m.id], columns = ["id", "time", "price"])
            df = df[["id", "price"]]
            df = df[(df["id"] > first) & (df["id"] < last)]
            df = df[df["id"] > skip_transactions]
            df = df.set_index("id")
            plt.plot(df, label = "{}".format(m.id))
        plt.legend()

        return plt.show()

    # Plot position (+ profits) all agents
    def plotPositions(self, agents = []):
        if len(agents) == 0:
            agents = [a.name for a in self.agents]
        for a in self.agents:
            if a.name in agents:
                df = pd.DataFrame(transaction.historyMarketAgent[self.id, a.name],
                                  columns = ["id", "runningPosition", "runningProfit"])
                df = df.set_index("id")
                rPosition = df["runningPosition"]
                plt.plot(rPosition, label = "{} ({})".format(str(a.name), a.strategy),
                         linestyle = strategies.strategiesDict[a.strategy]["linestyle"])
                plt.plot()
        plt.legend()

        return plt.show()

    # Plot profitsall agents
    def plotProfits(self, agents = []):
        if len(agents) == 0:
            agents = [a.name for a in self.agents]
        for a in self.agents:
            if a.name in agents:
                df = pd.DataFrame(transaction.historyMarketAgent[self.id, a.name],
                                  columns = ["id", "runningPosition", "runningProfit"])
                df = df.set_index("id")
                rProfit = df["runningProfit"]
                plt.plot(rProfit, label = "{} ({}) runningProfit".format(str(a.name), a.strategy),
                         linestyle = strategies.strategiesDict[a.strategy]["linestyle"])
                plt.plot()
        plt.legend()
        return plt.show()

    def plotPricePositions(self, agents = []):
        if len(agents) == 0:
            agents = [a.name for a in self.agents]
        # Plot price
        fig, ax1 = plt.subplots()
        ax1.set_xlabel('transctionNumber')
        ax1.set_ylabel('Price')
        df = pd.DataFrame(transaction.historyList[self.id], columns = ["id", "time", "price"])
        df[["id", "price"]]
        df = df.set_index("id")
        ax1.plot(df.index, df["price"])
        ax1.tick_params(axis = 'y')

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        ax2.set_ylabel('Position')  # we already handled the x-label with ax1
        for a in self.agents:
            if a.name in agents:
                df = pd.DataFrame(transaction.MarketAgent[self.id, a.name],
                                  columns = ["id", "runningPosition", "runningProfit"])
                df = df.set_index("id")
                ax2.plot(df.index, df["runningPosition"],
                         linestyle = strategies.strategiesDict[a.strategy]["linestyle"])
        ax2.tick_params(axis = 'y')

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        return plt.show()

    def plotOrdersTrades(self):
        # Times of order entry
        orderTimes = [o.datetime for o in order.history[self.id]]
        orderTimes = pd.DataFrame(orderTimes)

        # Times of transaction
        tradeTimes = [[t.datetime, t.price] for t in transaction.history[self.id]]
        tradeTimes = pd.DataFrame(tradeTimes)

        # combined
        combined = pd.merge(orderTimes, tradeTimes, on = 0, how = "left")
        combined = combined.set_index(0)

        return combined.plot()

        # Plot price, volatility, positions and profits

    def summary(self):
        df = pd.DataFrame(transaction.historyList[self.id], columns = ["id", "time", "price"])
        df["volatility"] = df["price"].rolling(7).std()
        df["volatilityTrend"] = df["volatility"].rolling(100).mean()
        df = df[["id", "price", "volatility", "volatilityTrend"]]
        df = df.set_index("id")

        dfPrice = df["price"]
        dfVolatility = df[["volatility", "volatilityTrend"]]

        # PLOT PRICE
        fig, axs = plt.subplots(2, 2)
        axs[0, 0].plot(dfPrice, label = "price")
        axs[0, 0].set_title("Price")
        axs[0, 0].legend()

        # PLOT VOLATILITY
        axs[0, 1].plot(dfVolatility)
        axs[0, 1].set_title("Volatility")
        axs[0, 1].legend()

        # PLOT RUNNING POSITIONS + RUNNING PROFITS AGENTS
        for a in self.agents:
            right = pd.DataFrame(transaction.historyMarketAgent[self.id, a.name],
                                 columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[a.name]
            axs[1, 0].plot(right, label = str(a.name))
        axs[1, 0].set_title("Positions")

        if len(self.agents) < 20:
            axs[1, 0].legend()

        for a in self.agents:
            right = pd.DataFrame(transaction.historyMarketAgent[self.id, a.name],
                                 columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[str(a.name) + "RunningProfit"]
            axs[1, 1].plot(right, label = str(a.name) + "RunningProfit")

        axs[1, 1].set_title("Running profit")

        return plt.show()

        # SHOW ORDERBOOK RAW VERSION

    def showOrderbook(self, show_depth = 10):
        widthOrderbook = len("0       Bert    Buy     33      5")
        print(widthOrderbook * 2 * "*")

        if self.id in order.activeSellOrders.keys():
            for sellOrder in sorted(order.activeSellOrders[self.id], key = operator.attrgetter("price"),
                                    reverse = True)[:show_depth]:
                print(widthOrderbook * "." + " " + str(sellOrder))
        if self.id in order.activeBuyOrders.keys():
            for buyOrder in sorted(order.activeBuyOrders[self.id], key = operator.attrgetter("price"), reverse = True)[
                            :show_depth]:
                print(str(buyOrder) + " " + widthOrderbook * ".")

        print(widthOrderbook * 2 * "*")
        print(" ")

    # SHOW ORDERBOOK GRAPHICALLY
    def showOrderbookH(self):
        buyOrders = []
        for b in order.activeBuyOrders[self.id]:
            for o in range(b.quantity):
                buyOrders.append(b.price)

        sellOrders = []
        for of in order.activeSellOrders[self.id]:
            for o in range(of.quantity):
                sellOrders.append(of.price)

        plt.hist(buyOrders, bins = 100, color = "green")
        plt.hist(sellOrders, bins = 100, color = "red")

        return plt.show()