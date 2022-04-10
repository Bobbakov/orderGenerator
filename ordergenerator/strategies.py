# Import libraries -->
import random
import numpy as np 
from matplotlib import pyplot as plt
plt.rcParams["figure.figsize"] = (15, 15)

# Import modules -->
import order
import transaction
import cancellation

class template_strategies():
    """
    Select out of the box trading strategies
    """
    def random_uniform(current_agent, market):
        """Select price and quantity from uniform distribution"""
        side = random.choice(["Buy", "Sell"])
        price = np.arange(market.minprice, (market.maxprice + market.ticksize), market.ticksize)
        price = np.random.choice(price)
        quantity = random.randint(market.minquantity, market.maxquantity)

        # Send order to market
        order.new_order(market, current_agent, side, price, quantity)

    def random_normal(current_agent, market):
        """Select price from normal distribution around last price and quantity from uniform distribution"""
        side = random.choice(["Buy", "Sell"])
        last_price = get_last_price(market)
        std = (0.1 * last_price)
        price = np.random.normal(last_price, std)
        quantity = random.randint(market.minquantity, market.maxquantity)

        # Send order to market
        order.new_order(market, current_agent, side, price, quantity)

    def random_lognormal(current_agent, market, buy_probability = 0.5):
        """Select price from lognormal distribution around last price and quantity from uniform distribution"""
        if "buy_probability" in current_agent.params.keys():
            buy_probability = current_agent.params["buy_probability"]

        sell_probability = (1 - buy_probability)
        side = np.random.choice(["Buy", "Sell"], 
                                p = [buy_probability, sell_probability])
        last_price = get_last_price(market)
        price = (last_price * np.random.lognormal(0, 0.2))
        quantity = random.randint(market.minquantity, market.maxquantity)

        # Send order to market
        order.new_order(market, current_agent, side, price, quantity)
    
    ###############################################################################
    # AGENT: MARKET MAKER
    ###############################################################################        
    def best_bid_offer(current_agent, market):
        """ Agents always tries to be best bid and best offer at market. If agent is not --> agent improves price by 1 tick.
        If position limit is exceeded --> agent closes position at market (in case position > 0) or buys back all shorts (in case position < 0) """
        quantity = random.randint(market.minquantity, market.maxquantity)

        # If agent has position_limit --> check if limit is exceeded
        if "position_limit" in current_agent.params.keys():
            position_limit = current_agent.params["position_limit"]
            if current_agent.position[market.id] > position_limit:
                order.new_order(market, current_agent, "Sell", market.minprice, abs(current_agent.position[market.id]))
            elif current_agent.position[market.id] < -1 * position_limit:
                order.new_order(market, current_agent, "Buy", market.maxprice, abs(current_agent.position[market.id]))

        # If there are active buy orders --> improve best bid by one tick
        (best_bid, best_bid_price) = get_best_bid(market) 
        if best_bid != None:
            if not best_bid.agent.name == current_agent.name:
                order.new_order(market, current_agent, "Buy", best_bid.price + market.ticksize, quantity)
            else:
                pass
        # If no buy orders active in market --> start the market
        else:
            order.new_order(market, current_agent, "Buy", market.minprice, quantity)
        
        (best_offer, best_offer_price) = get_best_offer(market) 
        # If there are active sell orders --> improve best offer by one tick
        if best_offer != None:
            # If trader is not best offer --> improve best offer
            if not best_offer.agent.name == current_agent.name:
                order.new_order(market, current_agent, "Sell", best_offer.price - market.ticksize, quantity)
            else:
                pass
        # Else --> create best bid
        else:
            order.new_order(market, current_agent, "Sell", market.maxprice, quantity)
    
    ###############################################################################
    # AGENT: Add strategies to list for selection
    ###############################################################################
    strategies = [random_uniform, 
                  random_normal, 
                  random_lognormal, 
                  best_bid_offer]

    ###############################################################################
    # AGENT: ARBITRAGE (BETWEEN MARKETS): Ignore for now -->
    ###############################################################################
    # If price at marketB is lower than best_bid at marketA --> agents buys best_offer at MarketB and sells to best_bid at marketA.
    # The same goes the other way around.
    '''
    def simpleArbitrage(current_agent, marketA, marketB):
        # If marketA is initiated
        if marketA.id in order.active_buy_orders.keys():
            # If there are active buy orders
            if not not order.active_buy_orders[marketA.id]:
                # If marketB is initiated
                if marketB.id in order.active_sell_orders.keys():
                    # If there are active sell orders
                    if not not order.active_sell_orders[marketB.id]:
                        buy_ordersMarketA = sorted(order.active_buy_orders[marketA.id], key = operator.attrgetter("price"),
                                                  reverse = True)
                        best_bidMarketA = buy_ordersMarketA[0]
    
                        sell_ordersMarketB = sorted(order.active_sell_orders[marketB.id], key = operator.attrgetter("price"), reverse = False)
                        best_offerMarketB = sell_ordersMarketB[0]
    
                        if best_bidMarketA.price > best_offerMarketB.price:
                            order(marketB, current_agent, "Buy", best_offerMarketB.price, best_offerMarketB.quantity)
                            order(marketA, current_agent, "Sell", best_bidMarketA.price, best_bidMarketA.quantity)
        # The other way around
        if marketA.id in order.active_sell_orders.keys():
            if not not order.active_sell_orders[marketA.id]:
                if marketB.id in order.active_buy_orders.keys():
                    if not not order.active_buy_orders[marketB.id]:
                        sell_ordersMaketA = sorted(order.active_sell_orders[marketA.id], key = operator.attrgetter("price"), reverse = False)
                        best_offerMarketA = sell_ordersMaketA[0]
    
                        buy_ordersMarketB = sorted(order.active_buy_orders[marketB.id], key = operator.attrgetter("price"),
                                                  reverse = True)
                        best_bidMarketB = buy_ordersMarketB[0]
    
                        if best_bidMarketB.price > best_offerMarketA.price:
                            order(marketA, current_agent, "Buy", best_offerMarketA.price, best_offerMarketA.quantity)
                            order(marketB, current_agent, "Sell", best_bidMarketB.price, best_bidMarketB.quantity)
    
    ###############################################################################
    # AGENT: ONE BUY ORDER WITH STOP LOSS
    ###############################################################################
    def stopLoss(current_agent, market):
        if market.id in self.last_order.keys():
            if (self.last_order[market.id].side == "Buy"):
                self.stop[market.id] = self.last_order[market.id].price * (1 + stop_loss)
    
        last_price = agent.get_last_price(market)
    
        # If agent doesn't have position in market
        if (not market.id in agent.position.keys()) or (agent.position[market.id] == 0):
            # Agent buys at market (= for any price). This is +- equivalent to buying at price = last_price * 2
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
            if last_price < self.stop[market.id]:
                # Sell position at market
                order(market, self, "Sell", market.minprice, self.position[market.id])
        return 0
    '''       
        
class custom_strategies():
    """ This is where you can code any self-developed trading strategies"""
    def only_best_bid_best_offer(current_agent, market):
        """
        This agent always want to be best bid and best offer
        
        If agent improves his own orders -- > other orders by agent are removed
        If sending in order will take away liquidity --> agent will not send in order
        
        """
        quantity = random.randint(market.minquantity, market.maxquantity)
        (best_bid, best_bid_price) = get_best_bid(market)
        (best_offer, best_offer_price) = get_best_offer(market)
        
        # If there are no active buy orders -->
        if best_bid == None:
            # If no transaction occurs by sending in bid -->
            if best_offer_price > market.minprice:
                order.new_order(market, current_agent, "Buy", market.minprice, quantity)
        # If there are active buy orders -->
        else:
            # If trader is best bid --> do nothing
            if (best_bid.agent.name == current_agent.name):
                pass
            else:
                # If no transaction occurs by improving best bid -->
                if best_offer_price > (best_bid_price + market.ticksize):
                    new_best_bid = order.new_order(market, current_agent, "Buy", (best_bid_price + market.ticksize), quantity)
                    cancellation.cancel_all_bids_agent_except(market, current_agent, new_best_bid)
        
        
        quantity = random.randint(market.minquantity, market.maxquantity)
        (best_bid, best_bid_price) = get_best_bid(market)
        (best_offer, best_offer_price) = get_best_offer(market)
        
        # If there are no active sell orders -->
        if best_offer == None:
            # If no transaction occurs by sending in bid -->
            if best_bid_price < market.maxprice:
                order.new_order(market, current_agent, "Sell", market.maxprice, quantity)
        # If there are active buy orders -->
        else:
            # If trader is best bid --> do nothing
            if (best_offer.agent.name == current_agent.name):
                pass
            else:
                # If no transaction occurs by improving best bid -->
                if best_bid_price < (best_offer_price - market.ticksize):
                    new_best_offer = order.new_order(market, current_agent, "Sell", (best_offer_price - market.ticksize), quantity)
                    cancellation.cancel_all_offers_agent_except(market, current_agent, new_best_offer)
 
    
    def orders_max_n_ticks_away_from_midpoint_price(current_agent, market, n_ticks=10, max_number_bids_in_orderbook = 5, max_number_offers_in_orderbook = 5):
        quantity = random.randint(market.minquantity, market.maxquantity)
        midpoint_price = get_midpoint_price(market)
        bid_target_price = (midpoint_price - (n_ticks *market.ticksize))
        offer_target_price = (midpoint_price + (n_ticks *market.ticksize))
        
        # Get bids agents -->
        bids_agent = bids_agent_in_orderbook(current_agent, market)
        
        # Get offers agent
        offers_agents = offers_agent_in_orderbook(current_agent, market)
        
        bids_to_delete = [o for o in bids_agent if o.price < bid_target_price]
        cancellation.cancel_orders(bids_to_delete)
        offers_to_delete = [o for o in offers_agents if o.price > offer_target_price]
        cancellation.cancel_orders(offers_to_delete)
        
        # If still room for more bids -->
        if (len(bids_agent) - len(bids_to_delete)) < max_number_bids_in_orderbook:
            if bid_target_price < market.minprice:
                order.new_order(market, current_agent, "Buy", market.minprice, quantity)
            else:
                order.new_order(market, current_agent, "Buy", bid_target_price, quantity)
                
        # Recalculate midpoint price after sending in bid -->
        quantity = random.randint(market.minquantity, market.maxquantity)
        midpoint_price = get_midpoint_price(market)
        bid_target_price = (midpoint_price - (n_ticks *market.ticksize))
        offer_target_price = (midpoint_price + (n_ticks *market.ticksize))
       
        # If still room for more offers -->
        if (len(offers_agents) - len(offers_to_delete)) < max_number_offers_in_orderbook:
           if offer_target_price > market.maxprice:
               order.new_order(market, current_agent, "Sell", market.maxprice, quantity)
           else:
               order.new_order(market, current_agent, "Sell", offer_target_price, quantity)         
                
            
    def snipe_best_bid_or_offer(current_agent, market):
        """"
        Agent always buys best offer (if available) and sells to best bid (if available) 
        
        In case both best offer and best bid are available, agent randomly buys or sells
        """
        quantity = random.randint(market.minquantity, market.maxquantity)
        (best_bid, _) = get_best_bid(market)
        (best_offer, _) = get_best_offer(market)
        
        # If no best_bid or best_offer
        if (best_bid == None and best_offer == None):
            pass
        elif (best_bid != None and best_offer == None):
            order.new_order(market, current_agent, "Sell", best_bid.price, quantity)
        elif (best_bid == None and best_offer != None):
            order.new_order(market, current_agent, "Buy", best_offer.price, quantity)
        else:
            buy_or_sell = random.choice(["Buy", "Sell"])
            if buy_or_sell == "Buy":
                order.new_order(market, current_agent, "Buy", best_offer.price, quantity)
            else:
                order.new_order(market, current_agent, "Sell", best_bid.price, quantity)               
                    
""" These functions are use in implmementing new trading strategies"""
def get_best_bid(market):
    """
    Return tuple (best_bid, best_bid_price)
    
    In case there is no best bid, returns (None, market.minprice - market.ticksize)
    """
    if len(order.active_buy_orders[market.id]) > 0:
        buy_orders = sorted(order.active_buy_orders[market.id], key = lambda x: (-1 * x.price, x.id))
        best_bid = buy_orders[0]
        best_bid_price = best_bid.price
    else:
        best_bid = None
        # If no bids --> improving best bid by one tick should send in market.minprice
        best_bid_price = (market.minprice - market.ticksize)
    return (best_bid, best_bid_price)

def get_next_best_bid(market):
    """
    Return tuple (next_best_bid_exists, next_best_bid_price)
    
    In case there is no best bid, returns (False, market.minprice - market.ticksize)
    """
    next_best_bid_exists = False
    if len(order.active_buy_orders[market.id]) > 1:
        buy_orders = sorted(order.active_buy_orders[market.id], key = lambda x: (-1 * x.price, x.id))
        next_best_bid = buy_orders[1]
        next_best_bid_price = next_best_bid.price
        next_best_bid_exists = True
    else:
        # If no bids --> improving best bid by one tick should send in market.minprice
        next_best_bid_price = (market.minprice - market.ticksize)
    return (next_best_bid_exists, next_best_bid_price)

def get_best_offer(market):
    """
    Return tuple (best_offer, best_offer_price)
    
    In case there is no best offer, returns (None, market.maxprice + market.ticksize)
    """
    if len(order.active_sell_orders[market.id]) > 0:
        sell_orders = sorted(order.active_sell_orders[market.id], key = lambda x: (x.price, x.id))
        best_offer = sell_orders[0]
        best_offer_price = best_offer.price
    else:
        best_offer = None
        # If no offers --> improving best offer by one tick should send in market.maxprice
        best_offer_price = (market.maxprice + market.ticksize)
    return (best_offer, best_offer_price)

def get_next_best_offer(market):
    """
    Return tuple (next_best_offer_exists, next_best_offer_price)
    
    In case there is no best bid, returns (False, market.maxprice + market.ticksize)
    """
    next_best_offer_exists = False
    if len(order.active_sell_orders[market.id]) > 1:
        sell_orders = sorted(order.active_sell_orders[market.id], key = lambda x: (x.price, x.id))
        next_best_offer = sell_orders[1]
        next_best_offer_price = next_best_offer.price
        next_best_offer_exists = True
    else:
        # If no bids --> improving best bid by one tick should send in market.minprice
        next_best_offer_price = (market.maxprice + market.ticksize)
    return (next_best_offer_exists, next_best_offer_price)

def agent_has_bids_in_orderbook(current_agent, market):
    """ If agent has bids in orderbook --> return 1"""
    agent_has_bids_in_orderbook = 0
    if len(order.active_buy_orders[market.id]) > 0:
        buy_orders_current_agent = [o for o in order.active_buy_orders[market.id] if o.agent.name == current_agent.name]
        # If buy orders in orderbook by current_agent -->
        if len(buy_orders_current_agent) > 0:
            agent_has_bids_in_orderbook = 1
    return agent_has_bids_in_orderbook
 
def agent_has_offers_in_orderbook(current_agent, market):
    """ If agent has offers in orderbook --> return 1"""
    agent_has_offers_in_orderbook = 0
    if len(order.active_sell_orders[market.id]) > 0:
        sell_orders_current_agent = [o for o in order.active_sell_orders[market.id] if o.agent.name == current_agent.name]
        # If buy orders in orderbook by current_agent -->
        if len(sell_orders_current_agent) > 0:
            agent_has_offers_in_orderbook = 1
    return agent_has_offers_in_orderbook

def bids_agent_in_orderbook(current_agent, market):
    """ Return list bids agent in orderbook"""
    if len(order.active_buy_orders[market.id]) > 0:
        buy_orders_current_agent = [o for o in order.active_buy_orders[market.id] if o.agent.name == current_agent.name]
    else:
        buy_orders_current_agent = []
    return buy_orders_current_agent

def offers_agent_in_orderbook(current_agent, market):
    """ Return list offers agent in orderbook"""
    if len(order.active_sell_orders[market.id]) > 0:
        sell_orders_current_agent = [o for o in order.active_sell_orders[market.id] if o.agent.name == current_agent.name]
    else:
        sell_orders_current_agent = []
    return sell_orders_current_agent

def get_last_price(market):
    """"
    If there has been transaction --> return last transaction price
    
    Else --> return (market.maxprice - market.minprice) / 2
    """
    if len(transaction.history[market.id]) > 0:
        price = transaction.history[market.id][-1].price
    else:
        price = (market.maxprice - market.minprice) / 2
    return price

def get_midpoint_price(market):
    """"
    If there is best bid and best offer--> return midpoint price
    
    Else --> return 0
    """
    (best_bid, best_bid_price) = get_best_bid(market)
    (best_offer, best_offer_price) = get_best_offer(market)
    if (best_bid != None and best_offer != None):
        return (best_offer_price + best_bid_price)/2
    elif (best_bid != None and best_offer == None):
        return (market.maxprice + best_bid_price)/2
    elif (best_bid == None and best_offer != None):
        return (best_offer_price + market.minprice)/2
    else:
        return (market.maxprice + market.minprice)/2                    