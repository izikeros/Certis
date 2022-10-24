# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.8
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown] tags=[]
# # Certis Quickstart

# %% [markdown]
# ## This notebook is a demonstration of:
# - supported order types (list all of them)
# - defining basic strategy (Simple Moving Average - SMA)
# - downloading financial timeseries from yahoo finance
# - input data format
# - initialization of ExchangeInfo object (parameters that characterize given exchange,
#     e.g. transaction fees)
# - initialization and run of engine (combined

# %%
# Add parent directory to path
import sys

import certis
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from yfinance import Ticker

sys.path.insert(0, "..")

# %%

# %% [markdown] tags=[]
# # Supported Order Types
# - LIMIT
# - MARKET
# - STOP_MARKET
# - STOP_LOSS_MARKET
# - TAKE_PROFIT_MARKET
#
# <a href="https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders"> order type docs for beginners

# %%
print(certis.OrderType.ORDERS)

# %% [markdown]
# # Supported Order Sides
# LONG: betting for upside
# SHORT: betting for downside

# %%
print("certis.OrderSide.LONG:", certis.OrderSide.LONG)
print("certis.OrderSide.SHORT:", certis.OrderSide.SHORT)


# %%
# from pprint import pprint

# %%
# pprint({"margin": 10000, "portfolio_value": 10000.0, "position": {"size": 0, "side": 0, "avg_price": 0, "unrealized_pnl": 0.0}, "has_position": "False", "timestamp": 1579076100000000000}, indent=False)

# %% [markdown]
# # Writing Trading Strategy With Certis
# - function certis.Strategy.execute() -> executes order with given data and account info
# - function certis.Strategy.calculate() -> calculates indicators, etc. with given raw data
#
# # MA Cross Strategy
# - In this Tutorial, We will write a simple strategy called "MA Cross Strategy"
# - BUY WHEN CLOSE > MA(CLOSE, 5)
# - SELL WHEN CLOSE < MA(CLOSE, 5)

# %%
class MyFirstStrategy(certis.Strategy):
    def __init__(self, config):
        # config: Dict[str, Any]: config for this strategy
        # name: str: name for this strategy
        super().__init__(config, "MyFirstStrategy")
        self.ma_period = config["MA_PERIOD"]

    def calculate(self, data):
        # data: pd.DataFrame contains [open, high, low, close, volume, timestamp]
        # calculations here
        data["MA"] = data["close"].rolling(self.ma_period).mean()
        return data

    def execute(self, state_dict) -> list[certis.core.Action]:
        actions = []

        """
        state_dict example:
            {
                'has_position': 0,
                 'margin': 10000,
                 'portfolio_value': 10000.0,
                 'position': {
                     'avg_price': 0,
                     'side': 0,
                     'size': 0,
                     'unrealized_pnl': 0.0
                 },
                 'timestamp': 1579076100000000000
            }
        """

        # has_position = state_dict["account_info"]["has_position"]
        portfolio_value = state_dict["account_info"]["portfolio_value"]
        position_size = state_dict["account_info"]["position"]["size"]
        data = state_dict["data"]

        if not state_dict["account_info"]["has_position"]:
            if data["close"] > data["MA"]:  # if above ma
                order = certis.Order(
                    order_type=certis.OrderType.MARKET,
                    order_quantity=portfolio_value / data["close"],  # full bet!,
                    order_side=certis.OrderSide.LONG,
                    order_price=None,  # MARKET ORDER
                    reduce_only=False,
                )
                actions.append(order)

        else:
            if data["close"] < data["MA"]:
                order = certis.Order(
                    order_type=certis.OrderType.MARKET,
                    order_quantity=position_size,  # full bet!,
                    order_side=certis.OrderSide.SHORT,
                    order_price=None,  # MARKET ORDER
                    reduce_only=True,
                )
                actions.append(order)

        return actions


# %% [markdown]
# # Market Info Object
# - essential market info for the backtesting
# - maker fee: fee for limit orders
# - taker fee: fee for market orders
# - slippage: slippage applied for market orders
# - tick_size: tick size
# - minimum_order_size: minimum order size

# %%
market_info = certis.ExchangeInfo(
    maker_fee=0.001,
    taker_fee=0.001,
    slippage=0.001,
    minimum_order_size=0.001,
    tick_size=0.01,
)

# %% [markdown]
# # Load data
# Certis Supports pandas DataFrame with `[timestamp, open, high, low, close, volume]` with datetime indexes

# %%

data = Ticker("BTC-USD").history(period="max")
data = data[data.columns[:5]]
data.columns = ["open", "high", "low", "close", "volume"]
data["timestamp"] = data.index.astype(int)
fin_data = data.copy()

# %% [markdown]
# # Initialize Engine
# ### to initialize certis backtesting engine, you need following components:
# - data: pandas DataFrame
# - initial margin: float
# - market info: ExchangeInfo Object
# - strategy: Strategy Class
# - strategy config: strategy config

# %%
MA_WINDOW = 7
initial_margin = 100000
strategy_config = {"MA_PERIOD": MA_WINDOW}

engine = certis.Engine(
    data=fin_data,
    initial_margin=initial_margin,
    market_info=market_info,
    strategy_cls=MyFirstStrategy,
    strategy_config=strategy_config,
)

# %%
engine.run()

# %% [markdown]
# # Analyzing Results
# The data for analysis can be obtained from the logger.
# - `engine.logger.account_infos`:  account info for timestamp-by-timestamp
# - `engine.logger.transactions`:   order fill (transactions)
# - `engine.logger.unfilled_order`: unfilled order for timestamp-by-timestamp

# %%

# %%
account_info_df = pd.DataFrame(engine.logger.account_infos)
account_info_df.index = pd.to_datetime(account_info_df["timestamp"])

# %% [markdown]
# ## Account info from the logger in form of Data Frame

# %%
account_info_df.head(3)

# %%
account_info_df.iloc[5].position

# %% [markdown]
# ## Plot portfolio value
# On the plot below there is:
# - portfolio value in given point of time relative to the initial portfolio value
# - BTC value in given point of time relative to the initial BTC value

# %%
(account_info_df["portfolio_value"] / initial_margin).plot(
    label="equity", figsize=(20, 10)
)
ax = (fin_data["close"] / fin_data["close"][0]).plot(label="BTC-USD")
plt.legend()
ax.set_title("Portfolio value compared to Bitcoin Price")
ax.set_ylabel("relative value change [x]")

# %%
engine.logger.transactions[:2]

# %%
transactions_df = pd.DataFrame(engine.logger.transactions)
transactions_df.index = pd.to_datetime(transactions_df["timestamp"])
transactions_df.sample(5)

# %%
realized = pd.DataFrame(transactions_df.realized.to_dict()).T
order = pd.DataFrame(transactions_df.order.to_dict()).T
re_ord = realized.join(order)
tr = re_ord.join(transactions_df).drop(["realized", "order"], axis=1)
tr

# %%
f, axs = plt.subplots(
    nrows=1,
    ncols=1,
    figsize=(16, 5),
)
buys = tr[tr.side == 1]
sells = tr[tr.side == -1]
price = fin_data["close"]
sma = fin_data.rolling(window=MA_WINDOW).mean().dropna()
sma = pd.DataFrame(sma["close"])
price.plot(ax=axs)
axs.scatter(buys.index, buys.price, alpha=0.8, label="Buy", marker="^", color="green")
axs.scatter(sells.index, sells.price, alpha=0.8, label="Sell", marker="v", color="red")


# %%
sma

# %%
# Plotting

# import plotly.io as pio
# pio.templates.default = "plotly_dark"

fig = go.Figure()

# price
k = 0.01
fig.add_trace(
    go.Scatter(
        x=fin_data.index, y=fin_data["close"], name="Close", line_color="#222222"
    )
)

# # SMA
fig.add_trace(go.Scatter(x=sma.index, y=sma["close"], name="SMA", line_color="#FECB52"))


# buy signals
fig.add_trace(
    go.Scatter(
        x=buys.index,
        y=(1 - k) * buys.price,
        name="Buys",
        mode="markers",
        marker=dict(color="#00CC96", size=10, symbol="triangle-up"),
    )
)
# sell signals
fig.add_trace(
    go.Scatter(
        x=sells.index,
        y=(1 + k) * sells.price,
        name="Sells",
        mode="markers",
        marker=dict(color="#EF553B", size=10, symbol="triangle-down"),
    )
)

fig.update_layout(
    autosize=False,
    width=960,
    height=700,
)

# Add range slider
fig.update_layout(
    xaxis=dict(rangeslider=dict(visible=True), type="date"),
    yaxis=dict(autorange=True, fixedrange=False),
)


layout = dict(
    title="Time series with range slider and selectors",
    xaxis=dict(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all"),
                ]
            )
        ),
        rangeslider=dict(visible=True),
        type="date",
    ),
)

# fig.show()
figu = go.FigureWidget(data=fig, layout=layout)


def zoom(layout, xrange):
    in_view = fin_data.loc[figu.layout.xaxis.range[0] : figu.layout.xaxis.range[1]]
    figu.layout.yaxis.range = [in_view.high.min() - 10, in_view.high.max() + 10]


figu.layout.on_change(zoom, "xaxis.range")
figu

# %%
buys

# %%

# %%
df = fin_data.copy()

# Make sure dates are in ascending order
# We need this for slicing in the callback below
df.sort_index(ascending=True, inplace=True)

trace = go.Scatter(x=list(df.index), y=list(df.high))

traces = [trace]


fig = go.FigureWidget(data=traces, layout=layout)
fig


# %%
def zoom(layout, xrange):
    in_view = df.loc[fig.layout.xaxis.range[0] : fig.layout.xaxis.range[1]]
    fig.layout.yaxis.range = [in_view.high.min() - 10, in_view.high.max() + 10]


fig.layout.on_change(zoom, "xaxis.range")

# %%
