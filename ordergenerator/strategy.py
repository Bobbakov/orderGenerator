import random
import numpy as np
import operator

from .agent import agent
from .order import order

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
        side = np.random.choice(["Buy", "Sell"], p = [buy_probability, sell_probability])
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
                    order(market, agentId, "Buy", agent.getLastPriceOrElse(market) * 2,
                          abs(agentId.position[market.id]))

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
                        buyOrdersMarketA = sorted(order.activeBuyOrders[marketA.id], key = operator.attrgetter("price"),
                                                  reverse = True)
                        bestBidMarketA = buyOrdersMarketA[0]

                        sellOrdersMarketB = sorted(order.activeSellOrders[marketB.id],
                                                   key = operator.attrgetter("price"), reverse = False)
                        bestOfferMarketB = sellOrdersMarketB[0]

                        if bestBidMarketA.price > bestOfferMarketB.price:
                            order(marketB, agentId, "Buy", bestOfferMarketB.price, bestOfferMarketB.quantity)
                            order(marketA, agentId, "Sell", bestBidMarketA.price, bestBidMarketA.quantity)
        # The other way around
        if marketA.id in order.activeSellOrders.keys():
            if not not order.activeSellOrders[marketA.id]:
                if marketB.id in order.activeBuyOrders.keys():
                    if not not order.activeBuyOrders[marketB.id]:
                        sellOrdersMaketA = sorted(order.activeSellOrders[marketA.id],
                                                  key = operator.attrgetter("price"), reverse = False)
                        bestOfferMarketA = sellOrdersMaketA[0]

                        buyOrdersMarketB = sorted(order.activeBuyOrders[marketB.id], key = operator.attrgetter("price"),
                                                  reverse = True)
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
        if (i % 2 == 0):
            strategiesDict[x] = {"strategy": strategies[i], "linestyle": "dotted"}
        else:
            strategiesDict[x] = {"strategy": strategies[i], "linestyle": "solid"}
