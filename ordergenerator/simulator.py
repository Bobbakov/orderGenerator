# Databricks notebook source
# Import libraries -->
import numpy as np
import pandas as pd
import random
import itertools
from datetime import datetime, timedelta
import time
import operator
from matplotlib import pyplot as plt
plt.rcParams["figure.figsize"] = (15, 15)

# COMMAND ----------

class order():
    counter = itertools.count()
    # Get datetime_counter for graphing purposes -->
    datetime_counter = datetime(2019, 1, 1, 9, 0, 0)
    history = {}
    history_order = {}
    active_buy_orders = {}
    active_sell_orders = {}
    cancellations = {}

    # Initialize order -->
    def __init__(self, market, agent, side, price, quantity):
        self.id = next(order.counter)
        # Each order is 1 second apart
        order.datetime_counter += timedelta(seconds = 1)
        self.datetime = order.datetime_counter
        self.market = market
        self.agent = agent
        self.side = side
        # Round price to nearest ticksize
        price = round(price / market.ticksize) * market.ticksize
        price = float("%.2f" % (price))
        # If price out of range market --> 
        if price > market.maxprice:
            price = market.maxprice
        if price < market.minprice:
            price = market.minprice
        self.price = price
        self.quantity = quantity

        # Add order to order history
        order.history[market.id].append(self)

        # Add hardcoded values to dictionaries (If you add self --> values get overwritten once order is (partially) executed)
        order.history_order[market.id][self.id] = {"id": self.id, "market": market, "agent": agent, "side": side, "price": price, "quantity": quantity}

        # Check if order results in transaction
        # If order is buy order
        if self.side == "Buy":
            # start loop
            remaining_quantity = self.quantity
            while True:
                # If there are active sell orders --> continue
                if not not order.active_sell_orders[market.id]:
                    sell_orders = sorted(order.active_sell_orders[market.id], key = lambda x: (x.price, x.id))
                    best_offer = sell_orders[0]

                    # If limit price buy order >= price best offer --> transaction
                    if self.price >= best_offer.price:
                        transaction_price = best_offer.price

                        # If quantity buy order larger quantity than best offer --> remove best offer from active orders
                        if remaining_quantity > best_offer.quantity:
                            transaction_quantity = best_offer.quantity

                            # Register transaction
                            transaction(self, best_offer, market, transaction_price, transaction_quantity)

                            # Remove offer from orderbook
                            order.remove_offer(best_offer, market)

                            # Reduce remaining quantity order
                            remaining_quantity -= transaction_quantity

                        # If quantity buy order equals quantity best offer
                        elif remaining_quantity == best_offer.quantity:
                            transaction_quantity = best_offer.quantity

                            # Register transaction
                            transaction(self, best_offer, market, transaction_price, transaction_quantity)

                            # Remove offer from orderbook
                            order.remove_offer(best_offer, market)

                            # Buy order is executed --> break loop
                            break

                            # if quantity buy order is small than quantity best offer --> reduce quantity best offer
                        else:
                            transaction_quantity = remaining_quantity

                            # Register transaction
                            transaction(self, best_offer, market, transaction_price, transaction_quantity)

                            # Reduce quantity offer
                            order.reduce_offer(best_offer, transaction_quantity, market)

                            # Buy order is executed --> break loop
                            break

                    # If bid price < best offer --> no transaction
                    else:
                        self.quantity = remaining_quantity

                        # Send(remaining) order to orderbook
                        order.active_buy_orders[market.id].append(self)
                        break

                # If there are NO active sell orders --> add order to active orders
                else:
                    self.quantity = remaining_quantity
                    order.active_buy_orders[market.id].append(self)
                    break

        # If order is sell order
        else:
            # start loop
            remaining_quantity = self.quantity
            while True:
                # if there are active buy orders --> continue
                if not not order.active_buy_orders[market.id]:
                    buy_orders = sorted(order.active_buy_orders[market.id], key = lambda x: (-1 * x.price, x.id))
                    best_bid = buy_orders[0]

                    # If price sell order <= price best bid --> transaction
                    if best_bid.price >= self.price:
                        transaction_price = best_bid.price

                        # If quantity offer larger than quantity best bid
                        if remaining_quantity > best_bid.quantity:
                            transaction_quantity = best_bid.quantity

                            # Register transaction
                            transaction(best_bid, self, market, transaction_price, transaction_quantity)

                            # Remove bid from orderbook
                            order.remove_bid(best_bid, market)

                            remaining_quantity -= transaction_quantity
                        # If quantity order equals quantity best offer
                        elif remaining_quantity == best_bid.quantity:
                            transaction_quantity = best_bid.quantity

                            # Register transaction
                            transaction(best_bid, self, market, transaction_price, transaction_quantity)

                            # Remove best bid from orderbook
                            order.remove_bid(best_bid, market)

                            # Order is executed --> break loop
                            break

                            # If quantity sell order is smaller than quantity best bid
                        else:
                            transaction_quantity = remaining_quantity

                            # Register transaction
                            transaction(best_bid, self, market, transaction_price, transaction_quantity)

                            # Reduce quantity best bid
                            order.reduce_bid(best_bid, transaction_quantity, market)
                            break

                    # If best offer price > best bid price --> no transaction
                    else:
                        self.quantity = remaining_quantity
                        order.active_sell_orders[market.id].append(self)
                        break

                # If there are no active buy orders --> add order to active orders
                else:
                    self.quantity = remaining_quantity
                    order.active_sell_orders[market.id].append(self)
                    break

    ### METHODS
    # Remove offer from orderbook
    def remove_offer(offer, market):
        a = order.active_sell_orders[market.id]
        for c, o in enumerate(a):
            if o.id == offer.id:
                del a[c]
                break

    # Reduce quantity offer in orderbook
    def reduce_offer(offer, transaction_quantity, market):
        a = order.active_sell_orders[market.id]
        for c, o in enumerate(a):
            if o.id == offer.id:
                if a[c].quantity == transaction_quantity:
                    order.remove_offer(offer, market)
                else:
                    a[c].quantity -= transaction_quantity
                break

    # Remove bid from orderbook
    def remove_bid(bid, market):
        a = order.active_buy_orders[market.id]
        for c, o in enumerate(a):
            if o.id == bid.id:
                del a[c]
                break

    # Reduce quantity bid in orderbook
    def reduce_bid(bid, transaction_quantity, market):
        a = order.active_buy_orders[market.id]
        for c, o in enumerate(a):
            if o.id == bid.id:
                if a[c].quantity == transaction_quantity:
                    order.remove_bid(bid, market)
                else:
                    a[c].quantity -= transaction_quantity
                break
    
     # Remove all bids except best id   
    def cancel_all_bids_agent_except(market, current_agent, current_order):
        cancellation.cancel_orders([o for o in order.active_buy_orders[market.id] if (o.agent.name == current_agent.name and o.id != current_order.id)])
            
    # Remove all offers except best offer 
    def cancel_all_offers_agent_except(market, current_agent, current_order):
        cancellation.cancel_orders([o for o in order.active_sell_orders[market.id] if (o.agent.name == current_agent.name and o.id != current_order.id)])

# COMMAND ----------

class cancellation():
    history = {}

    # Initialize order -->
    def __init__(self, order):
        self.id = next(order.counter)
        self.cancelled_order = order

        # Add order to order history
        cancellation.history[order.market.id].append(self)
        
    def cancel_orders(orders_to_delete):
        list_orders_to_delete = orders_to_delete if ( type(orders_to_delete) == list ) else [orders_to_delete]
        if len(list_orders_to_delete) > 0:
        # If orders_to_delete is non empty:
            # Delete each order in list -->
            for o in list_orders_to_delete:
                cancellation(o)

            # Assume each order is deleted on the same market -->
            # If orders simulateneously deleted on multiple markets --> amend code
            market_id = list_orders_to_delete[0].market.id
            # Update orderbook -->
            buy_orders_to_delete = [o.id for o in list_orders_to_delete if (o.side == "Buy")]
            sell_orders_to_delete = [o.id for o in list_orders_to_delete if (o.side == "Sell")]
            order.active_buy_orders[market_id] = [o for o in order.active_buy_orders[market_id] if (o.id not in buy_orders_to_delete)]    
            order.active_sell_orders[market_id] = [o for o in order.active_sell_orders[market_id] if (o.id not in sell_orders_to_delete)]    
        else:
            pass

# COMMAND ----------

class transaction():
    counter = itertools.count()
    history = {}
    history_list = {}
    history_market_agent = {}

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
            buy_order.agent.value_bought[market.id] += price * quantity
            buy_order.agent.quantity_bought[market.id] += quantity
            sell_order.agent.value_sold[market.id] += price * quantity
            sell_order.agent.quantity_sold[market.id] += quantity

        # Add to transaction history
        transaction.history[market.id].append(self)
        transaction.history_list[market.id].append([self.id, self.datetime.time(), self.price])

        # Add to history agent at market
        transaction.history_market_agent[market.id, buy_order.agent.name].append([self.id, buy_order.agent.position[market.id], transaction.get_realized_profit(buy_order.agent, market)])
        transaction.history_market_agent[market.id, sell_order.agent.name].append([self.id, sell_order.agent.position[market.id], transaction.get_realized_profit(sell_order.agent, market)])

    ### METHODS
    # Display transaction
    '''
    def __str__(self):
        return "{} \t {} \t {} \t {} \t {} \t {} \t {}".format(self.id, self.datetime.time(), self.market, self.buy_order.agent.name, self.sell_order.agent.name, self.price, self.quantity)
    '''

    # Calculate realized profit agent at market
    def get_realized_profit(agent, market):
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
        return print("At market {} - Best bid: {} ({}) Best offer: {} ({}) --> Transaction at: {} ({})".format(market.id, bid.price, bid.quantity, offer.price, offer.quantity, price, quantity))

# COMMAND ----------

class agent():
    counter = itertools.count()
    agents = []

    # Initialize agent
    def __init__(self, strategy, **params):
        self.name = next(agent.counter)
        
        # Strategy can be picked from class strategies or custom made
        self.strategy = strategy
        self.params = params

        # STARTS WITH EMPTY VALUES
        self.position = {}
        self.running_profit = {}
        self.value_bought = {}
        self.quantity_bought = {}
        self.value_sold = {}
        self.quantity_sold = {}
        self.stop = {}
            
        agent.agents.append(self)

    # If there has been transaction in market --> return last price. 
    # Else --> return midpoint price
    def get_last_price(market):
        if len(transaction.history[market.id]) > 0:
            price = transaction.history[market.id][-1].price
        else:
            price = (market.maxprice - market.minprice) / 2
        return price

# COMMAND ----------

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
        
        # Initialize values -->
        order.history[self.id] = []
        order.history_order[self.id] = {}
        order.active_buy_orders[self.id] = []
        order.active_sell_orders[self.id] = []
        transaction.history[self.id] = []
        transaction.history_list[self.id] = []
        cancellation.history[self.id] = []
        
        market.markets.append(self)

        # Initialize agents
        self.agents = []

        # Make sure simulations start from same feed --> that way they can be easily compared
        # random.seed(100)
        # np.random.seed(100)

    # Start agents sending in orders to market(s)
    def order_generator(self, n = 1000, print_orderbook = False, sleeptime = 0.0):
        # For each iteration
        for o in range(int(n)):
            # For each agent
            for current_agent in self.agents:
                # Take strategy agent --> execute strategy
                # Keep track of last values printed
                last_transaction_id = transaction.history[self.id][-1].id  if (len(transaction.history[self.id]) > 0) else -1
                last_order_id = max(order.history_order[self.id].keys()) if (len(order.history_order[self.id]) > 0) else -1
                last_order_cancelled_id = cancellation.history[self.id][-1].id if (len(cancellation.history[self.id]) > 0) else -1
                
                # Execute strategy
                current_agent.strategy(current_agent, self)
                
                # If print_orderbook == True --> show results
                if print_orderbook:
                    self.print_orderbook(last_transaction_id, last_order_id, last_order_cancelled_id)

                    # Slow down printing orderbook
                    time.sleep(float(sleeptime))
    
    ### METHODS
    def __str__(self):
        return "{}".format(self.id)

    # Add your agents to the market
    def add_agents(self, agents):
        for a in agents:
            self.agents.append(a)
            # Initialize values -->
            a.position[self.id] = 0
            a.value_bought[self.id] = 0
            a.quantity_bought[self.id] = 0
            a.value_sold[self.id] = 0
            a.quantity_sold[self.id] = 0                    
            transaction.history_market_agent[self.id, a.name] = []    
            
    # Empty active orders
    def clear(self):
        order.active_sell_orders[self.id] = []
        order.active_buy_orders[self.id] = []
        
    # Get last order
    def get_last_order(self):
        # If market has been activated --> get last order
        if len(order.history_order[self.id]) > 0:
            last_order_id = max(order.history_order[self.id].keys())
            last_order = order.history_order[self.id][last_order_id]
        # Else --> return 0
        else:
            last_order = 0     
        return last_order
    
    def print_last_cancellations(self, last_order_cancelled_id):
        for c in cancellation.history[self.id]:
            if c.id > last_order_cancelled_id:
                 print("Cancellation: {} by agent {} with price {} (quantity = {})".format(c.cancelled_order.side, c.cancelled_order.agent.name, c.cancelled_order.price, c.cancelled_order.quantity))
    
    # Print last transactions
    def print_last_orders(self, last_order_id):
        for counter, o in order.history_order[self.id].items():
            # Only print new orders -->
            if o["id"] > last_order_id:
                print("New order: {} by agent {} with price {} (quantity = {})".format(o["side"], o["agent"].name, o["price"], o["quantity"]))
    
    # Print last transactions
    def print_last_transactions(self, last_transaction_id, max_number_transactions = 5):
        for t in transaction.history[self.id][-max_number_transactions:]:
            # Only print new transactions -->
            if t.id > last_transaction_id:
                print("--> Trade at price {} (quantity = {}) {} from {}".format(t.price, t.quantity, t.buy_order.agent.name, t.sell_order.agent.name))
    
    def show_orderbook(self, depth = 10):
        # Show each seperate order
        width_orderbook = 33
        print(width_orderbook * 2 * "*")

        for sell_order in sorted(order.active_sell_orders[self.id], key = lambda x: (x.price, x.id), reverse=True)[(-1 * depth):]:
            print(width_orderbook * "." + " " + str(sell_order))
        for buy_order in sorted(order.active_buy_orders[self.id], key = lambda x: (-1 * x.price, x.id))[:depth]:
            print(str(buy_order) + " " + width_orderbook * ".")

        print(width_orderbook * 2 * "*")
        print(" ")

    def show_orderbook_orders_aggregated(self, depth = 10):    
        # Aggregate sell orders
        print("******************************************")
        sell_orders_aggregated = {}
        for o in sorted(order.active_sell_orders[self.id], key = lambda x: (x.price, x.id)):
            if o.price not in sell_orders_aggregated.keys():
                sell_orders_aggregated[o.price] = {"quantity": o.quantity, "number_orders": 1}
            else:
                sell_orders_aggregated[o.price]["quantity"] += o.quantity
                sell_orders_aggregated[o.price]["number_orders"] += 1

        for level in sorted(sell_orders_aggregated, reverse=True)[(-1 * depth):]:
            print(f"xxxxxxxxxxxxxxxxx\t{level}\t{sell_orders_aggregated[level]['quantity'] }\t{sell_orders_aggregated[level]['number_orders'] }")            
        # Aggregate buy orders
        buy_orders_aggregated = {}
        for o in sorted(order.active_buy_orders[self.id], key = lambda x: (-1 * x.price, x.id)):
            if o.price not in buy_orders_aggregated.keys():
                buy_orders_aggregated[o.price] = {"quantity": o.quantity, "number_orders": 1}
            else:
                buy_orders_aggregated[o.price]["quantity"] += o.quantity
                buy_orders_aggregated[o.price]["number_orders"] += 1

        for level in sorted(buy_orders_aggregated, reverse=True)[:10]:
            print(f"{level}\t{buy_orders_aggregated[level]['quantity'] }\t{buy_orders_aggregated[level]['number_orders'] }\txxxxxxxxxxxxxxxxx")    
        
        print("******************************************")
        print("                                          ")
   
    def print_orderbook(self, last_transaction_id = -1, last_order_id = -1, last_order_cancelled_id = -1):        
        # Print last cancellations
        market.print_last_cancellations(self, last_order_cancelled_id)
        
        # Print last order send in
        market.print_last_orders(self, last_order_id)

        # Print last transactions
        market.print_last_transactions(self, last_transaction_id)

        # Print orderbook
        self.show_orderbook_orders_aggregated()    
    
    def show_orders_agent(self, current_agent, depth_orderbook = 20):
        
        min_level_sell_side = min([o.price for o in order.active_sell_orders[self.id]]) if (len(order.active_sell_orders[self.id]) > 0) else self.maxprice
        max_level_buy_side = (max([o.price for o in order.active_buy_orders[self.id]]) + self.ticksize) if (len(order.active_buy_orders[self.id]) > 0) else self.minprice
        levels_sell_orders_orderbook = np.arange(min_level_sell_side, (self.maxprice + self.ticksize), self.ticksize).round(2)
        levels_buy_orders_orderbook = np.arange(self.minprice, max_level_buy_side, self.ticksize).round(2)

        # Intialize dictionaries
        sell_orders_current_agent = dict.fromkeys(levels_sell_orders_orderbook, 0)
        sell_orders_other_agents = dict.fromkeys(levels_sell_orders_orderbook, 0)

        for o in order.active_sell_orders[self.id]:
            if o.agent.name == current_agent.name:
                sell_orders_current_agent[o.price] += o.quantity
            else:
                sell_orders_other_agents[o.price] += o.quantity

        buy_orders_current_agent = dict.fromkeys(levels_buy_orders_orderbook, 0)
        buy_orders_other_agents = dict.fromkeys(levels_buy_orders_orderbook, 0)

        for o in order.active_buy_orders[self.id]:
            if o.agent.name == current_agent.name:
                buy_orders_current_agent[o.price] += o.quantity
            else:
                buy_orders_other_agents[o.price] += o.quantity        

        df_sell_orders = pd.DataFrame({"price": levels_sell_orders_orderbook, "quantity_others": sell_orders_other_agents.values(), "quantity_agent": sell_orders_current_agent.values()})
        df_buy_orders = pd.DataFrame({"price": levels_buy_orders_orderbook, "quantity_others": buy_orders_other_agents.values(), "quantity_agent": buy_orders_current_agent.values()})
        df_sell = df_sell_orders[(df_sell_orders["quantity_others"] > 0 ) | (df_sell_orders["quantity_agent"] > 0)].sort_values(by="price", ascending=False)[-depth_orderbook:]
        df_buy = df_buy_orders[(df_buy_orders["quantity_others"] > 0 ) | (df_buy_orders["quantity_agent"] > 0)].sort_values(by="price", ascending=False)[:depth_orderbook]
        # Turn buy quantity negative for visualization purposes
        df_buy[["quantity_others", "quantity_agent"]] = (df_buy[["quantity_others", "quantity_agent"]] * -1)
        df_orderbook = pd.concat([df_sell, df_buy])
        df_orderbook.plot.barh(x="price", stacked=True, figsize=(10, 10))
        plt.gca().invert_yaxis()
    
    
    ### TEMPLATE MARKETS
    # Initiate a healthy or normal market
    def healthy(self):
        a1 = agent("random_lognormal", buy_probability = 0.50)
        a2 = agent("best_bid_offer")
        a3 = agent("random_lognormal")
        a4 = agent("best_bid_offer")
        a5 = agent("best_bid_offer")
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)
    
    # Initiate a healthy or normal market
    def test(self):
        a1 = agent(strategies.random_lognormal, buy_probability = 0.50)
        a2 = agent(strategies.best_bid_offer)
        a3 = agent(strategies.random_lognormal)
        a4 = agent(strategies.best_bid_offer)
        a5 = agent(strategies.best_bid_offer)
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)
        
    def test2(self):
        a1 = agent(strategies.random_lognormal, buy_probability = 0.50)
        a2 = agent(only_best_bid_best_offer)
        agents = [a2, a1]
        self.add_agents(agents)
    
    # Initiate a stressed market (= high volatility)
    def stressed(self):
        a1 = agent("random_lognormal")
        a2 = agent("random_lognormal")
        a3 = agent("random_lognormal")
        a4 = agent("random_lognormal")
        a5 = agent("random_lognormal")
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)

    # Initiate a trending (up) market
    def trend_up(self):
        a1 = agent("random_lognormal", buy_probability = 0.55)
        a2 = agent("best_bid_offer")
        a3 = agent("random_lognormal")
        a4 = agent("best_bid_offer")
        a5 = agent("best_bid_offer")
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)

    # Initiate a trending (down) market
    def trend_down(self):
        a1 = agent("random_lognormal", buy_probability = 0.45)
        a2 = agent("best_bid_offer")
        a3 = agent("random_lognormal")
        a4 = agent("best_bid_offer")
        a5 = agent("best_bid_offer")
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)    

    ### PLOTTING
    # Plot price over time
    def plot_price(self, skip_first_transactions = 0, skip_last_transactions_after = 99999):
        df = pd.DataFrame(transaction.history_list[self.id], columns = ["id", "time", "price"])
        df = df[["id", "price"]]
        df = df[(df["id"] > skip_first_transactions) & (df["id"] < skip_last_transactions_after)]
        df = df.set_index("id")

        return df.plot()

    # Plot position (+ profits) all agents
    def plot_positions(self, agents = []):
        if len(agents) == 0:
            agents = [a.name for a in self.agents]
        for a in self.agents:
            if a.name in agents:
                df = pd.DataFrame(transaction.history_market_agent[self.id, a.name], columns = ["id", "running_position", "running_profit"])
                df = df.set_index("id")
                df_running_position = df["running_position"]
                plt.plot(df_running_position, label = "{} ({})".format(str(a.name), str(a.strategy)))
                plt.plot()
        plt.legend()
        return plt.show()

    # Plot profitsall agents
    def plot_profits(self, agents = []):
        if len(agents) == 0:
            agents = [a.name for a in self.agents]
        for a in self.agents:
            if a.name in agents:
                df = pd.DataFrame(transaction.history_market_agent[self.id, a.name], columns = ["id", "running_position", "running_profit"])
                df = df.set_index("id")
                df_running_profit = df["running_profit"]
                plt.plot(df_running_profit, label = "{} ({})".format(str(a.name), str(a.strategy)))
                plt.plot()
        plt.legend()
        return plt.show()
    
    '''
    def summary(self):
        df = pd.DataFrame(transaction.history_list[self.id], columns = ["id", "time", "price"])
        df["volatility"] = df["price"].rolling(7).std()
        df["volatility_trend"] = df["volatility"].rolling(100).mean()
        df = df[["id", "price", "volatility", "volatility_trend"]]
        df = df.set_index("id")

        df_price = df["price"]
        df_volatility = df[["volatility", "volatility_trend"]]

        # PLOT PRICE
        fig, axs = plt.subplots(2, 2)
        axs[0, 0].plot(df_price, label = "price")
        axs[0, 0].set_title("Price")
        axs[0, 0].legend()

        # PLOT VOLATILITY
        axs[0, 1].plot(df_volatility)
        axs[0, 1].set_title("Volatility")
        axs[0, 1].legend()

        # PLOT RUNNING POSITIONS + RUNNING PROFITS AGENTS
        for a in self.agents:
            right = pd.DataFrame(transaction.history_market_agent[self.id, a.name], columns = ["id", a.name, str(a.name) + "running_profit"])
            right = right.set_index("id")
            right = right[a.name]
            axs[1, 0].plot(right, label = str(a.name))
        axs[1, 0].set_title("Positions")

        if len(self.agents) < 20:
            axs[1, 0].legend()

        for a in self.agents:
            right = pd.DataFrame(transaction.history_market_agent[self.id, a.name],
                                 columns = ["id", a.name, str(a.name) + "running_profit"])
            right = right.set_index("id")
            right = right[str(a.name) + "running_profit"]
            axs[1, 1].plot(right, label = str(a.name) + "running_profit")

        axs[1, 1].set_title("Running profit")

        return plt.show()
    '''

# COMMAND ----------

class strategies():
    ################# 
    # DEFINE SUPPORTING FUNCTIONS
    #################
    def get_best_bid(market):
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
    
    def get_next_best_offer(market):
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
    
    def get_best_offer(market):
        if len(order.active_sell_orders[market.id]) > 0:
            sell_orders = sorted(order.active_sell_orders[market.id], key = lambda x: (x.price, x.id))
            best_offer = sell_orders[0]
            best_offer_price = best_offer.price
        else:
            best_offer = None
            # If no offers --> improving best offer by one tick should send in market.maxprice
            best_offer_price = (market.maxprice + market.ticksize)
        return (best_offer, best_offer_price)
    
    def agent_has_bids_in_orderbook(current_agent, market):
        agent_has_bids_in_orderbook = 0
        if len(order.active_buy_orders[market.id]) > 1:
            buy_orders_current_agent = [o for o in order.active_buy_orders[market.id] if o.agent.name == current_agent.name]
            # If buy orders in orderbook by current_agent -->
            if len(buy_orders_current_agent) > 0:
                agent_has_bids_in_orderbook = 1
        return agent_has_bids_in_orderbook
     
    def agent_has_offers_in_orderbook(current_agent, market):
        agent_has_offers_in_orderbook = 0
        if len(order.active_sell_orders[market.id]) > 1:
            sell_orders_current_agent = [o for o in order.active_sell_orders[market.id] if o.agent.name == current_agent.name]
            # If buy orders in orderbook by current_agent -->
            if len(sell_orders_current_agent) > 0:
                agent_has_offers_in_orderbook = 1
        return agent_has_offers_in_orderbook
    
    ################# 
    # DEFINE STRATEGIES
    #################
    def random_uniform(current_agent, market):
        side = random.choice(["Buy", "Sell"])
        price = np.arange(market.minprice, market.maxprice + market.ticksize, market.ticksize)
        price = np.random.choice(price)
        quantity = random.randint(market.minquantity, market.maxquantity)

        # Send order to market
        order(market, current_agent, side, price, quantity)

    # Randomly choose Buy/Sell order with price from normal distribution
    def random_normal(current_agent, market):
        side = random.choice(["Buy", "Sell"])
        last_price = agent.get_last_price(market)
        std = 0.1 * last_price
        price = np.random.normal(last_price, std)
        quantity = random.randint(market.minquantity, market.maxquantity)

        # Send order to market
        order(market, current_agent, side, price, quantity)

    # Randomly choose Buy/Sell order with price from lognormal distribution
    def random_lognormal(current_agent, market, buy_probability = 0.5):

        if "buy_probability" in current_agent.params.keys():
            buy_probability = current_agent.params["buy_probability"]

        sell_probability = 1 - buy_probability
        side = np.random.choice(["Buy", "Sell"], p = [buy_probability, sell_probability])
        last_price = agent.get_last_price(market)
        price = last_price * np.random.lognormal(0, 0.2)
        quantity = random.randint(market.minquantity, market.maxquantity)

        # Send order to market
        order(market, current_agent, side, price, quantity)

    ###############################################################################
    # AGENT: MARKET MAKER
    ###############################################################################
    # Agents always tries to be best bid and best offer at market. If he is not --> he improves price by 1 tick.
    # If position limit is exceeded --> agent closes position at market (in case position > 0) or buys back all shorts (in case position < 0)
    def best_bid_offer(current_agent, market):
        quantity = random.randint(market.minquantity, market.maxquantity)

        # If agent has position_limit --> check if limit is exceeded
        if "position_limit" in current_agent.params.keys():
            position_limit = current_agent.params["position_limit"]
            if current_agent.position[market.id] > position_limit:
                order(market, current_agent, "Sell", market.minprice, abs(current_agent.position[market.id]))
            elif current_agent.position[market.id] < -1 * position_limit:
                order(market, current_agent, "Buy", market.maxprice, abs(current_agent.position[market.id]))

        # If there are active buy orders --> improve best bid by one tick
        (best_bid, best_bid_price) = strategies.get_best_bid(market) 
        if best_bid != None:
            if not best_bid.agent.name == current_agent.name:
                order(market, current_agent, "Buy", best_bid.price + market.ticksize, quantity)
            else:
                pass
        # If no buy orders active in market --> start the market
        else:
            order(market, current_agent, "Buy", market.minprice, quantity)
        
        (best_offer, best_offer_price) = strategies.get_best_offer(market) 
        # If there are active sell orders --> improve best offer by one tick
        if best_offer != None:
            # If trader is not best offer --> improve best offer
            if not best_offer.agent.name == current_agent.name:
                order(market, current_agent, "Sell", best_offer.price - market.ticksize, quantity)
            else:
                pass
        # Else --> create best bid
        else:
            order(market, current_agent, "Sell", market.maxprice, quantity)

    ###############################################################################
    # AGENT: ARBITRAGE (BETWEEN MARKETS)
    ###############################################################################
    # If price at marketB is lower than best_bid at marketA --> agents buys best_offer at MarketB and sells to best_bid at marketA.
    # The same goes the other way around.
    # Ignore for now -->
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
    ###############################################################################
    # AGENT: ADD strategies TO ARRAY
    ###############################################################################
    strategies = [random_uniform, random_normal, random_lognormal, best_bid_offer]
    '''
    strategies_name = ["random_uniform", "random_normal", "random_lognormal", "best_bid_offer"]
    strategies_dictionary = {}

    for i, x in enumerate(strategies_name):
        if (i % 2 == 0):
            strategies_dictionary[x] = {"strategy": strategies[i], "linestyle": "dotted"}
        else:
            strategies_dictionary[x] = {"strategy": strategies[i], "linestyle": "solid"}
    '''

# COMMAND ----------

##############
# DEFINE CUSTOM STRATEGIES
##############
def only_best_bid_best_offer(current_agent, market):
    """
    This agent always want to be best bid and best offer
    Any other orders in orderbook by agent are deleted
    """
    quantity = random.randint(market.minquantity, market.maxquantity)
    (best_bid, best_bid_price) = strategies.get_best_bid(market)
    (best_offer, best_offer_price) = strategies.get_best_offer(market)
    
    # CHECK FOR BEST BID -->
    # If there are active buy orders -->
    if best_bid != None:
        # If trader is best bid -->
        if (best_bid.agent.name == current_agent.name):
            # LOGIC GOES WRONG HERE
            # If trader can lower price and still be best bid -->
            (next_best_bid_exists, next_best_bid_price) = strategies.get_next_best_bid(market)
            
            if next_best_bid_exists:
                if (next_best_bid_price < (best_bid_price - market.ticksize)):
                    order(market, current_agent, "Buy", next_best_bid_price - market.ticksize, quantity)
                    # Cancel best bid -->
                    cancellation.cancel_orders(best_bid)
            else:
                if (best_bid.price != market.minprice):
                    order(market, current_agent, "Buy", market.minprice, quantity)
                    cancellation.cancel_orders(best_bid)
        # If there are no active bids in orderbook -->
        else:
            # Check if no transaction occurs by sending in best price -->
            if best_offer_price > (best_bid_price + market.ticksize):
                new_best_bid = order(market, current_agent, "Buy", best_bid_price + market.ticksize, quantity)
                order.cancel_all_bids_agent_except(market, current_agent, new_best_bid)
            
            '''
            # Else --> join best bid
            else:
                new_best_bid = order(market, current_agent, "Buy", best_bid_price, quantity)        
                order.cancel_all_bids_agent_except(market, current_agent, new_best_bid)
            '''
    # If no active buy orders  -->
    else:
        # If no transaction occurs by sending in bid -->
        if best_offer_price > market.minprice:
            order(market, current_agent, "Buy", market.minprice, quantity)
    
    # CHECK FOR BEST OFFER -->
    # If there are active sell orders -->
    if best_offer != None:
        # If trader is best offer -->
        if (best_offer.agent.name == current_agent.name):
            # If trader can lower price and still be best bid -->
            (next_best_offer_exists, next_best_offer_price) = strategies.get_next_best_offer(market)
            if next_best_offer_exists:
                if (next_best_offer_price > (best_offer_price + market.ticksize)):
                    order(market, current_agent, "Sell", best_offer_price + market.ticksize, quantity)
                    # Cancel best bid -->
                    cancellation.cancel_orders(best_offer) 
            else:
                if (best_offer.price != market.maxprice):
                    order(market, current_agent, "Sell", market.maxprice, quantity)
                    cancellation.cancel_orders(best_offer)
            pass
        # If trader is not best offer -->
        else:
            # Check if no transaction occurs  -->
            if best_bid_price < (best_offer_price - market.ticksize):
                new_best_offer = order(market, current_agent, "Sell", best_offer_price - market.ticksize, quantity)
                order.cancel_all_offers_agent_except(market, current_agent, new_best_offer)
            
            '''
            # Else --> join best offer
            else:
                new_best_offer = order(market, current_agent, "Sell", best_offer_price, quantity)
                order.cancel_all_offers_agent_except(market, current_agent, new_best_offer)
            '''    
    # If no active sell orders -->
    else:
         # If no transaction occurs by sending in offer -->
        if (best_bid_price < market.maxprice):
            order(market, current_agent, "Sell", market.maxprice, quantity)
            

# Test strategy -->
# Snipe (1) best offer or (2) best offer -->
def snipe_best_bid_or_offer(current_agent, market):
    quantity = random.randint(market.minquantity, market.maxquantity)
    (best_bid, _) = strategies.get_best_bid(market)
    (best_offer, _) = strategies.get_best_offer(market)
    
    # If no best_bid or best_offer
    if (best_bid == None and best_offer == None):
        pass
    elif (best_bid != None and best_offer == None):
        order(market, current_agent, "Sell", best_bid.price, quantity)
    elif (best_bid == None and best_offer != None):
        order(market, current_agent, "Buy", best_offer.price, quantity)
    else:
        buy_or_sell = random.choice(["Buy", "Sell"])
        if buy_or_sell == "Buy":
            order(market, current_agent, "Buy", best_offer.price, quantity)
        else:
            order(market, current_agent, "Sell", best_bid.price, quantity)
