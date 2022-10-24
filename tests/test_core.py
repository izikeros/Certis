import pandas as pd
from certis import Engine
from certis import ExchangeInfo
from certis.strategies.ma_crossing import MACrossing


MA_WINDOW = 7
initial_margin = 100000
strategy_config = {"MA_PERIOD": MA_WINDOW}
fin_data = pd.read_csv("data/btc_usd_ohlcv.csv")

market_info = ExchangeInfo(
    maker_fee=0.001,
    taker_fee=0.001,
    slippage=0.001,
    minimum_order_size=0.001,
    tick_size=0.01,
)


class TestEngine:
    def test_engine__smoke(self):
        engine = Engine(
            fin_data, initial_margin, market_info, MACrossing, strategy_config
        )
        engine.run()
