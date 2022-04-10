# Import libraries -->
import itertools

# Initialize variables -->
counter = itertools.count()
history = {}
history_list = {}
history_market_agent = {}
 
class new_transaction():
    """Register new transaction"""
    # Initialize transaction
    def __init__(self, buy_order, sell_order, market, price, quantity):
        market.transaction_counter += 1
        self.id = market.transaction_counter
        # Time of transaction is equal to time last order send in
        self.datetime = max(buy_order.datetime, sell_order.datetime)
        self.market = market
        self.buy_order = buy_order
        self.sell_order = sell_order
        self.price = price
        self.quantity = quantity

        # Update values agents at market
        # If agent buys from himself --> ignore (otherwise calculation of realized profit goes wrong)
        if buy_order.agent.name != sell_order.agent.name:
            buy_order.agent.position[market.id] += quantity
            sell_order.agent.position[market.id] -= quantity
            buy_order.agent.value_bought[market.id] += (price * quantity)
            buy_order.agent.quantity_bought[market.id] += quantity
            sell_order.agent.value_sold[market.id] += (price * quantity)
            sell_order.agent.quantity_sold[market.id] += quantity

        # Add to transaction history
        history[market.id].append(self)
        history_list[market.id].append([self.id, self.datetime.time(), self.price])

        # Add to history agent at market
        history_market_agent[market.id, buy_order.agent.name].append([self.id, 
                                                                      buy_order.agent.position[market.id], 
                                                                      supporting_functions.get_realized_profit(buy_order.agent, market)])
        history_market_agent[market.id, sell_order.agent.name].append([self.id, 
                                                                       sell_order.agent.position[market.id], 
                                                                       supporting_functions.get_realized_profit(sell_order.agent, market)])


    '''
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {} \t {} \t {}".format(self.id, 
                                                               self.datetime.time(), 
                                                               self.market, 
                                                               self.buy_order.agent.name, 
                                                               self.sell_order.agent.name, 
                                                               self.price, 
                                                               self.quantity)
    '''
class supporting_functions():
    """These functions are used in registering new transactions"""
    def get_realized_profit(agent, market):
        """Get realized profit by agent at market"""
        ask_vwap = 0
        bid_vwap = 0
        quantity_sold = 0
        quantity_bought = 0
        if agent.quantity_sold[market.id] > 0:
            ask_vwap = agent.value_sold[market.id] / agent.quantity_sold[market.id]
            quantity_sold = agent.quantity_sold[market.id]
    
        if agent.quantity_bought[market.id] > 0:
            bid_vwap = agent.value_bought[market.id] / agent.quantity_bought[market.id]
            quantity_bought = agent.quantity_bought[market.id]
    
        realized_quantity = min(quantity_sold, quantity_bought)
        realized_profit = realized_quantity * (ask_vwap - bid_vwap)
        return realized_profit
    
    def transaction_description(bid, offer, market, price, quantity):
        return print("At market {} - Best bid: {} ({}) Best offer: {} ({}) --> Transaction at: {} ({})".format(market.id, 
                                                                                                               bid.price, 
                                                                                                               bid.quantity, 
                                                                                                               offer.price, 
                                                                                                               offer.quantity, 
                                                                                                               price, 
                                                                                                               quantity))