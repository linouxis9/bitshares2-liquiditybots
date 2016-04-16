from .basestrategy import BaseStrategy, MissingSettingsException
import math
from numpy import linspace


class MakerSellBuyWalls(BaseStrategy):
    """ Play Buy/Sell Walls into a market

        **Settings**:

        * **target_price**: target_price to place Ramps around (floating number or "feed")
        * **target_price_offset_percentage**: +-percentage offset from target_price
        * **spread_percentage**: Another "offset". Allows a spread. The lowest orders will be placed here
        * **volume_percentage**: The amount of funds (%) you want to use
        * **symmetric_sides**: (boolean) Place symmetric walls on both sides?
        * **only_buy**: Serve only on of both sides 
        * **only_sell**: Serve only on of both sides 
        * **expiration**: expiration time in seconds of buy/sell orders.

        Only used if run in continuous mode (e.g. with ``run_conf.py``):

        * **skip_blocks**: Checks the collateral ratio only every x blocks

        .. code-block:: python

            from strategies.maker import MakerSellBuyWalls
            bots["MakerWall"] = {"bot" : MakerSellBuyWalls,
                                 "markets" : ["USD : BTS"],
                                 "target_price" : "feed",
                                 "target_price_offset_percentage" : 5,
                                 "spread_percentage" : 5,
                                 "volume_percentage" : 10,
                                 "symmetric_sides" : True,
                                 "only_buy" : False,
                                 "only_sell" : False,
                                 }

        .. note:: This module does not watch your orders, all it does is
                  place new orders!
    """

    block_counter = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init(self):
        """ set default settings
        """
        if "target_price_offset_percentage" not in self.settings:
            self.settings["target_price_offset_percentage"] = 0.0

        if "target_price" not in self.settings:
            raise MissingSettingsException("target_price")

        if "spread_percentage" not in self.settings:
            raise MissingSettingsException("spread_percentage")

        if "volume_percentage" not in self.settings:
            raise MissingSettingsException("volume_percentage")

        if "symmetric_sides" not in self.settings:
            self.settings["symmetric_sides"] = True

        if "expiration" not in self.settings:
            self.settings["expiration"] = 60*60*24

        if "skip_blocks" not in self.settings:
            self.settings["skip_blocks"] = 20

        # Execute one tick()
        self.tick()

    def orderFilled(self, oid):
        """ Do nothing, when an order is Filled
        """
        pass

    def tick(self):
        self.block_counter += 1
        if (self.block_counter % self.settings["skip_blocks"]) == 0:
            ticker = self.dex.returnTicker()
            for m in self.settings["markets"]:

    def place(self) :
        """ Place all orders according to the settings.
        """
        print("Placing Orders:")
        target_price = self.settings["target_price"]
        only_sell = True if "only_sell" in self.settings and self.settings["only_sell"] else False
        only_buy = True if "only_buy" in self.settings and self.settings["only_buy"] else False

        #: Amount of Funds available for trading (per asset)
        balances = self.dex.returnBalances()
        asset_ids = []
        amounts = {}
        for market in self.settings["markets"] :
            quote, base = market.split(self.config.market_separator)
            asset_ids.append(base)
            asset_ids.append(quote)
        assets_unique = list(set(asset_ids))
        for a in assets_unique:
            if a in balances :
                amounts[a] = balances[a] * self.settings["volume_percentage"] / 100 / asset_ids.count(a)

        ticker = self.dex.returnTicker()
        for m in self.settings["markets"]:

            if isinstance(target_price, float) or isinstance(target_price, int):
                base_price = float(target_price) * (1 + self.settings["target_price_offset_percentage"] / 100)
            elif (isinstance(target_price, str) and
                  target_price is "settlement_price" or
                  target_price is "feed" or
                  target_price is "price_feed"):
                if "settlement_price" in ticker[m] :
                    base_price = ticker[m]["settlement_price"] * (1 + self.settings["target_price_offset_percentage"] / 100)
                else :
                    raise Exception("Pair %s does not have a settlement price!" % m)

            buy_price  = base_price * (1.0 - self.settings["spread_percentage"] / 200)
            sell_price = base_price * (1.0 + self.settings["spread_percentage"] / 200)

            quote, base = m.split(self.config.market_separator)
            if quote in amounts and not only_buy:
                if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_sell:
                    thisAmount = min([amounts[quote], amounts[base] / buy_price]) if base in amounts else amounts[quote]
                    self.sell(m, sell_price, thisAmount)
                else :
                    self.sell(m, sell_price, amounts[quote])
            if base in amounts and not only_sell:
                if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_buy:
                    thisAmount = min([amounts[quote], amounts[base] / buy_price]) if quote in amounts else amounts[base] / buy_price
                    self.buy(m, buy_price, thisAmount)
                else :
                    self.buy(m, buy_price, amounts[base] / buy_price)


