from typing import List

import certis


class MACrossing(certis.Strategy):
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

    def execute(self, state_dict) -> List[certis.core.Action]:
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

        has_position = state_dict["account_info"]["has_position"]
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
