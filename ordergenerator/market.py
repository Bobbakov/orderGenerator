# Import libraries -->
import itertools
import random
import numpy as np 
import time
import pandas as pd
from matplotlib import pyplot as plt
plt.rcParams["figure.figsize"] = (10, 10)

# Import modules -->
import order as ordr
import transaction as tr
import cancellation as cx
import agent as ag
import strategies as stg
import strategies_custom as stg_cust

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
        ordr.order.history[self.id] = []
        ordr.order.history_order[self.id] = {}
        ordr.order.active_buy_orders[self.id] = []
        ordr.order.active_sell_orders[self.id] = []
        tr.transaction.history[self.id] = []
        tr.transaction.history_list[self.id] = []
        
        cx.cancellation.history[self.id] = []
        
        market.markets.append(self)

        # Initialize agents
        self.agents = []

        # Make sure simulations start from same feed --> that way they can be easily compared
        random.seed(100)
        np.random.seed(100)

    # Start agents sending in orders to market(s)
    def order_generator(self, n = 100, print_orderbook = True, sleeptime = 0.0):
        # For each iteration
        for o in range(int(n)):
            # For each agent
            for current_agent in self.agents:
                # Take strategy agent --> execute strategy
                # Keep track of last values printed
                last_transaction_id = tr.transaction.history[self.id][-1].id  if (len(tr.transaction.history[self.id]) > 0) else -1
                last_order_id = max(ordr.order.history_order[self.id].keys()) if (len(ordr.order.history_order[self.id]) > 0) else -1
                last_order_cancelled_id = cx.cancellation.history[self.id][-1].id if (len(cx.cancellation.history[self.id]) > 0) else -1
                
                # Execute strategy
                current_agent.strategy(current_agent, self)
                
                # If print_orderbook == True --> show results
                if print_orderbook:
                    display_functions.print_orderbook(self, last_transaction_id, last_order_id, last_order_cancelled_id)

                    # Slow down printing orderbook
                    time.sleep(float(sleeptime))
    
    def __str__(self):
        return "{}".format(self.id)
    
    ### METHODS
    # Add agents to the market
    def add_agents(self, agents):
        for a in agents:
            self.agents.append(a)
            # Initialize values -->
            a.position[self.id] = 0
            a.value_bought[self.id] = 0
            a.quantity_bought[self.id] = 0
            a.value_sold[self.id] = 0
            a.quantity_sold[self.id] = 0                    
            tr.transaction.history_market_agent[self.id, a.name] = []    
    
class display_functions(): 
    # Empty active orders
    def clear(market):
        ordr.order.active_sell_orders[market.id] = []
        ordr.order.active_buy_orders[market.id] = []
        
    # Get last order
    def get_last_order(market):
        # If market has been activated --> get last order
        if len(ordr.order.history_order[market.id]) > 0:
            last_order_id = max(ordr.order.history_order[market.id].keys())
            last_order = ordr.order.history_order[market.id][last_order_id]
        # Else --> return 0
        else:
            last_order = 0     
        return last_order
    
    def print_last_cancellations(market, last_order_cancelled_id):
        for c in cx.cancellation.history[market.id]:
            if c.id > last_order_cancelled_id:
                 print("Cancellation: {} by agent {} with price {} (quantity = {})".format(c.cancelled_order.side, 
                                                                                           c.cancelled_order.agent.name, 
                                                                                           c.cancelled_order.price, 
                                                                                           c.cancelled_order.quantity))
    
    # Print last transactions
    def print_last_orders(market, last_order_id):
        for counter, o in ordr.order.history_order[market.id].items():
            # Only print new orders -->
            if o["id"] > last_order_id:
                print("New order: {} by agent {} with price {} (quantity = {})".format(o["side"], 
                                                                                       o["agent"].name, 
                                                                                       o["price"], 
                                                                                       o["quantity"]))
    
    # Print last transactions
    def print_last_transactions(market, last_transaction_id, max_number_transactions = 5):
        for t in tr.transaction.history[market.id][-max_number_transactions:]:
            # Only print new transactions -->
            if t.id > last_transaction_id:
                print("--> Trade at price {} (quantity = {}) {} from {}".format(t.price, 
                                                                                t.quantity, 
                                                                                t.buy_order.agent.name, 
                                                                                t.sell_order.agent.name))
    
    def show_orderbook(market, depth = 10):
        # Show each seperate order
        width_orderbook = 33
        print(width_orderbook * 2 * "*")

        for sell_order in sorted(ordr.order.active_sell_orders[market.id], key = lambda x: (x.price, x.id), reverse=True)[(-1 * depth):]:
            print(width_orderbook * "." + " " + str(sell_order))
        for buy_order in sorted(ordr.order.active_buy_orders[market.id], key = lambda x: (-1 * x.price, x.id))[:depth]:
            print(str(buy_order) + " " + width_orderbook * ".")

        print(width_orderbook * 2 * "*")
        print(" ")

    def show_orderbook_orders_aggregated(market, depth = 10):    
        # Aggregate sell orders
        print("******************************************")
        sell_orders_aggregated = {}
        for o in sorted(ordr.order.active_sell_orders[market.id], key = lambda x: (x.price, x.id)):
            if o.price not in sell_orders_aggregated.keys():
                sell_orders_aggregated[o.price] = {"quantity": o.quantity, 
                                                   "number_orders": 1}
            else:
                sell_orders_aggregated[o.price]["quantity"] += o.quantity
                sell_orders_aggregated[o.price]["number_orders"] += 1

        for level in sorted(sell_orders_aggregated, reverse=True)[(-1 * depth):]:
            print(f"xxxxxxxxxxxxxxxxx\t{level}\t{sell_orders_aggregated[level]['quantity'] }\t{sell_orders_aggregated[level]['number_orders'] }")            
        # Aggregate buy orders
        buy_orders_aggregated = {}
        for o in sorted(ordr.order.active_buy_orders[market.id], key = lambda x: (-1 * x.price, x.id)):
            if o.price not in buy_orders_aggregated.keys():
                buy_orders_aggregated[o.price] = {"quantity": o.quantity, 
                                                  "number_orders": 1}
            else:
                buy_orders_aggregated[o.price]["quantity"] += o.quantity
                buy_orders_aggregated[o.price]["number_orders"] += 1

        for level in sorted(buy_orders_aggregated, reverse=True)[:10]:
            print(f"{level}\t{buy_orders_aggregated[level]['quantity'] }\t{buy_orders_aggregated[level]['number_orders'] }\txxxxxxxxxxxxxxxxx")    
        
        print("******************************************")
        print("                                          ")
   
    def print_orderbook(market, last_transaction_id = -1, last_order_id = -1, last_order_cancelled_id = -1):        
        # Print last cancellations
        display_functions.print_last_cancellations(market, last_order_cancelled_id)
        
        # Print last order send in
        display_functions.print_last_orders(market, last_order_id)

        # Print last transactions
        display_functions.print_last_transactions(market, last_transaction_id)

        # Print orderbook
        display_functions.show_orderbook_orders_aggregated(market)    
    
    def show_orders_agent(market, current_agent, depth_orderbook = 20):        
        min_level_sell_side = min([o.price for o in ordr.order.active_sell_orders[market.id]]) if (len(ordr.order.active_sell_orders[market.id]) > 0) else market.maxprice
        max_level_buy_side = (max([o.price for o in ordr.order.active_buy_orders[market.id]]) + market.ticksize) if (len(ordr.order.active_buy_orders[market.id]) > 0) else market.minprice
        levels_sell_orders_orderbook = np.arange(min_level_sell_side, (market.maxprice + market.ticksize), market.ticksize).round(2)
        levels_buy_orders_orderbook = np.arange(market.minprice, max_level_buy_side, market.ticksize).round(2)

        # Intialize dictionaries
        sell_orders_current_agent = dict.fromkeys(levels_sell_orders_orderbook, 0)
        sell_orders_other_agents = dict.fromkeys(levels_sell_orders_orderbook, 0)

        for o in ordr.order.active_sell_orders[market.id]:
            if o.agent.name == current_agent.name:
                sell_orders_current_agent[o.price] += o.quantity
            else:
                sell_orders_other_agents[o.price] += o.quantity

        buy_orders_current_agent = dict.fromkeys(levels_buy_orders_orderbook, 0)
        buy_orders_other_agents = dict.fromkeys(levels_buy_orders_orderbook, 0)

        for o in ordr.order.active_buy_orders[market.id]:
            if o.agent.name == current_agent.name:
                buy_orders_current_agent[o.price] += o.quantity
            else:
                buy_orders_other_agents[o.price] += o.quantity        

        df_sell_orders = pd.DataFrame({"price": levels_sell_orders_orderbook, 
                                       "quantity_others": sell_orders_other_agents.values(), 
                                       "quantity_agent": sell_orders_current_agent.values()})
        df_buy_orders = pd.DataFrame({"price": levels_buy_orders_orderbook, 
                                      "quantity_others": buy_orders_other_agents.values(), 
                                      "quantity_agent": buy_orders_current_agent.values()})
        
        df_sell = (df_sell_orders[(df_sell_orders["quantity_others"] > 0 ) | (df_sell_orders["quantity_agent"] > 0)]
                                .sort_values(by="price", ascending=False)[-depth_orderbook:])
        df_buy = (df_buy_orders[(df_buy_orders["quantity_others"] > 0 ) | (df_buy_orders["quantity_agent"] > 0)]
                                .sort_values(by="price", ascending=False)[:depth_orderbook])
        # Turn buy quantity negative for visualization purposes
        df_buy[["quantity_others", "quantity_agent"]] = (df_buy[["quantity_others", "quantity_agent"]] * -1)
        df_orderbook = pd.concat([df_sell, df_buy])
        df_orderbook.plot.barh(x="price", stacked=True, figsize=(10, 10))
        plt.gca().invert_yaxis()
    
class template_markets():
    ### TEMPLATE MARKETS
    # Initiate a healthy or normal market
    '''  
    def healthy(self):
        a1 = ag.agent(random_lognormal, buy_probability = 0.50)
        a2 = ag.agent("best_bid_offer")
        a3 = ag.agent("random_lognormal")
        a4 = ag.agent("best_bid_offer")
        a5 = ag.agent("best_bid_offer")
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)
    '''
    # Initiate a healthy or normal market
    def test(market):
        a1 = ag.agent(stg.strategies[2], buy_probability = 0.50)
        a2 = ag.agent(stg.strategies[3])
        a3 = ag.agent(stg.strategies[2])
        a4 = ag.agent(stg.strategies[3])
        a5 = ag.agent(stg.strategies[3])
        agents = [a1, a2, a3, a4, a5]
        market.add_agents(agents)
        
    def test2(self):
        a1 = ag.agent(stg.strategies.random_lognormal, buy_probability = 0.50)
        a2 = ag.agent(stg_cust.only_best_bid_best_offer)
        agents = [a2, a1]
        self.add_agents(agents)
    
    # Initiate a stressed market (= high volatility)
    def stressed(self):
        a1 = ag.agent("random_lognormal")
        a2 = ag.agent("random_lognormal")
        a3 = ag.agent("random_lognormal")
        a4 = ag.agent("random_lognormal")
        a5 = ag.agent("random_lognormal")
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)

    # Initiate a trending (up) market
    def trend_up(self):
        a1 = ag.agent("random_lognormal", buy_probability = 0.55)
        a2 = ag.agent("best_bid_offer")
        a3 = ag.agent("random_lognormal")
        a4 = ag.agent("best_bid_offer")
        a5 = ag.agent("best_bid_offer")
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)

    # Initiate a trending (down) market
    def trend_down(self):
        a1 = ag.agent("random_lognormal", buy_probability = 0.45)
        a2 = ag.agent("best_bid_offer")
        a3 = ag.agent("random_lognormal")
        a4 = ag.agent("best_bid_offer")
        a5 = ag.agent("best_bid_offer")
        agents = [a1, a2, a3, a4, a5]
        self.add_agents(agents)    

class show_results():
    ### PLOTTING
    # Plot price over time
    def plot_price(market, skip_first_transactions = 0, skip_last_transactions_after = 99999):
        df = pd.DataFrame(tr.transaction.history_list[market.id], columns = ["id", 
                                                                           "time", 
                                                                           "price"])
        df = df[["id", "price"]]
        df = df[(df["id"] > skip_first_transactions) & (df["id"] < skip_last_transactions_after)]
        df = df.set_index("id")

        return df.plot()

    # Plot position (+ profits) all agents
    def plot_positions(market, agents = []):
        if len(agents) == 0:
            agents = [a.name for a in market.agents]
        for a in market.agents:
            if a.name in agents:
                df = pd.DataFrame(tr.transaction.history_market_agent[market.id, a.name], columns = ["id", 
                                                                                                   "running_position", 
                                                                                                   "running_profit"])
                df = df.set_index("id")
                df_running_position = df["running_position"]
                plt.plot(df_running_position, label = "{} ({})".format(str(a.name), str(a.strategy)))
                plt.plot()
        plt.legend()
        return plt.show()

    # Plot profitsall agents
    def plot_profits(market, agents = []):
        if len(agents) == 0:
            agents = [a.name for a in market.agents]
        for a in market.agents:
            if a.name in agents:
                df = pd.DataFrame(tr.transaction.history_market_agent[market.id, a.name], columns = ["id", 
                                                                                       "running_position", 
                                                                                       "running_profit"])
                df = df.set_index("id")
                df_running_profit = df["running_profit"]
                plt.plot(df_running_profit, label = "{} ({})".format(str(a.name), str(a.strategy)))
                plt.plot()
        plt.legend()
        return plt.show()
    

    def summary(market):
        df = pd.DataFrame(tr.transaction.history_list[market.id], columns = ["id", 
                                                                             "time", 
                                                                             "price"])
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
        for a in market.agents:
            right = pd.DataFrame(tr.transaction.history_market_agent[market.id, a.name], columns = ["id", 
                                                                                                    a.name, 
                                                                                                    str(a.name) + "running_profit"])
            right = right.set_index("id")
            right = right[a.name]
            axs[1, 0].plot(right, label = str(a.name))
        axs[1, 0].set_title("Positions")

        if len(market.agents) < 20:
            axs[1, 0].legend()

        for a in market.agents:
            right = pd.DataFrame(tr.transaction.history_market_agent[market.id, a.name],
                                 columns = ["id", a.name, str(a.name) + "running_profit"])
            right = right.set_index("id")
            right = right[str(a.name) + "running_profit"]
            axs[1, 1].plot(right, label = str(a.name) + "running_profit")

        axs[1, 1].set_title("Running profit")

        return plt.show()