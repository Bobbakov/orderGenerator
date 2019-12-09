###############################################################################
# IMPORT REQUIRED LIBRARIES
###############################################################################
from datetime import datetime
import itertools

# IMPORT random + numpy 
# SET random.seed values = 100 --> SAME RANDOM SEQUENCES GERENATED EACH TIME
import random
import numpy as np

import operator
from matplotlib import pyplot as plt
import pandas as pd    
import seaborn as sns

# SET DEFAULT FIGURE SIZE
sns.set(rc={'figure.figsize':(20, 10)})

import time
###############################################################################
# ORDER: SUPPORTING FUNCTIONS FOR ORDER
###############################################################################
# Remove offer from orderbook
def removeOffer(offer, market):
    a = order.activeSellOrders[market.id]
    for c, o in enumerate(a):
        if o.id == offer.id:
            del a[c]
            break

# Reduce quantity offer in orderbook
def reduceOffer(offer, transactionQuantity, market):
    a = order.activeSellOrders[market.id]
    for c, o in enumerate(a):
        if o.id == offer.id:
            if a[c].quantity == transactionQuantity:
                removeOffer(offer, market)
            else:
                a[c].quantity -= transactionQuantity
            break

# Remove bid from orderbook
def removeBid(bid, market):
    a = order.activeBuyOrders[market.id]
    for c, o in enumerate(a):
        if o.id == bid.id:
            del a[c]
            break  
        
# Reduce quantity bid in orderbook
def reduceBid(bid, transactionQuantity, market):
    a = order.activeBuyOrders[market.id]
    for c, o in enumerate(a):
        if o.id == bid.id:
            if a[c].quantity == transactionQuantity:
                removeBid(bid, market)
            else:
               a[c].quantity -= transactionQuantity
            break

# If price has been printed in market --> return last price. Else --> return mid price
def getLastPriceOrElse(market):
    if market.id in transaction.historyRaw.keys():
        p = transaction.historyRaw[market.id][-1].price 
    else:
        p = (market.maxprice - market.minprice)/2             
    return p

###############################################################################
# ORDER
###############################################################################
class order():
    counter = itertools.count()
    history = {}
    activeOrders = {}
    activeBuyOrders = {}
    activeSellOrders = {}
    
    # Initialize order
    def __init__(self, market, agent, side, price, quantity):
        self.id = next(order.counter)
        self.datetime = datetime.now()
        self.market = market
        self.agent = agent
        self.side = side
        self.price = price
        self.quantity = quantity
        
        # If order is first order in a market --> create orderbook
        if not market.id in order.history.keys():
            order.history[market.id] = []
            order.activeOrders[market.id] = []
            order.activeBuyOrders[market.id] = []
            order.activeSellOrders[market.id] = []
        
        # Add order to order history
        order.history[market.id].append(self)
        
        # Check if order results in transaction
        # If order is buy order
        if self.side == "Buy":
        
            # start loop
            remainingQuantity = self.quantity
            while True:
                # If there are active sell orders --> continue
                if not not order.activeSellOrders[market.id]:
                    sellOrders = sorted(order.activeSellOrders[market.id], key = operator.attrgetter("price"))
                    bestOffer = sellOrders[0]
                    
                    # If limit price buy order >= price best offer --> transaction
                    if self.price >= bestOffer.price:
                        transactionPrice = bestOffer.price
                        
                        # If quantity buy order larger quantity than best offer --> remove best offer from active orders
                        if remainingQuantity > bestOffer.quantity:
                            transactionQuantity = bestOffer.quantity
                            
                            # Register transaction
                            transaction(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            # Remove offer from orderbook
                            removeOffer(bestOffer, market)  
                            
                            # Reduce remaining quantity order
                            remainingQuantity -= transactionQuantity

                        # If quantity buy order equals quantity best offer    
                        elif remainingQuantity == bestOffer.quantity:
                            transactionQuantity = bestOffer.quantity
                            
                            # Register transaction
                            transaction(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            # Remove offer from orderbook
                            removeOffer(bestOffer, market) 

                            # Buy order is executed --> break loop
                            break       
                        # if quantity buy order is small than quantity best offer --> reduce quantity best offer
                        else:
                            transactionQuantity = remainingQuantity
                            
                            # Register transaction
                            transaction(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            # Reduce quantity offer
                            reduceOffer(bestOffer, transactionQuantity, market)
                            
                            # Buy order is executed --> break loop
                            break
                            
                    # If bid price < best offer --> no transaction    
                    else:
                        self.quantity = remainingQuantity
                        
                        # Send order to orderbook
                        order.activeOrders[market.id].append(self)
                        order.activeBuyOrders[market.id].append(self)
                        break
                    
                # If there are NO active sell orders --> add order to active orders        
                else:
                    self.quantity = remainingQuantity
                    order.activeOrders[market.id].append(self)
                    order.activeBuyOrders[market.id].append(self)
                    break
                
        # If order is sell order                  
        else:
            
            # start loop
            remainingQuantity = self.quantity
            while True:
                    # if there are active buy orders --> continue
                    if not not order.activeBuyOrders[market.id]:
                        buyOrders = sorted(order.activeBuyOrders[market.id], key = operator.attrgetter("price"), reverse = True)
                        bestBid = buyOrders[0]
                        # If price sell order <= price best bid --> transaction
                        if bestBid.price >= self.price:
                            transactionPrice = bestBid.price
                            
                            # If quantity offer larger than quantity best bid
                            if remainingQuantity > bestBid.quantity:
                                transactionQuantity = bestBid.quantity
                                
                                # Register transaction
                                transaction(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                # Remove bid from orderbook
                                removeBid(bestBid, market)    
                                
                                remainingQuantity -= transactionQuantity
                              # If quantity order equals quantity best offer    
                            elif remainingQuantity == bestBid.quantity:
                                transactionQuantity = bestBid.quantity
                                
                                # Register transaction
                                transaction(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                # Remove best bid from orderbook
                                removeBid(bestBid, market) 
    
                                # Order is executed --> break loop
                                break       
                            
                            # If quantity sell order is smaller than quantity best bid
                            else:
                                transactionQuantity = remainingQuantity
                                
                                # Register transaction
                                transaction(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                # Reduce quantity best bid
                                reduceBid(bestBid, transactionQuantity, market)
                                break
                            
                        # If best offer price > best bid price --> no transaction     
                        else:
                            self.quantity = remainingQuantity
                            order.activeOrders[market.id].append(self)
                            order.activeSellOrders[market.id].append(self)
                            break
                        
                    # If there are no active buy orders --> add order to active orders         
                    else: 
                        self.quantity = remainingQuantity
                        order.activeOrders[market.id].append(self)
                        order.activeSellOrders[market.id].append(self)
                        break
                
            
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {}".format(self.market, self.agent.name, self.side, self.price, self.quantity)

###############################################################################
# TRANSACTION: SUPPORTING FUNCTIONS FOR TRANSACTIONS
###############################################################################
def transactionDescription(bid, offer, market, price, quantity):
    return print("At market {} - Best bid: {} ({}) Best offer: {} ({}) --> Transaction at: {} ({})".format(market.id, bid.price, bid.quantity, 
                 offer.price, offer.quantity, price, quantity))

###############################################################################
# TRANSACTION
###############################################################################
class transaction():
    counter = itertools.count()
    historyRaw = {}
    historyList = {}
    MarketAgent = {}
    
    # Initialize transaction
    def __init__(self, buyOrder, sellOrder, market, price, quantity):
        self.id = next(transaction.counter)
        self.datetime = datetime.now()
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
        
        if not market.id in transaction.historyRaw.keys():
            transaction.historyRaw[market.id] = []
            transaction.historyList[market.id] = []
            
        if not (market.id, buyOrder.agent.name) in transaction.MarketAgent.keys():
            transaction.MarketAgent[market.id, buyOrder.agent.name] = []
            
        if not (market.id, sellOrder.agent.name) in transaction.MarketAgent.keys():
            transaction.MarketAgent[market.id, sellOrder.agent.name] = []    
        
        # Update values agents at market
        buyOrder.agent.position[market.id] += quantity
        sellOrder.agent.position[market.id] -= quantity
        buyOrder.agent.valueBought[market.id] += price * quantity
        buyOrder.agent.quantityBought[market.id] += quantity
        sellOrder.agent.valueSold[market.id] += price * quantity
        sellOrder.agent.quantitySold[market.id] += quantity            
        
        # Add to transaction history
        transaction.historyRaw[market.id].append(self)
        transaction.historyList[market.id].append([self.id, self.datetime.time(), self.price])
        
        # Add to history agent at market
        transaction.MarketAgent[market.id, buyOrder.agent.name].append([self.id, 
                               buyOrder.agent.position[market.id], 
                               calculateRprofit(buyOrder.agent, market)])
        transaction.MarketAgent[market.id, sellOrder.agent.name].append([self.id, 
                               sellOrder.agent.position[market.id], 
                               calculateRprofit(sellOrder.agent, market)])
    
    # Display transaction
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {} \t {} \t {}".format(self.id, self.datetime.time(), self.market, self.buyOrder.agent.name, self.sellOrder.agent.name, self.price, self.quantity)        
    
###############################################################################
# SUPPORTING FUNCTIONS AGENT
###############################################################################  
# Calculate realized profit agent at market        
def calculateRprofit(self, market):
    if self.quantitySold[market.id] > 0:
        askVwap = self.valueSold[market.id]/self.quantitySold[market.id]
    else:
        askVwap = 0
    if self.quantityBought[market.id] > 0:
        bidVwap = self.valueBought[market.id]/self.quantityBought[market.id]
    else:
        bidVwap = 0
        
    q = min(self.quantitySold[market.id], self.quantityBought[market.id])
    rp = q * (askVwap - bidVwap)
    return rp     


###############################################################################
# AGENTS: TRADING STRATEGIES
###############################################################################
###############################################################################
# AGENTS: RANDOM AGENTS
###############################################################################      
# Randomly choose Buy/Sell order with both quantity and price from uniform distribution
def randomUniform(self, market):
    side = random.choice(["Buy", "Sell"])
    price = np.arange(market.minprice, market.maxprice, market.ticksize)
    price = np.random.choice(price)
    quantity = random.randint(market.minquantity, market.maxquantity)
    
    # Send order to market
    order(market, self, side, price, quantity)

# Randomly choose Buy/Sell order with price from normal distribution      
def randomNormal(self, market):
    side = random.choice(["Buy", "Sell"])
    
    lastPrice = getLastPriceOrElse(market)
    std = 0.1 * lastPrice
    price = np.random.normal(lastPrice, std)
    quantity = random.randint(market.minquantity, market.maxquantity)
    
    # Send order to market
    order(market, self, side, price, quantity)    

# Randomly choose Buy/Sell order with price from lognormal distribution          
def randomLogNormal(self, market):
    side = random.choice(["Buy", "Sell"])

    lastPrice = getLastPriceOrElse(market)
    
    price = lastPrice * np.random.lognormal(0, 0.2)
    # Correct for ticksize market
    price = round(price/market.ticksize) * market.ticksize
    quantity = random.randint(market.minquantity, market.maxquantity)
    
    # Send order to market
    order(market, self, side, price, quantity)    

###############################################################################
# AGENTS: MARKET MAKER
############################################################################### 
# Agents always tries to be best bid and best offer at market. If he is not --> he improves price by 1 tick.
# If position limit is exceeded --> agent closes position at market (in case position > 0) or buys back all shorts (in case position < 0)
def bestBidOffer(self, market):
    quantity = random.randint(market.minquantity, market.maxquantity)
    
    # If agent has position_limit --> check if limit is exceeded    
    if "position_limit" in self.parameters.keys(): 
        position_limit = self.parameters["position_limit"]
        
        if market.id in self.position.keys():
            if self.position[market.id] > position_limit:
                order(market, self, "Sell", market.minprice, abs(self.position[market.id]))  
            elif self.position[market.id] < - position_limit:
                order(market, self, "Buy", market.maxprice, abs(self.position[market.id]))  
            
    # If there are active buy orders --> improve best bid by one tick
    if market.id in order.activeBuyOrders.keys():
        if not not order.activeBuyOrders[market.id]:
            buyOrders = sorted(order.activeBuyOrders[market.id], key = operator.attrgetter("price"), reverse = True)
            bestBid = buyOrders[0]
            
            # If trader is not best bid --> improve best bid
            if not bestBid.agent.name == self.name:
                order(market, self, "Buy", bestBid.price + market.ticksize, quantity)    
            else:
                pass
        # Else --> create best bid    
        else:
            order(market, self, "Buy", market.minprice, quantity)
    # If no buy orders active in market --> start the market
    else:
        order(market, self, "Sell", market.maxprice, quantity)
    
    # If there are active sell orders --> improve best offer by one tick
    if market.id in order.activeSellOrders.keys():
        if not not order.activeSellOrders[market.id]:
            sellOrders = sorted(order.activeSellOrders[market.id], key = operator.attrgetter("price"))
            bestOffer = sellOrders[0]
            
            # If trader is not best offer --> improve best offer
            if not bestOffer.agent.name == self.name:
                order(market, self, "Sell", bestOffer.price - market.ticksize, quantity)    
            else:
                pass
        # Else --> create best bid    
        else:
            order(market, self, "Sell", market.maxprice, quantity) 
    else:
        # If no sell orders active in market --> start the market
        order(market, self, "Sell", market.maxprice, quantity)
  
###############################################################################
# AGENTS: ARBITRAGE (BETWEEN MARKETS)
###############################################################################         
# Agent buys bestOffer at MarketB if its price is lower than bestBid at marketA. 
# He simultenously sells to bestBid at marketA.
# The same goes the other way around.        
def simpleArbitrage(self, marketA, marketB):
    # If marketA is initiated
    if marketA.id in order.activeBuyOrders.keys():
        # If there are active buy orders
        if not not order.activeBuyOrders[marketA.id]:
            # If marketB is initiated
            if marketB.id in order.activeSellOrders.keys(): 
                # If there are active sell orders
                if not not order.activeSellOrders[marketB.id]:
                    buyOrdersMarketA = sorted(order.activeBuyOrders[marketA.id], key = operator.attrgetter("price"), reverse = True)
                    bestBidMarketA = buyOrdersMarketA[0]
                    
                    sellOrdersMarketB = sorted(order.activeSellOrders[marketB.id], key = operator.attrgetter("price"), reverse = False)
                    bestOfferMarketB = sellOrdersMarketB[0]
                    
                    if bestBidMarketA.price > bestOfferMarketB.price:
                        order(marketB, self, "Buy", bestOfferMarketB.price, bestOfferMarketB.quantity)
                        order(marketA, self, "Sell", bestBidMarketA.price, bestBidMarketA.quantity)
    # The other way around                        
    if marketA.id in order.activeSellOrders.keys(): 
        if not not order.activeSellOrders[marketA.id]: 
            if marketB.id in order.activeBuyOrders.keys(): 
                if not not order.activeBuyOrders[marketB.id]:
                    sellOrdersMaketA = sorted(order.activeSellOrders[marketA.id], key = operator.attrgetter("price"), reverse = False)
                    bestOfferMarketA = sellOrdersMaketA[0]
                    
                    buyOrdersMarketB = sorted(order.activeBuyOrders[marketB.id], key = operator.attrgetter("price"), reverse = True)
                    bestBidMarketB = buyOrdersMarketB[0]
                    
                    if bestBidMarketB.price > bestOfferMarketA.price:
                        order(marketA, self, "Buy", bestOfferMarketA.price, bestOfferMarketA.quantity)
                        order(marketB, self, "Sell", bestBidMarketB.price, bestBidMarketB.quantity)

###############################################################################
# AGENTS: ADD strategies TO ARRAY
############################################################################### 
strategies = [randomUniform, randomNormal, randomLogNormal, bestBidOffer, simpleArbitrage]
strategiesDict = dict(zip(range(0, len(strategies)), strategies))
###############################################################################
# AGENT
###############################################################################      

class agent():  
    counter = itertools.count()
    
    # Initialize agent
    def __init__(self, strategy, **parameters): 
        self.name = next(agent.counter)
        self.strategy = strategy
        self.parameters = parameters
        
        # STARTS WITH EMPTY VALUES
        self.position = {}
        self.runningProfit = {}
        
        self.valueBought = {}
        self.quantityBought = {}
        self.valueSold = {}
        self.quantitySold = {}  
        
###############################################################################
# MARKET
############################################################################### 
class market():
    counter = itertools.count()
    markets = []
       
    # Initialize market
    def __init__(self, minprice = 1, maxprice = 100, ticksize = 0.05, minquantity = 1, maxquantity = 10):
        self.id = next(market.counter)
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
    
    def __str__(self):
        return "{}".format(self.id)    
 
    # Add your agents to the market     
    def addAgents(self, agents):
        for a in agents:
            self.agents.append(a)
  
    # Start agents sending in orders to market(s)
    def orderGenerator(self, n = 5000, clearAt = 10000, printOrderbook = False, sleeptime = 0):
        c = 1
                 
        # For each iteration
        for o in range(int(n)):   
            # For each market
            for m in market.markets:
                # For each agent
                for a in m.agents:
                    # Take strategy agent
                    strategyAgent = strategiesDict[a.strategy] 
                    
                    # If strategy == simpleArbitrage --> number of markets should be 2.
                    if (a.strategy == 4):
                        if (len(market.markets) == 2): 
                            m1, m2 = market.markets
                            strategyAgent(a, m1, m2)
                    else:
                        strategyAgent(a, m)
                    
                c+= 1
                
                # Clear orderbook at fixed intervals
                if (c%clearAt == 0):
                    self.clear()   
                
                # Print orderbook in progress    
                if printOrderbook:
                    print("Iteration {}".format(c))
                    
                    if self.id in transaction.historyRaw.keys():
                        
                        # Print last five transactions
                        for x in transaction.historyRaw[self.id][-5:]:
                            print("Trade {}: {} buys {} from {} for {}".format(x.id, x.buyOrder.agent.name, x.quantity, x.sellOrder.agent.name, x.price))
                        
                    self.showOrderbook()
                    
                    # Slow down printing orderbook
                    time.sleep(float(sleeptime))
            
    # Empty active orders        
    def clear(self):
        order.activeBuyOrders[self.id] = []
        order.activeSellOrders[self.id] = []
    
    # Plot price + running volatility
    def plot(self):
        df = pd.DataFrame(transaction.historyList[self.id], columns = ["id", "time", "price"])
        df[["id", "price"]]
        df = df.set_index("id")
        return df.plot() 
        
    def plotPositionAgentMarket(agentName, market):
        # Plot position agent at market
        df = pd.DataFrame(transaction.MarketAgent[market.id, agentName], columns = ["id", agentName, str(agentName) + "RunningProfit"])
        df = df.set_index("id")
        df = df[agentName]
        plt.plot(df, label = str(agentName))
        plt.legend()

        return plt.show()
    
    # Plot position all agents
    def plotPositions(self):
        for a, s in self.agents:
            right = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[a.name]
            plt.plot(right, label = str(a.name))
            plt.legend()

        return plt.show()
    
    # Plot profits all agents
    def plotProfits(self):
        for a, s in self.agents:
            right = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[str(a.name) + "RunningProfit"]
            plt.plot(right, label = str(a.name) + "RunningProfit")
            plt.legend()

        return plt.show()
    
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
            right = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[a.name]
            axs[1, 0].plot(right, label = str(a.name))
        axs[1, 0].set_title("Positions")  
        if len(self.agents) < 20:
            axs[1, 0].legend()
        
        for a in self.agents:
            right = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[str(a.name) + "RunningProfit"]
            axs[1, 1].plot(right, label = str(a.name) + "RunningProfit")
        
        axs[1, 1].set_title("Running profit")

        return plt.show()
    
     # SHOW ORDERBOOK RAW VERSION     
    def showOrderbook(self):
        widthOrderbook = len("0       Bert    Buy     33      5")
        print(widthOrderbook * 2 * "*")
        
        if self.id in order.activeSellOrders.keys():
            for sellOrder in sorted(order.activeSellOrders[self.id], key = operator.attrgetter("price"), reverse = True):
                    print(widthOrderbook * "." + " " + str(sellOrder))
        if self.id in order.activeBuyOrders.keys():
            for buyOrder in sorted(order.activeBuyOrders[self.id], key = operator.attrgetter("price"), reverse = True):
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
        plt.show()