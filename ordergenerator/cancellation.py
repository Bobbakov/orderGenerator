# Import libraries -->
import itertools

# Import modules -->
import order as ordr

class cancellation():
    counter = itertools.count()
    history = {}
    
    # Initialize cancellation -->
    def __init__(self, order):        
        self.id = next(cancellation.counter)
        self.cancelled_order = order

        # Add order to order history
        cancellation.history[order.market.id].append(self)
        
def cancel_orders(orders_to_delete):
    list_orders_to_delete = orders_to_delete if ( type(orders_to_delete) == list ) else [orders_to_delete]
    if len(list_orders_to_delete) > 0:
    # If there are orders_to_delete -->
        # If orders deleted on same market -->
        market_id = list_orders_to_delete[0].market.id
        
        # Update orderbook -->
        buy_orders_to_delete = [o.id for o in list_orders_to_delete if (o.side == "Buy")]
        sell_orders_to_delete = [o.id for o in list_orders_to_delete if (o.side == "Sell")]
        ordr.order.active_buy_orders[market_id] = [o for o in ordr.order.active_buy_orders[market_id] if (o.id not in buy_orders_to_delete)]    
        ordr.order.active_sell_orders[market_id] = [o for o in ordr.order.active_sell_orders[market_id] if (o.id not in sell_orders_to_delete)]       
    
    # Delete each order in list -->
        for o in list_orders_to_delete:
            cancellation(o)   
    else:
        pass

### METHODS
# Remove all bids agent except
def cancel_all_bids_agent_except(market, current_agent, current_order):
    cancel_orders([o for o in ordr.order.active_buy_orders[market.id] if (o.agent.name == current_agent.name and o.id != current_order.id)])
        
# Remove all offers agent except
def cancel_all_offers_agent_except(market, current_agent, current_order):
    cancel_orders([o for o in ordr.order.active_sell_orders[market.id] if (o.agent.name == current_agent.name and o.id != current_order.id)])