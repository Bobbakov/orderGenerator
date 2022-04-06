# Import libraries -->
import random
from matplotlib import pyplot as plt
plt.rcParams["figure.figsize"] = (15, 15)

# Import modules -->
import order as ordr
import cancellation as cx
import strategies as stg

##############
# DEFINE CUSTOM STRATEGIES
##############
def only_best_bid_best_offer(current_agent, market):
    """
    This agent always want to be best bid and best offer
    Any other orders in orderbook by agent are deleted
    """
    quantity = random.randint(market.minquantity, market.maxquantity)
    (best_bid, best_bid_price) = stg.get_best_bid(market)
    (best_offer, best_offer_price) = stg.get_best_offer(market)
    
    # CHECK FOR BEST BID -->
    # If there are active buy orders -->
    if best_bid != None:
        # If trader is best bid -->
        if (best_bid.agent.name == current_agent.name):
            # LOGIC GOES WRONG HERE
            # If trader can lower price and still be best bid -->
            (next_best_bid_exists, next_best_bid_price) = stg.get_next_best_bid(market)
            
            if next_best_bid_exists:
                if (next_best_bid_price < (best_bid_price - market.ticksize)):
                    ordr.order(market, current_agent, "Buy", next_best_bid_price - market.ticksize, quantity)
                    # Cancel best bid -->
                    cx.cancellation.cancel_orders(best_bid)
            else:
                if (best_bid.price != market.minprice):
                    ordr.order(market, current_agent, "Buy", market.minprice, quantity)
                    cx.cancellation.cancel_orders(best_bid)
        # If there are no active bids in orderbook -->
        else:
            # Check if no transaction occurs by sending in best price -->
            if best_offer_price > (best_bid_price + market.ticksize):
                new_best_bid = ordr.order(market, current_agent, "Buy", best_bid_price + market.ticksize, quantity)
                ordr.order.cancel_all_bids_agent_except(market, current_agent, new_best_bid)
            
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
            ordr.order(market, current_agent, "Buy", market.minprice, quantity)
    
    # CHECK FOR BEST OFFER -->
    # If there are active sell orders -->
    if best_offer != None:
        # If trader is best offer -->
        if (best_offer.agent.name == current_agent.name):
            # If trader can lower price and still be best bid -->
            (next_best_offer_exists, next_best_offer_price) = stg.strategies.get_next_best_offer(market)
            if next_best_offer_exists:
                if (next_best_offer_price > (best_offer_price + market.ticksize)):
                    ordr.order(market, current_agent, "Sell", best_offer_price + market.ticksize, quantity)
                    # Cancel best bid -->
                    cx.cancellation.cancel_orders(best_offer) 
            else:
                if (best_offer.price != market.maxprice):
                    ordr.order(market, current_agent, "Sell", market.maxprice, quantity)
                    cx.cancellation.cancel_orders(best_offer)
            pass
        # If trader is not best offer -->
        else:
            # Check if no transaction occurs  -->
            if best_bid_price < (best_offer_price - market.ticksize):
                new_best_offer = ordr.order(market, current_agent, "Sell", best_offer_price - market.ticksize, quantity)
                ordr.order.cancel_all_offers_agent_except(market, current_agent, new_best_offer)
            
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
            ordr.order(market, current_agent, "Sell", market.maxprice, quantity)
            

# Test strategy -->
# Snipe (1) best offer or (2) best offer -->
def snipe_best_bid_or_offer(current_agent, market):
    quantity = random.randint(market.minquantity, market.maxquantity)
    (best_bid, _) = stg.strategies.get_best_bid(market)
    (best_offer, _) = stg.strategies.get_best_offer(market)
    
    # If no best_bid or best_offer
    if (best_bid == None and best_offer == None):
        pass
    elif (best_bid != None and best_offer == None):
        ordr.order(market, current_agent, "Sell", best_bid.price, quantity)
    elif (best_bid == None and best_offer != None):
        ordr.order(market, current_agent, "Buy", best_offer.price, quantity)
    else:
        buy_or_sell = random.choice(["Buy", "Sell"])
        if buy_or_sell == "Buy":
            ordr.order(market, current_agent, "Buy", best_offer.price, quantity)
        else:
            ordr.order(market, current_agent, "Sell", best_bid.price, quantity)