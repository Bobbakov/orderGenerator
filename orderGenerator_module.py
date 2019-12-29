###############################################################################
# IMPORT REQUIRED LIBRARIES
###############################################################################
import itertools
from datetime import datetime, timedelta
import random
import numpy as np
import operator
from matplotlib import pyplot as plt
import pandas as pd    
import seaborn as sns
import time

# SET DEFAULT FIGURE SIZE
sns.set(rc={'figure.figsize':(10, 5)})

###############################################################################
# ORDER
###############################################################################
class order():
    counter = itertools.count()
    datetimeCounter = datetime(2019, 1, 1, 9, 0, 0)
    history = {}
    activeOrders = {}
    activeBuyOrders = {}
    activeSellOrders = {}
    historyIntialOrder = {}
    
    # Initialize order
    def __init__(self, market, agent, side, price, quantity):
        self.id = next(order.counter)
        order.datetimeCounter += timedelta(seconds = 1)
        self.datetime = order.datetimeCounter 
        self.market = market
        self.agent = agent
        self.side = side
        price = round(price/market.ticksize) * market.ticksize
        price = float("%.2f"%(price))
        self.price = price
        self.quantity = quantity
        
        # If order is first order in a market --> create orderbook
        if not market.id in order.history.keys():
            order.history[market.id] = []
            order.activeOrders[market.id] = []
            order.activeBuyOrders[market.id] = []
            order.activeSellOrders[market.id] = []
            order.historyIntialOrder[market.id] = {}
            
        # Add order to order history
        order.history[market.id].append(self)
        
        # Add hardcoded values to dictionaries (If you add self --> values get overwritten)
        order.historyIntialOrder[market.id][self.id] = {"id": self.id, "market": market, "side": side, 
                         "price": price, "quantity": quantity}
        
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
                            order.removeOffer(bestOffer, market)  
                            
                            # Reduce remaining quantity order
                            remainingQuantity -= transactionQuantity

                        # If quantity buy order equals quantity best offer    
                        elif remainingQuantity == bestOffer.quantity:
                            transactionQuantity = bestOffer.quantity
                            
                            # Register transaction
                            transaction(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            # Remove offer from orderbook
                            order.removeOffer(bestOffer, market) 

                            # Buy order is executed --> break loop
                            break   
                        
                        # if quantity buy order is small than quantity best offer --> reduce quantity best offer
                        else:
                            transactionQuantity = remainingQuantity
                            
                            # Register transaction
                            transaction(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            # Reduce quantity offer
                            order.reduceOffer(bestOffer, transactionQuantity, market)
                            
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
                            order.removeBid(bestBid, market)    
                            
                            remainingQuantity -= transactionQuantity
                          # If quantity order equals quantity best offer    
                        elif remainingQuantity == bestBid.quantity:
                            transactionQuantity = bestBid.quantity
                            
                            # Register transaction
                            transaction(bestBid, self, market, transactionPrice, transactionQuantity)
                            
                            # Remove best bid from orderbook
                            order.removeBid(bestBid, market) 

                            # Order is executed --> break loop
                            break       
                        
                        # If quantity sell order is smaller than quantity best bid
                        else:
                            transactionQuantity = remainingQuantity
                            
                            # Register transaction
                            transaction(bestBid, self, market, transactionPrice, transactionQuantity)
                            
                            # Reduce quantity best bid
                            order.reduceBid(bestBid, transactionQuantity, market)
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
                
###############################################################################
# ORDER: SUPPORTING FUNCTIONS
###############################################################################                            
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {}".format(self.market, self.agent.name, self.side, self.price, self.quantity)

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
                    order.removeOffer(offer, market)
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
                    order.removeBid(bid, market)
                else:
                   a[c].quantity -= transactionQuantity
                break
            
###############################################################################
# TRANSACTION
###############################################################################
class transaction():
    counter = itertools.count()
    history = {}
    historyList = {}
    historyMarketAgent = {}
    
    # Initialize transaction
    def __init__(self, buyOrder, sellOrder, market, price, quantity):
        market.transaction_counter += 1
        self.id  = market.transaction_counter
        
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
                               transaction.calculateRprofit(buyOrder.agent, market)])
        transaction.historyMarketAgent[market.id, sellOrder.agent.name].append([self.id, 
                               sellOrder.agent.position[market.id], 
                               transaction.calculateRprofit(sellOrder.agent, market)])
    
###############################################################################
# TRANSACTION: SUPPORTING FUNCTIONS
###############################################################################
    # Display transaction
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {} \t {} \t {}".format(self.id, self.datetime.time(), self.market, self.buyOrder.agent.name, self.sellOrder.agent.name, self.price, self.quantity)        
    
    # Calculate realized profit agent at market        
    def calculateRprofit(agent, market):
        if agent.quantitySold[market.id] > 0:
            askVwap = agent.valueSold[market.id]/agent.quantitySold[market.id]
        else:
            askVwap = 0
        if agent.quantityBought[market.id] > 0:
            bidVwap = agent.valueBought[market.id]/agent.quantityBought[market.id]
        else:
            bidVwap = 0
            
        q = min(agent.quantitySold[market.id], agent.quantityBought[market.id])
        rp = q * (askVwap - bidVwap)
        return rp 
    
    def transactionDescription(bid, offer, market, price, quantity):
        return print("At market {} - Best bid: {} ({}) Best offer: {} ({}) --> Transaction at: {} ({})".format(market.id, bid.price, bid.quantity, 
                     offer.price, offer.quantity, price, quantity))
        
###############################################################################
# STRATEGIES
###############################################################################      
# Randomly choose Buy/Sell order with both quantity and price from uniform distribution
class strategies():
    def randomUniform(agentId, market):
        side = random.choice(["Buy", "Sell"])
        price = np.arange(market.minprice, market.maxprice, market.ticksize)
        price = np.random.choice(price)
        quantity = random.randint(market.minquantity, market.maxquantity)
        
        # Send order to market
        order(market, agentId, side, price, quantity)
    
    # Randomly choose Buy/Sell order with price from normal distribution      
    def randomNormal(agentId, market):
        side = random.choice(["Buy", "Sell"])
        lastPrice = agent.getLastPriceOrElse(market)
        std = 0.1 * lastPrice
        price = np.random.normal(lastPrice, std)
        quantity = random.randint(market.minquantity, market.maxquantity)
        
        # Send order to market
        order(market, agentId, side, price, quantity)    
    
    # Randomly choose Buy/Sell order with price from lognormal distribution          
    def randomLogNormal(agentId, market, buy_probability = 0.5):
        
        if "buy_probability" in agentId.params.keys():  
            buy_probability = agentId.params["buy_probability"]
        
        sell_probability = 1 - buy_probability
        side = np.random.choice(["Buy", "Sell"], p=[buy_probability, sell_probability])
        lastPrice = agent.getLastPriceOrElse(market)        
        price = lastPrice * np.random.lognormal(0, 0.2)
        quantity = random.randint(market.minquantity, market.maxquantity)
        
        # Send order to market
        order(market, agentId, side, price, quantity)    
    
    ###############################################################################
    # AGENT: MARKET MAKER
    ############################################################################### 
    # Agents always tries to be best bid and best offer at market. If he is not --> he improves price by 1 tick.
    # If position limit is exceeded --> agent closes position at market (in case position > 0) or buys back all shorts (in case position < 0)
    def bestBidOffer(agentId, market):
        quantity = random.randint(market.minquantity, market.maxquantity)
        
        # If agent has position_limit --> check if limit is exceeded    
        if "position_limit" in agentId.params.keys():  
            position_limit = agentId.params["position_limit"]
            if market.id in agentId.position.keys():
                if agentId.position[market.id] > position_limit:
                    order(market, agentId, "Sell", market.minprice, abs(agentId.position[market.id]))  
                elif agentId.position[market.id] < -1 * position_limit:
                    order(market, agentId, "Buy", agent.getLastPriceOrElse(market) * 2, abs(agentId.position[market.id]))  
                
        # If there are active buy orders --> improve best bid by one tick
        if market.id in order.activeBuyOrders.keys():
            if not not order.activeBuyOrders[market.id]:
                buyOrders = sorted(order.activeBuyOrders[market.id], key = operator.attrgetter("price"), reverse = True)
                bestBid = buyOrders[0]
                
                # If trader is not best bid --> improve best bid
                if not bestBid.agent.name == agentId.name:
                    order(market, agentId, "Buy", bestBid.price + market.ticksize, quantity)    
                else:
                    pass
            # Else --> create best bid    
            else:
                order(market, agentId, "Buy", market.minprice, quantity)
        # If no buy orders active in market --> start the market
        else:
            order(market, agentId, "Sell", market.maxprice, quantity)
        
        # If there are active sell orders --> improve best offer by one tick
        if market.id in order.activeSellOrders.keys():
            if not not order.activeSellOrders[market.id]:
                sellOrders = sorted(order.activeSellOrders[market.id], key = operator.attrgetter("price"))
                bestOffer = sellOrders[0]
                
                # If trader is not best offer --> improve best offer
                if not bestOffer.agent.name == agentId.name:
                    order(market, agentId, "Sell", bestOffer.price - market.ticksize, quantity)    
                else:
                    pass
            # Else --> create best bid    
            else:
                order(market, agentId, "Sell", market.maxprice, quantity) 
        else:
            # If no sell orders active in market --> start the market
            order(market, agentId, "Sell", market.maxprice, quantity)
      
    ###############################################################################
    # AGENT: ARBITRAGE (BETWEEN MARKETS)
    ###############################################################################         
    # If price at marketB is lower than bestBid at marketA --> agents buys bestOffer at MarketB and sells to bestBid at marketA.
    # The same goes the other way around.        
    def simpleArbitrage(agentId, marketA, marketB):
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
                            order(marketB, agentId, "Buy", bestOfferMarketB.price, bestOfferMarketB.quantity)
                            order(marketA, agentId, "Sell", bestBidMarketA.price, bestBidMarketA.quantity)
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
                            order(marketA, agentId, "Buy", bestOfferMarketA.price, bestOfferMarketA.quantity)
                            order(marketB, agentId, "Sell", bestBidMarketB.price, bestBidMarketB.quantity)
    
    ###############################################################################
    # AGENT: ONE BUY ORDER WITH STOP LOSS
    ###############################################################################
    def stopLoss(agentId, market):
        '''
        if market.id in self.lastOrder.keys():
            if (self.lastOrder[market.id].side == "Buy"):
                self.stop[market.id] = self.lastOrder[market.id].price * (1 + stop_loss)
        
        lastPrice = agent.getLastPriceOrElse(market)
        
        # If agent doesn't have position in market
        if (not market.id in agent.position.keys()) or (agent.position[market.id] == 0):
            # Agent buys at market (= for any price). This is +- equivalent to buying at price = lastPrice * 2
            price = market.maxprice
            # Correct for ticksize market
            quantity = random.randint(market.minquantity, market.maxquantity)
            
            # Send order to market
            order(market, self, "Buy", price, quantity)  
            
            # Initiate stop
            if "stop_loss" in self.params.keys():  
                stop_loss = self.params["stop_loss"]
            self.stop[market.id] = price * (1 + stop_loss)
        else:
            if lastPrice < self.stop[market.id]:
                # Sell position at market
                order(market, self, "Sell", market.minprice, self.position[market.id])  
        '''
        return 0
    
    ###############################################################################
    # AGENT: ADD strategies TO ARRAY
    ############################################################################### 
    strategies = [randomUniform, randomNormal, randomLogNormal, bestBidOffer, simpleArbitrage, stopLoss]
    strategiesName = ["randomUniform", "randomNormal", "randomLogNormal", "bestBidOffer", "simpleArbitrage", "stopLoss"]
    linestyles = ["solid", "dotted", "solid", "dashed", "dashdot", "dashed"]
    strategiesDict = {}
    
    for i, x in enumerate(strategiesName):
        # print(i)
        if (i%2 == 0):
            strategiesDict[x] = {"strategy": strategies[i], "linestyle": "dotted"}
        else:
            strategiesDict[x] = {"strategy": strategies[i], "linestyle": "solid"}

###############################################################################
# AGENT
###############################################################################      
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
        
###############################################################################
# AGENT: SUPPORTING FUNCTIONS
###############################################################################  
    
    # If price has been printed in market --> return last price. Else --> return mid price
    def getLastPriceOrElse(market):
        if market.id in transaction.history.keys():
            p = transaction.history[market.id][-1].price 
        else:
            p = (market.maxprice - market.minprice)/2             
        return p

###############################################################################
# MARKET
############################################################################### 
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
                    
                c+= 1
                
                # Clear orderbook at fixed intervals
                if (c%clearAt == 0):
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
        print("Last order: \n{} with price {} (quantity = {})".format(last_order["side"], last_order["price"], last_order["quantity"]))
        
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
                df = pd.DataFrame(transaction.historyMarketAgent[self.id, a.name], columns = ["id", "runningPosition", "runningProfit"])
                df = df.set_index("id")
                rPosition = df["runningPosition"]
                plt.plot(rPosition, label = "{} ({})".format(str(a.name), a.strategy), linestyle = strategies.strategiesDict[a.strategy]["linestyle"])
                plt.plot()
        plt.legend()

        return plt.show()
    
     # Plot profitsall agents
    def plotProfits(self, agents = []):
        if len(agents) == 0:
            agents = [a.name for a in self.agents]        
        for a in self.agents:
            if a.name in agents:
                df = pd.DataFrame(transaction.historyMarketAgent[self.id, a.name], columns = ["id", "runningPosition", "runningProfit"])
                df = df.set_index("id")
                rProfit = df["runningProfit"]
                plt.plot(rProfit, label = "{} ({}) runningProfit".format(str(a.name), a.strategy), linestyle = strategies.strategiesDict[a.strategy]["linestyle"])
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
        ax1.tick_params(axis='y')
        
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        ax2.set_ylabel('Position')  # we already handled the x-label with ax1
        for a in self.agents:
            if a.name in agents:
                df = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", "runningPosition", "runningProfit"])
                df = df.set_index("id")
                ax2.plot(df.index, df["runningPosition"], linestyle = strategies.strategiesDict[a.strategy]["linestyle"])
        ax2.tick_params(axis='y')
        
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        return plt.show()
        
    def plotOrdersTrades(self):
        #Times of order entry
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
            right = pd.DataFrame(transaction.historyMarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[a.name]
            axs[1, 0].plot(right, label = str(a.name))
        axs[1, 0].set_title("Positions")  
        
        if len(self.agents) < 20:
            axs[1, 0].legend()
        
        for a in self.agents:
            right = pd.DataFrame(transaction.historyMarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
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
            for sellOrder in sorted(order.activeSellOrders[self.id], key = operator.attrgetter("price"), reverse = True)[:show_depth]:
                    print(widthOrderbook * "." + " " + str(sellOrder))
        if self.id in order.activeBuyOrders.keys():
            for buyOrder in sorted(order.activeBuyOrders[self.id], key = operator.attrgetter("price"), reverse = True)[:show_depth]:
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