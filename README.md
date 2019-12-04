# orderGenerator
## This library allows the user to create order-based financial markets, add agents, and evaluate the effects of combinations of agents on measures such as volatility, agents-profits and more.


## What the project does
This library allows the user to create order-based financial markets, add agents, and evaluate the effects of combinations of agents on measures such as volatility, agents-profits and more.

When a market is started, agents will send orders to the market (according to their strategy), which are in turn processing by a matching engine. If the order matches an order/orders of the opposite side, a transaction will occur. Otherwise, the order will be a added to the orderbook. 

By initiating markets with different setups (different tick-sizes, for example) and different sets of agents (many/no market makers, many/few random agents, etc.) one can see the impact on price development, volatility, agents positions and profits. One can see - for example - that adding a market maker to the market, will decrease volatility. 

![examplePriceDevelopment](pictures/examplePriceDevelopment.png)

Adding a market maker with a position limit (= closes position when limit is reached), can lead to sudden price spike (I leave this on for you to investigate ;) ).


## Why the project is useful
This project can be usefull for at least three groups of people: trading firms, regulators and trading venues. 

### Trading firms
For the first, it can be used test algorithmic trading strategies.

ALthough there is plenty of transaction data around to backtest strategies on, this doesn't provide an accurate picture of a market.

In reality, your orders will have market-impact, directly matching other orders (hence changing the price) or cause other market participants to change their behaviour.

In order to deal with this issue, a dynamic order generation system is necessary.

Also, this order simulator could allow parties to test their strategies under a wide range of conditions. One can set the market (the ticksize, for example), and add various sets of agents.

Hence one can test the results of one's trading strategy under various circumstances, making sure it's robust.

### Regulators
Regulators can test the effects of various combinations of algorthimic strategies on the financial market. While two trading strategies might - one used without the other - have good results for the markets (i.e., decrease volatitliy, increase market depth, etc.), the combination of both might have unintentional (and negative) consequences.

Simulations can help regulators in testing under what condtions dangers might emerge, and how to mitigate them (for example: changing the proporitions of various trading strategies).

### Trading venues
Trading venues can use simulations to test the effects of features of their market (tick size, for example) on variables of interest (number of transactions, for example). There might turn out to be conditions under which the market is not as stable as expected. What would for example happen with liquidity if we add a whole bunch trend following algorithms? And would they trigger agents with stop losses? And if so, what would be the net effect on the market? What are the worst case scenarious you have to prepare for?

## How users can get started with the project
Using the libary is simple. 

First: Download "orderGenerator_module.py" and save it on your Python path.

Secondly: Import the libary. 

```
from orderGenerator_module.py import *
``` 

Lets start by creating a market:

### Market

`a = market()`

Adding no parameters initializes a market with minimum allowed price = 1, maximum price = 100,
ticksize = 0.05, minimal quantity of any order = 1 and maximum quantity = 10.

You can change of these parameters by putting any of them between brackets:

`a = market(minprice = 100, maxprice = 1000, ticksize = 1, minquantity = 10, maxquantity = 1000)`

By default, you will also add two agents: 
- random agent
- market maker

the random agent sends in orders according to a logNormal distribution. Specifically: it checks the last price, and sends in order for lastPrice * lognormal(). The market maker always want to best bid and offer.

You can also add your own agents:

`b = market()`

You do so by picking from the available strategies. At this point, they are:
- randomUniform
- randomNormal
- randomLogNormal
- marketMaker

Add them to an array
```
agents = ["randomLogNormal", "marketMaker", "marketMaker", "randomLogNormal"]
b.addAgents(agents)
```

Now you can start the market/have the various agents send in orders. 

You do so by:

`b.orderGenerator()`

![showOrderbook()](pictures/showOrderBook.png)

This functions loops through the agents (from left to right), and have each agent execute its strategy. Once finished, it will repeat. It will do so for (by default) 5000 times.

You can adjust parameters 

`b.orderGenerator(n, cleart, sleeptime)`
where 
n = number of iterations
clearAt = number of iterations after which orderbook gets cleared
sleeptime = seconds between interations. Usefull to slowdown printing intermerdiate results.

Once the loop is finished, we can see our results.

`a.summary()`

![summary()](pictures/summary2.png)

Shows four graphs:
price over time
volatility over time
positions of each agent over time
realized profit of each agent over time

You can also just check the price by:

`a.plot()`

![plot()](pictures/plot.png)

You can also see the orderbook by typing:

`a.showOrderbook()`

![showOrderbook()](pictures/showOrderBook.png)

Or (viusally) by typing

`a.showOrderbookH()`

![showOrderbookH()](pictures/depthOrderbook.png)

### Agents

First intialize an agent:

`agent1 = agent()`

As described above, you can add agents yourself by picking from the set of available strategies.

At this point in time, there are four strategies:
#### randomUniform: 
agent randomly chooses to send in Buy or Sell Order
agent chooses randomly (from a uniform distribution) a price between minprice of market and maxprice market
agent chooses randomly (from a uniform distribution) a quantity between minquantity of market and maxquantity market

#### randomNormal: 
agent randomly chooses to send in Buy or Sell Order
agent chooses randomly from a normal distribution with mean = last price and standard deviation = 0.1
agent chooses randomly (from a uniform distribution) a quantity between minquantity of market and maxquantity market

agent1.randomNormal(a)

#### randomLogNormal
agent randomly chooses to send in Buy or Sell Order
agent chooses randomly from a lognormal distribution with mean = 0 and standard deviation = 0.2. It multiplies this value with the last price traded. Value gets rounded to nearest multiple of ticksize.
agent chooses randomly (from a uniform distribution) a quantity between minquantity of market and maxquantity market

agent1.randomLogNormal(a)

Where users can get help with your project
Who maintains and contributes to the project

#### marketMaker
The market maker always check if he is best bid and best offer in orderbook. If he is not, he will improve best bid by 1 tick or best offer by 1 tick (or both). If he is best bid or best offer, he will do nothing. If there are no bids, he will send in a best bid at the lowest possible price. The oppostite goes for no offers.

agent chooses randomly (from a uniform distribution) a quantity between minquantity of market and maxquantity market

You can set various parameters at the marketMaker:

`agent1.marketMaker(a, stop, position_limit)`

The marketMaker might have a position limit, meaning: if his accumulated position exceeds its limit, it will close its entire position at market. Also, if his short position exceeds the position limit, he will buy back all shorts at market.

If stop = True, position_limit = 250 by default. You can set the limit you want.

You could even have an agent that changes between strategies

```
agent1.randomNormal(a)
agent1.marketMaker(a)
...
```

### Orders
If an agents sends in an order, the order will go through the matching engine. This follows the standard rules of a limit order book. Briefly: if the price of a bid order is higher than the price of best offer in the orderbook, there will be a transaction. If there is remaining quantity left (= agent didn't buy all units he wanted), the engine will check for the next lowest offer. If there is, there will be a transaction. This will go on untill either the buyer bought all units he wanted, or there are no offers matching the bid price. In case of the later, the reimaing bid will be send to the orderbook.

The opposite goes for offers.

### Transaction
If an order leads to a transaction, a transaciton will occur.

## Where users can get help with your project
You can contact me or commit changes yourself.
