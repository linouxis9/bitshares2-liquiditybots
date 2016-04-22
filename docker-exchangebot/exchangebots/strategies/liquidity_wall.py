from .basestrategy import BaseStrategy, MissingSettingsException
import math
from datetime import datetime


class LiquiditySellBuyWalls(BaseStrategy):
    """ Provide liquidity by putting up buy/sell walls at a specific spread in the market, replacing orders as the price changes.

        **Settings**:

        * **borrow_percentages**: how to divide the bts for lending bitAssets
        * **minimum_amounts**: the minimum amount an order has to be
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
        * **ratio**: The desired collateral ratio
        * **calculate_total_bts**: How the total bts should be calculated. "bts" for all bts and "worth" for bts and worth of bitassets
        Only used if run in continuous mode (e.g. with ``run_conf.py``):

        * **skip_blocks**: Checks the collateral ratio only every x blocks

        .. code-block:: python

            from strategies.maker import LiquiditySellBuyWalls
            bots["LiquidityWall"] = {"bot" : LiquiditySellBuyWalls,
                                 "markets" : ["USD : BTS"],
                                 "borrow_percentages" : ["USD" : 30, "BTS" : 70]
                                 "minimum_amounts" : ["USD" : 0.2]
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
        """ Set default settings
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

        if "ratio" not in self.settings:
            raise MissingSettingsException("ratio")

        if "borrow_percentages" not in self.settings:
            raise MissingSettingsException("borrow_percentages")

        if "minimum_amounts" not in self.settings:
            raise MissingSettingsException("minimum_amounts")

        if "minimum_change_percentage" not in self.settings:
            raise MissingSettingsException("minimum_change_percentage")

        """ Verify that the markets are against the assets
        """
        for market in self.settings["markets"]:
            quote_name, base_name = market.split(self.dex.market_separator)
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
            self.place_initial_debt_positions(debt_positions)

        """ Check if there is at least 1 order for each market, placing orders for that market if that's not the case
        """
        open_orders = self.dex.returnOpenOrders()
        for market in self.settings["markets"]:
            if len(open_orders[market]) == 0:
                self.place_orders_market(market)

        # Execute 1 tick before the websocket is activated
        self.tick()

    def tick(self):
        self.block_counter += 1
        if (self.block_counter % self.settings["skip_blocks"]) == 0:
            print("%s | Amount of blocks since bot has been started: %d" % (datetime.now(), self.block_counter))
            ticker = self.dex.returnTicker()
            open_orders = self.dex.returnOpenOrders()
            for market in self.settings["markets"]:
                if market in open_orders:
                    for o in open_orders[market]:
                        order_feed_spread = math.fabs((o["rate"] - ticker[market]["settlement_price"]) / ticker[market]["settlement_price"] * 100)
                        print("%s | Order: %s is %.3f%% away from feed" % (datetime.now(), o['orderNumber'], order_feed_spread))
                        if order_feed_spread <= self.settings["allowed_spread_percentage"] / 2 or order_feed_spread >= (self.settings["allowed_spread_percentage"] + self.settings["spread_percentage"]) / 2:
                            self.cancel_orders(market)
                            self.update_debt_positions()
                            self.place_orders_market(market)

    def loadMarket(self, notify=True):
        """ Load the markets and compare the stored orders with the
            still open orders. Calls ``orderFilled(order_id)`` for orders no
            longer open (i.e. fully filled)
        """

        self.opened_orders = self.dex.returnOpenOrdersIds()

        #: Have orders been matched?
        old_orders = self.getState()["orders"]
        cur_orders = self.dex.returnOpenOrdersIds()
        for market in self.settings["markets"] :
            if market in old_orders:
                for order_id in old_orders[market] :
                    if order_id not in cur_orders[market] :
                        # Remove it from the state
                        self.state["orders"][market].remove(order_id)
                        # Execute orderFilled call
                        if notify :
                            self.orderFilled(order_id, market)
                            
    def orderFilled(self, oid, market):
        print("%s | Order %s filled or cancelled" % (datetime.now(), oid))
        self.cancel_orders(market)
        self.place_orders_market(market)

    def orderPlaced(self, oid):
        print("%s | Order %s placed." % (datetime.now(), oid))

    def place_orders(self, market='all'):
        if market != "all":
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
                    base_price = ticker[market]["settlement_price"] * (1 + self.settings["target_price_offset_percentage"] / 100)
                else :
                    raise Exception("Pair %s does not have a settlement price!" % market)

            buy_price  = base_price * (1.0 - self.settings["spread_percentage"] / 200)
            sell_price = base_price * (1.0 + self.settings["spread_percentage"] / 200)

            quote, base = market.split(self.config.market_separator)
            if quote in amounts and not only_buy:
                if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_sell:
                    thisAmount = min([amounts[quote], amounts[base] / buy_price]) if base in amounts else amounts[quote]
                    if thisAmount >= self.config.minimum_amounts[quote]:
                        self.sell(market, sell_price, thisAmount)
                else :
                    thisAmount = amounts[quote]
                    if thisAmount >= self.config.minimum_amounts[quote]:
                        self.sell(market, sell_price, thisAmount)
            if base in amounts and not only_sell:
                if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_buy:
                    thisAmount = min([amounts[quote], amounts[base] / buy_price]) if quote in amounts else amounts[base] / buy_price
                    if thisAmount >= self.config.minimum_amounts[quote]:
                        self.buy(market, buy_price, thisAmount)
                else :
                    thisAmount = amounts[base] / buy_price
                    if thisAmount >= self.config.minimum_amounts[quote]:
                        self.buy(market, buy_price, thisAmount)
        else:
            for market in self.settings["markets"]:
                self.place_orders(market)

    def cancel_orders(self, market='all') :
        """ Cancel all orders for all markets or a specific market
        """
        print("%s | Cancelling orders for %s market(s)" % (datetime.now(), market))
        open_orders = self.dex.returnOpenOrders()
        if market != 'all':
            for order in open_orders[market]:
                try:
                    print("Cancelling %s" % order["orderNumber"])
                    self.dex.cancel_orders(order["orderNumber"])
                except:
                    print("An error has occured when trying to cancel order %s!" % order)
        else:
            for market in self.settings["markets"]:
                self.cancel_orders(market)

    def place_initial_debt_positions(self, debt_positions=None):
        if not debt_positions:
            debt_positions = self.dex.list_debt_positions()

        debt_amounts = self.get_debt_amounts(debt_positions)
        print("%s | No debt positions, placing them... " % datetime.now())
        for symbol, amount in debt_amounts.items():
            print("%s | Placing debt position for %s of %4.f" % (datetime.now(), symbol, amount))
            self.dex.borrow(amount, symbol, self.settings["ratio"])

    def update_debt_positions(self):
        debt_positions = self.dex.list_debt_positions()
        debt_amounts = self.get_debt_amounts(debt_positions)
        if len(debt_positions) == 0:
            self.place_initial_debt_positions(debt_positions)
        elif len(debt_positions) == 3:
            for symbol, amount in debt_amounts.items():
                change_percentage = math.fabs((amount/debt_positions[symbol]['debt']) - 1) * 100
                print("%s | Calculated amount: %.4f | Current amount: %.4f | Change: %.2f " % (datetime.now(), amount, debt_positions[symbol]['debt'], change_percentage))
                if change_percentage >= self.settings["minimum_change_percentage"]:
                    delta_amount = amount - debt_positions[symbol]['debt']
                    self.adjust_debt_amount(delta_amount, symbol)
        else:
            print("%s | Something is wrong, %d amount of debt positions " % (datetime.now(), len(debt_positions)))

    def adjust_debt_amount(self, delta_amount, symbol):
        """ Actually adjust the debt amount
        """
        print("%s | Adjusting position for %s by %4.f" % (datetime.now(), symbol, delta_amount))
        self.dex.adjust_debt(delta_amount, symbol, self.settings["ratio"])

    def get_debt_amounts(self, debt_positions):
        """ Calculate the amount of the asset that should be borrowed according to the settings.
        """
        total_bts = self.get_total_bts(debt_positions)
        ticker = self.dex.returnTicker()
        quote_amounts = {}
        for m in self.settings["markets"]:
            quote, base = m.split(self.config.market_separator)
            quote_amount = (total_bts * (self.config.borrow_percentages[quote] / 100)) / ticker[m]['settlement_price']
            quote_amounts[quote] = quote_amount
        return quote_amounts

    def get_total_bts(self, debt_positions, calculation_type=None):
        if not debt_positions:
            debt_positions = self.dex.list_debt_positions()
        if not calculation_type:
            calculation_type = self.settings['calculate_bts_total']
        total_collateral = sum([value['collateral'] for key, value in debt_positions.items() if value['collateral_asset'] == "BTS"])
        balances = self.dex.returnBalances()
        open_orders = self.dex.returnOpenOrders()
        order_list = []
        for market in open_orders:
            order_list.extend(open_orders[market])
        bts_on_orderbook = sum([order['total'] for order in order_list if order['type'] == 'buy'])
        total_bts = total_collateral + balances["BTS"] + bts_on_orderbook

        if calculation_type == "worth":
        #    ticker = self.dex.returnTicker()
        #    market_postfix = self.config.market_separator + "BTS"
        #    bitasset_balances_worth = sum([balances[asset] * ticker[asset + market_postfix]["settlement_price"] for asset in balances if asset != "BTS"])
            total_bts = total_bts

        return total_bts