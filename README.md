# orderGenerator
This library allows the user to easily simulate a financial market, add agents, and gerenate orders.


What the project does
This repositoy allows you to create a virtual market, add agents, and start the market. 
Agents will send orders to the market (according to their strategy), which are send to a matching engine. 
If an order matches and order of the opposite side, a trade will occur.


Why the project is useful
This project can be usefull for two groups of people: trading firms and regulators. For the first, it can be used test algorithmic trading strategies.
ALthough there is plenty of transaction data around to backtest strategies on, this doesn't provide an accurate picture of a market.
In reality, your orders will have market-impact, directly matching other orders (hence changing the price) or cause other market participants to chagne their behaviour.
In to incorporate this dynamic, a dynamic order generation system is necessary.

Also, this could allows parties to test their strategies under a wide range of conditions. One can set the market (the ticksize, for example), and add various sets of agents.
Hence one can test the results of one's trading strategy under various circumstances.

Regulators can test the effects of various combinations of algorthimic strategies on the financial market. While two trading strategies might - when used without the other - have
good results for the markets (i.e., decrease volatitliy, increase market depth, etc.), the combination of both might have unintentional (and negative) consequences.

Simulations can help regulators in testing under what condtions dangers might emerge, and how to mitigate them (for example: changing the proporitions of various trading strategies).

How users can get started with the project
Using the libary is simple. 


Where users can get help with your project
Who maintains and contributes to the project

