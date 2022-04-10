# Import libraries -->
import itertools
from datetime import datetime, timedelta

# Import modules -->
import transaction

# Initialize variables -->
counter = itertools.count()
# Get datetime_counter for graphing purposes -->
history = {}
history_order = {}
active_buy_orders = {}
active_sell_orders = {}

class new_order():
    """ Send order to the market"""
    datetime_counter = datetime(2019, 1, 1, 9, 0, 0)
    # Initialize order -->
    def __init__(self, market, agent, side, price, quantity):
        self.id = next(counter)
        # Each order is 1 second apart -->
        new_order.datetime_counter += timedelta(seconds = 1)
        self.datetime = new_order.datetime_counter
        self.market = market
        self.agent = agent
        self.side = side
        # Round price to nearest ticksize -->
        price = round(price / market.ticksize) * market.ticksize
        price = float("%.2f" % (price))
        # If price out of range market --> 
        if price > market.maxprice:
            price = market.maxprice
        if price < market.minprice:
            price = market.minprice
        self.price = price
        self.quantity = quantity

        # Add order to order history -->
        history[market.id].append(self)

        # Add hardcoded values to dictionaries (If you add "self" --> values get overwritten once order is (partially) executed)
        history_order[market.id][self.id] = {"id": self.id, 
                                                   "market": market, 
                                                   "agent": agent, 
                                                   "side": side, 
                                                   "price": price, 
                                                   "quantity": quantity}

        # Check if order results in new_transaction
        # If order is buy order
        if self.side == "Buy":
            # Start loop
            remaining_quantity = self.quantity
            while True:
                # If there are active sell orders --> continue
                if not not active_sell_orders[market.id]:
                    sell_orders = sorted(active_sell_orders[market.id], key = lambda x: (x.price, x.id))
                    best_offer = sell_orders[0]

                    # If limit price buy order >= price best offer --> new_transaction
                    if self.price >= best_offer.price:
                        transaction_price = best_offer.price

                        # If quantity buy order larger quantity than best offer --> remove best offer from active orders
                        if remaining_quantity > best_offer.quantity:
                            transaction_quantity = best_offer.quantity

                            # Register transaction
                            transaction.new_transaction(self, best_offer, market, transaction_price, transaction_quantity)

                            # Remove offer from orderbook
                            remove_offer(best_offer, market)

                            # Reduce remaining quantity order
                            remaining_quantity -= transaction_quantity

                        # If quantity buy order equals quantity best offer
                        elif remaining_quantity == best_offer.quantity:
                            transaction_quantity = best_offer.quantity

                            # Register transaction
                            transaction.new_transaction(self, best_offer, market, transaction_price, transaction_quantity)

                            # Remove offer from orderbook
                            remove_offer(best_offer, market)

                            # Buy order is executed --> break loop
                            break

                        # If quantity buy order is smaller than quantity best offer --> reduce quantity best offer
                        else:
                            transaction_quantity = remaining_quantity

                            # Register transaction
                            transaction.new_transaction(self, best_offer, market, transaction_price, transaction_quantity)

                            # Reduce quantity offer
                            reduce_offer(best_offer, transaction_quantity, market)

                            # Buy order is executed --> break loop
                            break

                    # If bid price < best offer --> no transaction
                    else:
                        self.quantity = remaining_quantity

                        # Send(remaining) order to orderbook
                        active_buy_orders[market.id].append(self)
                        break

                # If there are NO active sell orders --> add order to active orders
                else:
                    self.quantity = remaining_quantity
                    active_buy_orders[market.id].append(self)
                    break

        # If order is sell order
        else:
            # Start loop
            remaining_quantity = self.quantity
            while True:
                # If there are active buy orders --> continue
                if not not active_buy_orders[market.id]:
                    buy_orders = sorted(active_buy_orders[market.id], key = lambda x: (-1 * x.price, x.id))
                    best_bid = buy_orders[0]

                    # If price best bid >= price sell order --> transaction
                    if best_bid.price >= self.price:
                        transaction_price = best_bid.price

                        # If quantity offer larger than quantity best bid
                        if remaining_quantity > best_bid.quantity:
                            transaction_quantity = best_bid.quantity

                            # Register transaction
                            transaction.new_transaction(best_bid, self, market, transaction_price, transaction_quantity)

                            # Remove bid from orderbook
                            remove_bid(best_bid, market)

                            remaining_quantity -= transaction_quantity
                        # If quantity order equals quantity best offer
                        elif remaining_quantity == best_bid.quantity:
                            transaction_quantity = best_bid.quantity

                            # Register transaction
                            transaction.new_transaction(best_bid, self, market, transaction_price, transaction_quantity)

                            # Remove best bid from orderbook
                            remove_bid(best_bid, market)

                            # Order is executed --> break loop
                            break

                        # If quantity sell order is smaller than quantity best bid
                        else:
                            transaction_quantity = remaining_quantity

                            # Register transaction
                            transaction.new_transaction(best_bid, self, market, transaction_price, transaction_quantity)

                            # Reduce quantity best bid
                            reduce_bid(best_bid, transaction_quantity, market)
                            break

                    # If best bid price < best offer price  --> no transaction
                    else:
                        self.quantity = remaining_quantity
                        active_sell_orders[market.id].append(self)
                        break

                # If there are no active buy orders --> add order to active orders
                else:
                    self.quantity = remaining_quantity
                    active_sell_orders[market.id].append(self)
                    break
    
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {}".format(self.market, self.agent.name, self.side, self.price, self.quantity)
    
""" These functions are used in processing incoming orders"""
def remove_offer(offer, market):
    """Remove offer from orderbook """
    a = active_sell_orders[market.id]
    for c, o in enumerate(a):
        if o.id == offer.id:
            del a[c]
            break

def reduce_offer(offer, transaction_quantity, market):
    """Reduce quantity offer in orderbook"""
    a = active_sell_orders[market.id]
    for c, o in enumerate(a):
        if o.id == offer.id:
            if a[c].quantity == transaction_quantity:
                remove_offer(offer, market)
            else:
                a[c].quantity -= transaction_quantity
            break


def remove_bid(bid, market):
    """Remove bid from orderbook"""
    a = active_buy_orders[market.id]
    for c, o in enumerate(a):
        if o.id == bid.id:
            del a[c]
            break


def reduce_bid(bid, transaction_quantity, market):
    """Reduce quantity bid in orderbook"""
    a = active_buy_orders[market.id]
    for c, o in enumerate(a):
        if o.id == bid.id:
            if a[c].quantity == transaction_quantity:
                remove_bid(bid, market)
            else:
                a[c].quantity -= transaction_quantity
            break   