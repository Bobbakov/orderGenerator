import ordergenerator as og

# initialize a market
a = og.market(minprice = 100, maxprice = 1000, ticksize = 1, minquantity = 10, maxquantity = 1000)


# initialize agents
agent1 = og.agent("randomLogNormal") # initialize agent1 with strategy "randomLogNormal"
agent2 = og.agent("randomLogNormal", buy_probability = 0.6) # initialize agent with strategy "randomLogNormal" that buys with probability 0.6 (and sells with probability 0.4). This causes an upwards tendency in the price.
agent3 = og.agent("bestBidOffer") # initialize agent2 with strategy "bestBidOffer" (= market maker)
agent4 = og.agent("bestBidOffer", position_limit = 100) # a market maker with position limit = 100

# add agents
a.addAgents([agent1, agent2, agent3, agent4])

# run the market for 1000 ticks
a.orderGenerator()

# summarize
a.summary()

