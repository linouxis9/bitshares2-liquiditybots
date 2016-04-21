from .basestrategy import BaseStrategy, MissingSettingsException
import math
from datetime import datetime
import time


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
        * **minimum_change_percentage**: minimum difference between the current and calculated position to trigger an update
        * **ratio**: The desired collateral ratio (if you combine this bot with MaintainCollateralRatio set this to target_ratio

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
                                 "ratio" : 2.5,
                                 "minimum_change_percentage" : 10,
                                 }


    """

    block_counter = -1

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

        """ Verify that the markets are against the assets
        """
        for m in self.settings["markets"]:
            quote_name, base_name = m.split(self.dex.market_separator)
            quote = self.dex.rpc.get_asset(quote_name)
            base = self.dex.rpc.get_asset(base_name)
            if "bitasset_data_id" not in quote:
                raise ValueError(
                    "The quote asset %s is not a bitasset "
                    "and thus can't be borrowed" % quote_name
                )
            collateral_asset_id = self.dex.getObject(
                quote["bitasset_data_id"]
            )["options"]["short_backing_asset"]
            assert collateral_asset_id == base["id"], Exception(
                "Collateral asset of %s doesn't match" % quote_name
            )

        """ Check if there are no existing debt positions, creating the initial positions if none exist
        """

        debt_positions = self.dex.list_debt_positions()
        if len(debt_positions) == 0:
            quote_amounts = self.calculate_quote_amounts(debt_positions)
            print("%s | No debt positions, placing them... " % datetime.now())
            for symbol, amount in quote_amounts.items():
                print(symbol, amount)
                self.dex.borrow(amount, symbol, self.settings["ratio"])

        cur_orders = self.dex.returnOpenOrders()
        for market in self.settings["markets"]:
            if len(cur_orders[market]) == 0:
                self.place_orders_market(market)
        self.tick()

    def adjust_debt_amount(self, delta_amount, symbol):
        """ Actually adjust the debt amount
        """
        print("%s | Adjusting position for %s by %4.f" % (datetime.now(), symbol, delta_amount))
        self.dex.adjust_debt(delta_amount, symbol, self.settings["ratio"])

    def calculate_quote_amounts(self, debt_positions):
        """ Calculate the amount of the asset that should be borrowed according to the settings.
        """
        total_collateral = sum([value['collateral'] for key, value in debt_positions.items() if value['collateral_asset'] == "BTS"])
        balances = self.dex.returnBalances()
        open_orders = self.dex.returnOpenOrders()
        order_list = []
        for market in open_orders:
            order_list.extend(open_orders[market])
        bts_on_orderbook = sum([order['total'] for order in order_list if order['type'] == 'buy'])
        total_bts = total_collateral + balances["BTS"] + bts_on_orderbook

        ticker = self.dex.returnTicker()
        quote_amounts = {}
        for m in self.settings["markets"]:
            quote, base = m.split(self.config.market_separator)
            quote_amount = (total_bts * (self.config.borrow_percentages[quote] / 100)) / ticker[m]['settlement_price']
            quote_amounts[quote] = quote_amount
        return quote_amounts

    def loadMarket(self, notify=True):
        """ Load the markets and compare the stored orders with the
            still open orders. Calls ``orderFilled(orderid)`` for orders no
            longer open (i.e. fully filled)
        """

        self.opened_orders = self.dex.returnOpenOrdersIds()

        #: Have orders been matched?
        old_orders = self.getState()["orders"]
        cur_orders = self.dex.returnOpenOrdersIds()
        for market in self.settings["markets"] :
            if market in old_orders:
                for orderid in old_orders[market] :
                    if orderid not in cur_orders[market] :
                        # Remove it from the state
                        self.state["orders"][market].remove(orderid)
                        # Execute orderFilled call
                        if notify :
                            self.orderFilled(orderid, market)
                            
    def orderFilled(self, oid, market):
        print("%s | Order %s filled or cancelled" % (datetime.now(), oid))
        self.place_orders_market(market)

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
                        print("%s | Order: %s is %.3f%% away from feed" % (datetime.now(), o['orderNumber'], order_feed_spread))
                        if order_feed_spread <= self.settings["allowed_spread_percentage"] / 2 or order_feed_spread >= (self.settings["allowed_spread_percentage"] + self.settings["spread_percentage"]) / 2:
                            self.cancel_orders_market(m)
                            self.place_orders_market(m)
                
    def orderPlaced(self, oid):
        print("%s | Order %s placed." % (datetime.now(), oid))

    def cancel_orders_market(self, market) :
        """ Cancel all orders for a specific market
        """
        print("%s | Cancelling orders for %s market" % (datetime.now(), market))
        curOrders = self.dex.returnOpenOrders()
        for o in curOrders[market]:
            try :
                print("Cancelling %s" % o["orderNumber"])
                self.dex.cancel(o["orderNumber"])
            except:
                print("An error has occured when trying to cancel order %s!" % o)

    def place_orders_market(self, market):
        m = market
        debt_positions = self.dex.list_debt_positions()
        quote_amounts = self.calculate_quote_amounts(debt_positions)
        if len(debt_positions) == 0:
            print("%s | No debt positions, placing them... " % datetime.now())
            for symbol, amount in quote_amounts.items():
                self.dex.borrow(amount, symbol, self.settings["ratio"])
        elif len(debt_positions) == 3:
            for symbol, amount in quote_amounts.items():
                change_percentage = math.fabs((amount/debt_positions[symbol]['debt']) - 1) * 100
                print("%s | Calculated amount: %.4f | Current amount: %.4f | Change: %.2f " % (datetime.now(), amount, debt_positions[symbol]['debt'], change_percentage))
                if change_percentage >= self.settings["minimum_change_percentage"]:
                    delta_amount = amount - debt_positions[symbol]['debt']
                    self.adjust_debt_amount(delta_amount, symbol)
        else:
            print("%s | Something is wrong, %d amount of debt positions " % (datetime.now(), len(debt_positions)))


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