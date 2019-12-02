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
sns.set(rc={'figure.figsize':(30, 15)})

###############################################################################
# FUNCTIONS FOR ORDER: CORRECT
###############################################################################
# Remove offer from order book
def removeOffer(offer, market):
    a = order.activeSellOrders[market.id]
    for c, o in enumerate(a):
        if o.id == offer.id:
            del a[c]
            break

# Remove offer from order book
def reduceOffer(offer, transactionQuantity, market):
    a = order.activeSellOrders[market.id]
    for c, o in enumerate(a):
        if o.id == offer.id:
            if a[c].quantity == transactionQuantity:
                removeOffer(offer, market)
            else:
                a[c].quantity -= transactionQuantity
            break

# Remove bid from order book
def removeBid(bid, market):
    a = order.activeBuyOrders[market.id]
    for c, o in enumerate(a):
        if o.id == bid.id:
            del a[c]
            break  
        
# Remove offer from order book
def reduceBid(bid, transactionQuantity, market):
    a = order.activeBuyOrders[market.id]
    for c, o in enumerate(a):
        if o.id == bid.id:
            if a[c].quantity == transactionQuantity:
                removeBid(bid, market)
            else:
               a[c].quantity -= transactionQuantity
            break

def getLastPriceOrElse(market):
    # IF MARKET EXISTS/IF THERE HAS BEEN TRADE IN THE MARKET
    if market.id in transaction.historyRaw.keys():
        p = transaction.historyRaw[market.id][-1].price 
    else:
        p = (market.maxprice - market.minprice)/2             
    return p

def getMidPointPriceOrElse(market):
    if market.id in transaction.historyRaw.keys():
        # IF THERE IS AN OFFER
        if not not order.activeSellOrders[market.id]:
            sellOrders = sorted(order.activeSellOrders[market.id], key = operator.attrgetter("price"))
            bestOffer = sellOrders[0]
            
            # GET BEST OFFER PRICE
            bestOfferPrice = bestOffer.price
        else:
            bestOfferPrice = market.maxprice
        
        # IF THERE IS A BID
        if not not order.activeBuyOrders[market.id]:
            buyOrders = sorted(order.activeBuyOrders[market.id], key = operator.attrgetter("price"), reverse = True)
            bestBid = buyOrders[0]
            
            # GET BEST BID
            bestBidPrice = bestBid.price
        else:
            bestBidPrice = market.minprice
    else:
        bestOfferPrice = market.maxprice
        bestBidPrice = market.minprice
        
    midPointPrice = (bestOfferPrice - bestBidPrice)/2
            
    return midPointPrice   

###############################################################################
# ORDER: CORRECT
###############################################################################
        
class order():
    counter = itertools.count()
    history = {}
    activeOrders = {}
    activeBuyOrders = {}
    activeSellOrders = {}
    
    # Initialize order
    def __init__(self, market, agent, side, price, quantity, mute_transactions = True):
        self.id = next(order.counter)
        self.datetime = datetime.now()
        self.market = market
        self.agent = agent
        self.side = side
        self.price = price
        self.quantity = quantity
        
        # IF FIRST ORDER IN MARKET --> INITIALIZE ORDERBOOKS
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
                        
                        # If quantity order larger than best offer
                        if remainingQuantity > bestOffer.quantity:
                            transactionQuantity = bestOffer.quantity
                            
                            # Register transaction
                            transaction(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            if not mute_transactions:
                                transactionDescription(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            # Remove offer from orderbook
                            removeOffer(bestOffer, market)  
                            
                            # Reduce remaining quantity order
                            remainingQuantity -= transactionQuantity

                        # If quantity order equals quantity best offer    
                        elif remainingQuantity == bestOffer.quantity:
                            transactionQuantity = bestOffer.quantity
                            
                            # Register transaction
                            transaction(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            if not mute_transactions:
                                transactionDescription(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            # Remove offer from orderbook
                            removeOffer(bestOffer, market) 

                            # order is executed --> break loop
                            break       
                        # IF quantity order is small than quantity best offer
                        else:
                            transactionQuantity = remainingQuantity
                            
                            # Register transaction
                            transaction(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            if not mute_transactions:
                                transactionDescription(self, bestOffer, market, transactionPrice, transactionQuantity)
                            
                            # Reduce offer
                            reduceOffer(bestOffer, transactionQuantity, market)
                            break
                            
                        
                    # If bid price < best offer --> no transaction    
                    else:
                        self.quantity = remainingQuantity
                        order.activeOrders[market.id].append(self)
                        order.activeBuyOrders[market.id].append(self)
                        break
                    
                # If there are NOT active sell orders --> add order to active orders        
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
                        # If limit price sell order <= price best bid --> transaction
                        if bestBid.price >= self.price:
                            transactionPrice = bestBid.price
                            
                            # If quantity offer larger than quantity best bid
                            if remainingQuantity > bestBid.quantity:
                                transactionQuantity = bestBid.quantity
                                
                                # Register transaction
                                transaction(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                
                                if not mute_transactions:
                                    transactionDescription(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                # Remove bid from orderbook
                                removeBid(bestBid, market)    
                                
                                remainingQuantity -= transactionQuantity
                              # If quantity order equals quantity best offer    
                            elif remainingQuantity == bestBid.quantity:
                                transactionQuantity = bestBid.quantity
                                
                                # Register transaction
                                transaction(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                if not mute_transactions:
                                    transactionDescription(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                # Remove offer from orderbook
                                removeBid(bestBid, market) 
    
                                # order is executed --> break loop
                                break       
                            
                            # IF quantity order is smaller than quantity best bid
                            else:
                                transactionQuantity = remainingQuantity
                                
                                # Register transaction
                                transaction(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                if not mute_transactions:
                                    transactionDescription(bestBid, self, market, transactionPrice, transactionQuantity)
                                
                                # Reduce offer
                                reduceBid(bestBid, transactionQuantity, market)
                                break
                            
                        # No transaction    
                        else:
                            self.quantity = remainingQuantity
                            order.activeOrders[market.id].append(self)
                            order.activeSellOrders[market.id].append(self)
                            break
                        
                    # If there are NOT active buy orders --> add order to active orders         
                    else: 
                        self.quantity = remainingQuantity
                        order.activeOrders[market.id].append(self)
                        order.activeSellOrders[market.id].append(self)
                        break
                
            
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {}".format(self.market, self.agent.name, self.side, self.price, self.quantity)

###############################################################################
# FUNCTIONS FOR TRANSACTIONS
###############################################################################
def transactionDescription(bid, offer, market, transactionPrice, transactionQuantity):
    return print("At market {} - Best bid: {} ({}) Best offer: {} ({}) --> Transaction at: {} ({})".format(market.id, bid.price, bid.quantity, 
                 offer.price, offer.quantity, transactionPrice, transactionQuantity))

###############################################################################
# TRANSACTIONS: CORRECT
###############################################################################
class transaction():
    counter = itertools.count()
    historyRaw = {}
    historyList = {}
    MarketAgent = {}
    
    def __init__(self, buyOrder, sellOrder, market, price, quantity):
        self.id = next(transaction.counter)
        self.datetime = datetime.now()
        self.market = market
        self.buyOrder = buyOrder
        self.sellOrder = sellOrder
        self.price = price
        self.quantity = quantity
        
        # INITIALIZE POSTIION VALUEBOUGHT, ETC.
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
        
        # UPDATE POSITIONS ETC.
        buyOrder.agent.position[market.id] += quantity
        sellOrder.agent.position[market.id] -= quantity
        buyOrder.agent.valueBought[market.id] += price * quantity
        buyOrder.agent.quantityBought[market.id] += quantity
        sellOrder.agent.valueSold[market.id] += price * quantity
        sellOrder.agent.quantitySold[market.id] += quantity
        
        # INITIALIZE VALUES
        if not market.id in transaction.historyRaw.keys():
            transaction.historyRaw[market.id] = []
            transaction.historyList[market.id] = []
            
        if not (market.id, buyOrder.agent.name) in transaction.MarketAgent.keys():
            transaction.MarketAgent[market.id, buyOrder.agent.name] = []
            
        if not (market.id, sellOrder.agent.name) in transaction.MarketAgent.keys():
            transaction.MarketAgent[market.id, sellOrder.agent.name] = []        
        
        # RECORD PRICE
        transaction.historyRaw[market.id].append(self)
        transaction.historyList[market.id].append([self.id, self.datetime.time(), self.price])
        
        # PER MARKET PER AGENT --> RECORD RUNNING POSITION + RUNNING PROFIT
        transaction.MarketAgent[market.id, buyOrder.agent.name].append([self.id, 
                               buyOrder.agent.position[market.id], 
                               buyOrder.agent.calculateRprofit(market)])
        transaction.MarketAgent[market.id, sellOrder.agent.name].append([self.id, 
                               sellOrder.agent.position[market.id], 
                               sellOrder.agent.calculateRprofit(market)])
    
    # CHANGE DISPLAY TRANSACTIONS    
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {} \t {} \t {}".format(self.id, self.datetime.time(), self.market, self.buyOrder.agent.name, self.sellOrder.agent.name, self.price, self.quantity)        
    
###############################################################################
# AGENTS: CORRECT
###############################################################################      
class agent():  
    # INITIALIZE VALUES
    def __init__(self, name): 
        self.name = name
        
        # STARTS WITH EMPTY VALUES
        self.position = {}
        self.runningProfit = {}
        
        self.valueBought = {}
        self.quantityBought = {}
        self.valueSold = {}
        self.quantitySold = {}  
     
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
    
    # ALGORITHMIC TRADING STRATEGIES
    
    # RANDOMLY PICK BUY/SELL + PRICE AND QUANTITY FROM A UNIFORM DISTRIBUTION
    def randomUniform(self, market):
        side = random.choice(["Buy", "Sell"])
        
        # GENERATE SET OF POSSIBLE PRICES
        price = np.arange(market.minprice, market.maxprice, market.ticksize)
        price = np.random.choice(price)
        quantity = random.randint(market.minquantity, market.maxquantity)
        
        # SEND ORDER TO MARKET
        order(market, self, side, price, quantity)
    
    # RANDOMLY PICK BUY/SELL + PRICE FROM A NORMAL DISTRIBUTION       
    def randomNormal(self, market):
        side = random.choice(["Buy", "Sell"])
        
        lastPrice = getLastPriceOrElse(market)
        std = 0.1 * lastPrice
        
        # GENERATE SET OF POSSIBLE PRICES
        price = np.random.normal(lastPrice, std)
        quantity = random.randint(market.minquantity, market.maxquantity)
        
        # SEND ORDER TO MARKET
        order(market, self, side, price, quantity)    
    
    # RANDOMLY PICK BUY/SELL + PRICE FROM A LOGNORMAL DISTRIBUTION          
    def randomLogNormal(self, market):
        side = random.choice(["Buy", "Sell"])

        lastPrice = getLastPriceOrElse(market)
        
        # GENERATE SET OF POSSIBLE PRICES
        # FIX FOR TICK.SIZE
        price = lastPrice * np.random.lognormal(0, 0.2)
        price = round(price/market.ticksize) * market.ticksize
        quantity = random.randint(market.minquantity, market.maxquantity)
        
        # SEND ORDER TO MARKET
        order(market, self, side, price, quantity)    
    
    # AGENT ALWAYS WANTS TO BE BEST BID + BEST OFFER. IF NOT --> HE IMPROVES PRICE BY 1 TICK.
    # IF POSITION LIMIT EXCEEDED --> AGENTS CLOSES POSITION BY SENDING IN MARKET ORDER.
    def bestBidOffer(self, market, stop = False, position_limit = 250):
        quantity = random.randint(market.minquantity, market.maxquantity)
        
        if stop:
            
            # IF POSITION IS INITIATED
            if market.id in self.position.keys():
                # CORRECT FOR IF MARKET HASN'T STARTED YET
                if self.position[market.id] > position_limit:
                    order(market, self, "Sell", market.minprice, abs(self.position[market.id]))  
                elif self.position[market.id] < - position_limit:
                    order(market, self, "Buy", market.maxprice, abs(self.position[market.id]))  
                
        # IF THERE ARE ACTIVCE BUY ORDERS --> IMPROVE BEST BID
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
         
        # If there are active sell orders --> improve best offer
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
    
###############################################################################
# MARKET: CORRECT
############################################################################### 
class market():
    counter = itertools.count()
       
    # INITIALIZE THE MARKET
    def __init__(self, minprice = 1, maxprice = 100, ticksize = 0.05, minquantity = 1, maxquantity = 10, auto_init = True):
        self.id = next(market.counter)
        self.minprice = minprice
        self.maxprice = maxprice
        self.ticksize = ticksize
        self.minquantity = minquantity
        self.maxquantity = maxquantity
        
        # INITIALIZE EMPTY LIST OF AGENTS + AGENT COUNTER
        self.agents = []
        self.agent_counter = {}
        
        # MAKE SURE SIMULATIONS START FROM SAME SEEED --> OTHERWISE SIMULATIONS WILL BE DIFFERENT
        random.seed(100)
        np.random.seed(100)
        
        # AUTOMATICALLY ADD preset_agents TO MARKET
        if auto_init:
            preset_agents = ["randomLogNormal", "marketMaker", "marketMaker", "marketMaker"]
            self.addAgents(preset_agents)
            self.orderGenerator(5000)
    
    def __str__(self):
        return "{}".format(self.id)    
 
    # ADD AGENTS TO MARKET     
    def addAgents(self, agents):
        for a in agents:
                if a in self.agent_counter.keys():
                    self.agent_counter[a] += 1
                else: 
                    self.agent_counter[a] = 1
                self.agents.append((agent(str(a) + str(self.agent_counter[a])) , a))
  
    # ORDER GENERATOR
    def orderGenerator(self, n = 5000, clearAt = 1000, sleeptime = 0):
        c = 1
        
        # FOR EACH ITERATION
        for o in range(int(n)):      
            # LOOP THROUGH AGENTS
            for a, s in self.agents:
                if s == "randomUniform":
                    a.randomUniform(self) 
                if s == "randomNormal":
                    a.randomNormal(self)
                if s == "randomLogNormal":
                    a.randomLogNormal(self)
                if s == "marketMaker":
                    a.bestBidOffer(self, stop = False)     
                                
            c+= 1
            
            '''
            # CLEAR ORDERBOOK AT FIXED INTERVALS
            if (c%clearAt == 0):
                self.clear()   
            '''
            
            '''
            # SLOW DOWN ORDER GENERATION    
            if (c%10 == 0):
                self.showOrderbook()
                #self.plotPositions()
                time.sleep(float(5))
            '''
            
    # EMPTY ORDERBOOK        
    def clear(self):
        order.activeBuyOrders[self.id] = []
        order.activeSellOrders[self.id] = []
    
    # PLOT PRICE + RUNNING VOLATILITY
    def plot(self):
        df = pd.DataFrame(transaction.historyList[self.id], columns = ["id", "time", "price"])
        #df["volatility"] = df["price"].rolling(7).std()
        #df["volatilityTrend"] = df["volatility"].rolling(14).mean()
        #df = df[["id", "price", "volatility", "volatilityTrend"]]
        df[["id", "price"]]
        df = df.set_index("id")
        return df.plot() 
    
    # PLOT POSITIONS
    def plotPositions(self):
        # PLOT RUNNING POSITIONS + RUNNING PROFITS AGENTS
        for a, s in self.agents:
            right = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[a.name]
            plt.plot(right, label = str(a.name))
            plt.legend()

        return plt.show()
    
    # PLOT PROFITS
    def plotProfits(self):
        for a, s in self.agents:
            right = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[str(a.name) + "RunningProfit"]
            plt.plot(right, label = str(a.name) + "RunningProfit")
            plt.legend()

        return plt.show()
    
    # PLOT ALL FIGURES INTO ONE OVERVIEW
    def summary(self):
        df = pd.DataFrame(transaction.historyList[self.id], columns = ["id", "time", "price"])
        df["volatility"] = df["price"].rolling(7).std()
        df["volatilityTrend"] = df["volatility"].rolling(100).mean()
        df = df[["id", "price", "volatility", "volatilityTrend"]]
        df = df.set_index("id")
        
        dfPrice = df["price"]
        dfVolatility = df[["volatility", "volatilityTrend"]]
        
        # PLOT PRICE
        fig, axs = plt.subplots(3, 2)
        axs[0, 0].plot(dfPrice, label = "price")
        axs[0, 0].set_title("Price")
        axs[0, 0].legend()
        
        # PLOT VOLATILITY
        #plt.subplot(2, 2, 2)
        axs[0, 1].plot(dfVolatility)
        axs[0, 1].set_title("Volatility")
        axs[0, 1].legend()
        
        # PLOT RUNNING POSITIONS + RUNNING PROFITS AGENTS
        for a, s in self.agents:
            right = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            right = right[a.name]
            #plt.subplot(2, 2, 3)
            axs[1, 0].plot(right, label = str(a.name))
        axs[1, 0].set_title("Positions")    
        axs[1, 0].legend()
        
        for a, s in self.agents:
            right = pd.DataFrame(transaction.MarketAgent[self.id, a.name], columns = ["id", a.name, str(a.name) + "RunningProfit"])
            right = right.set_index("id")
            ##plt.subplot(2, 2, 4)
            right = right[str(a.name) + "RunningProfit"]
            axs[1, 1].plot(right, label = str(a.name) + "RunningProfit")
        
        #axs[1, 1].legend()
        axs[1, 1].set_title("Running profit")
        # plt.savefig('test.pdf')
        
        
        return plt.show()
    
     # SHOW ORDERBOOK RAW VERSION     
    def showOrderbook(self):
        widthOrderbook = len("0       Bert    Buy     33      5")
        print(widthOrderbook * 2 * "*")
        
        for sellOrder in sorted(order.activeSellOrders[self.id], key = operator.attrgetter("price"), reverse = True):
                print(widthOrderbook * "." + " " + str(sellOrder))
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

        # sns.set(rc={'figure.figsize':(10, 5)})
        
        plt.hist(buyOrders, bins = 100, color = "green")
        plt.hist(sellOrders, bins = 100, color = "red")
        plt.show()