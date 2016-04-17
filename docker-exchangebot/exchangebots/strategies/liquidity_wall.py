from .basestrategy import BaseStrategy, MissingSettingsException
import math
from numpy import linspace
from datetime import datetime


class LiquiditySellBuyWalls(BaseStrategy):
    """ Provide liquidity by putting up buy/sell walls at a specific spread in the market, replacing orders as the price changes.

        **Settings**:

        * **target_price**: target_price to place Ramps around (floating number or "feed")
        * **target_price_offset_percentage**: +-percentage offset from target_price
        * **spread_percentage**: Another "offset". Allows a spread. The lowest orders will be placed here
        * **allowed_spread_percentage**: The allowed spread an order may have before it gets replaced
        * **volume_percentage**: The amount of funds (%) you want to use
        * **symmetric_sides**: (boolean) Place symmetric walls on both sides?
        * **only_buy**: Serve only on of both sides 
        * **only_sell**: Serve only on of both sides 
        * **expiration**: expiration time in seconds of buy/sell orders.

        Only used if run in continuous mode (e.g. with ``run_conf.py``):

        * **skip_blocks**: Checks the collateral ratio only every x blocks

        .. code-block:: python

            from strategies.maker import LiquiditySellBuyWalls
            bots["LiquidityWall"] = {"bot" : LiquiditySellBuyWalls,
                                 "markets" : ["USD : BTS"],
                                 "target_price" : "feed",
                                 "target_price_offset_percentage" : 5,
                                 "spread_percentage" : 5,
                                 "allowed_spread_percentage" : 2.5,
                                 "volume_percentage" : 10,
                                 "symmetric_sides" : True,
                                 "only_buy" : False,
                                 "only_sell" : False,
                                 "expiration" : 60 * 60 * 6
                                 }


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
        
        self.cancel_all()
        self.place()
        # Execute one tick()
        self.tick()

    def orderFilled(self, oid):
        print("%s | Order %s filled." % (datetime.now(), oid))
        replace_orders = []
        order = self.dex.ws.get_objects([oid])[0]
        base_asset, quote_asset = self._get_assets_from_ids(order['sell_price']['base']['asset_id'], order['sell_price']['quote']['asset_id'])

        for market in self.settings["markets"]:
            quote, base = single_market.split(self.config.market_separator)
            if quote == quote_asset["symbol"] and base == base_asset["symbol"] or quote == base_asset["symbol"] and base == quote_asset["symbol"]:
                replace_orders.append(market)
        
        for market in replace_orders:
            self.replace(market)

    def tick(self):
        self.block_counter += 1
        if (self.block_counter % self.settings["skip_blocks"]) == 0:
            print("%s | Amount of blocks since bot has been started: %d" % (datetime.now(), self.block_counter))
            ticker = self.dex.returnTicker()
            curOrders = self.dex.returnOpenOrders()
            for m in self.settings["markets"]:
                if m in curOrders:
                    for o in curOrders[m]:
                        order_feed_spread = math.fabs((o["rate"] - ticker[m]["settlement_price"]) / ticker[m]["settlement_price"] * 100)
                        #print("%s | Order: %s is %.3f%% away from feed" % (datetime.now(), o['orderNumber'], order_feed_spread))
                        if order_feed_spread <= self.settings["allowed_spread_percentage"] / 2 or order_feed_spread >= (self.settings["allowed_spread_percentage"] + self.settings["spread_percentage"]) / 2:
                            self.replace(m)
                
    def orderPlaced(self, oid):
        print("%s | Order %s placed." % (datetime.now(), oid))
    
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
                    if thisAmount >= self.config.minimum_amounts[quote]:
                        self.sell(m, sell_price, thisAmount)
                else :
                    thisAmount = amounts[quote]
                    if thisAmount >= self.config.minimum_amounts[quote]:
                        self.sell(m, sell_price, thisAmount)
            if base in amounts and not only_sell:
                if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_buy:
                    thisAmount = min([amounts[quote], amounts[base] / buy_price]) if quote in amounts else amounts[base] / buy_price
                    if thisAmount >= self.config.minimum_amounts[quote]:
                        self.buy(m, buy_price, thisAmount)
                else :
                    thisAmount = amounts[base] / buy_price
                    if thisAmount >= self.config.minimum_amounts[quote]:
                        self.buy(m, buy_price, thisAmount)
                    
    def replace(self, market) :
        """ (re)place orders for specific market.
        """
        print("%s | Replacing Orders for %s market" % (datetime.now(), market))
        m = market
        curOrders = self.dex.returnOpenOrders()
        for o in curOrders[market]:
            try :
                print("Cancelling %s" % o["orderNumber"])
                self.dex.cancel(o["orderNumber"])
            except:
                print("An error has occured when trying to cancel order %s!" % o)
                
        target_price = self.settings["target_price"]
        only_sell = True if "only_sell" in self.settings and self.settings["only_sell"] else False
        only_buy = True if "only_buy" in self.settings and self.settings["only_buy"] else False

        #: Amount of Funds available for trading (per asset)
        balances = self.dex.returnBalances()
        asset_ids = []
        amounts = {}
        for single_market in self.settings["markets"] :
            quote, base = single_market.split(self.config.market_separator)
            asset_ids.append(base)
            asset_ids.append(quote)
        assets_unique = list(set(asset_ids))
        for a in assets_unique:
            if a in balances :
                amounts[a] = balances[a] * self.settings["volume_percentage"] / 100 / asset_ids.count(a)

        ticker = self.dex.returnTicker()

        if isinstance(target_price, float) or isinstance(target_price, int):
            base_price = float(target_price) * (1 + self.settings["target_price_offset_percentage"] / 100)
        elif (isinstance(target_price, str) and
              target_price is "settlement_price" or
              target_price is "feed" or
              target_price is "price_feed"):
            if "settlement_price" in ticker[market] :
                base_price = ticker[m]["settlement_price"] * (1 + self.settings["target_price_offset_percentage"] / 100)
            else :
                raise Exception("Pair %s does not have a settlement price!" % m)
        
        buy_price  = base_price * (1.0 - self.settings["spread_percentage"] / 200)
        sell_price = base_price * (1.0 + self.settings["spread_percentage"] / 200)
        
        quote, base = m.split(self.config.market_separator)
        if quote in amounts and not only_buy:
            if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_sell:
                thisAmount = min([amounts[quote], amounts[base] / buy_price]) if base in amounts else amounts[quote]
                if thisAmount >= self.config.minimum_amounts[quote]:
                    self.sell(m, sell_price, thisAmount)
            else :
                thisAmount = amounts[quote]
                if thisAmount >= self.config.minimum_amounts[quote]:
                    self.sell(m, sell_price, thisAmount)
        if base in amounts and not only_sell:
            if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_buy:
                thisAmount = min([amounts[quote], amounts[base] / buy_price]) if quote in amounts else amounts[base] / buy_price
                if thisAmount >= self.config.minimum_amounts[quote]:
                    self.buy(m, buy_price, thisAmount)
            else :
                thisAmount = amounts[base] / buy_price
                if thisAmount >= self.config.minimum_amounts[quote]:
                    self.buy(m, buy_price, thisAmount)