# Import libraries -->
import itertools

# Import modules -->
import order

# Initialize variables -->
counter = itertools.count()
history = {}

class new_cancellation():
    # Initialize cancellation -->
    def __init__(self, order):        
        self.id = next(counter)
        self.cancelled_order = order

        # Add order to cancellation history
        history[order.market.id].append(self)

class supporting_functions():
    """These functions are used to process new cancellations"""        
    def cancel_orders(orders_to_delete):
        """Delete orders from market"""
        list_orders_to_delete = orders_to_delete if ( type(orders_to_delete) == list ) else [orders_to_delete]
        if len(list_orders_to_delete) > 0:
        # If there are orders_to_delete -->
            # If orders deleted on same market -->
            market_id = list_orders_to_delete[0].market.id
            
            # Update orderbook -->
            buy_orders_to_delete = [o.id for o in list_orders_to_delete if (o.side == "Buy")]
            sell_orders_to_delete = [o.id for o in list_orders_to_delete if (o.side == "Sell")]
            order.active_buy_orders[market_id] = [o for o in order.active_buy_orders[market_id] if (o.id not in buy_orders_to_delete)]    
            order.active_sell_orders[market_id] = [o for o in order.active_sell_orders[market_id] if (o.id not in sell_orders_to_delete)]       
        
        # Delete each order in list -->
            for o in list_orders_to_delete:
                new_cancellation(o)   
        else:
            pass
    
    def cancel_all_bids_agent_except(market, current_agent, current_order):
        """Remove all bids agent except"""
        supporting_functions.cancel_orders([o for o in order.active_buy_orders[market.id] if (o.agent.name == current_agent.name and o.id != current_order.id)])
            
    def cancel_all_offers_agent_except(market, current_agent, current_order):
        """Remove all bids agent except"""
        supporting_functions.cancel_orders([o for o in order.active_sell_orders[market.id] if (o.agent.name == current_agent.name and o.id != current_order.id)])