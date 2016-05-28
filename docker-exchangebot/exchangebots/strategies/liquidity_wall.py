import math
from datetime import datetime
import time
from .basestrategy import BaseStrategy, MissingSettingsException


class LiquiditySellBuyWalls(BaseStrategy):
    """ Puts up buy/sell walls at a specific spread in the market, replacing orders as the price changes.

        **Settings**:
        
        * **borrow**: Borrow bitassets? (Boolean)
        * **borrow_percentages**: how to divide the bts for lending bitAssets
        * **minimum_amounts**: the minimum amount an order has to be
        * **target_price**: target_price to place walls around (floating number or "feed")
        * **spread_percentage**: Another "offset". Allows a spread. The lowest orders will be placed here
        * **allowed_spread_percentage**: The allowed spread an order may have before it gets replaced
        * **volume_percentage**: The amount of funds (%) you want to use
        * **expiration**: Expiration time of the order in seconds
        * **ratio**: The desired collateral ratio (same as maintain_collateral_ratio.py)


        * **skip_blocks**: Runs the bot logic only every x blocks

        .. code-block:: python

            from strategies.maker import LiquiditySellBuyWalls
            bots["LiquidityWall"] = {"bot" : LiquiditySellBuyWalls,
                                 "markets" : ["USD : BTS"],
                                 "borrow" : True,
                                 "borrow_percentages" : ["USD" : 30, "BTS" : 70]
                                 "minimum_amounts" : ["USD" : 0.2]
                                 "target_price" : "feed",
                                 "spread_percentage" : 5,
                                 "allowed_spread_percentage" : 2.5,
                                 "volume_percentage" : 10,
                                 "symmetric_sides" : True,
                                 "expiration" : 60 * 60 * 6
                                 "ratio" : 2.5,
                                 "skip_blocks" : 3,
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
            self.settings["expiration"] = 60*60*2

        if "skip_blocks" not in self.settings:
            self.settings["skip_blocks"] = 20

        if "ratio" not in self.settings:
            raise MissingSettingsException("ratio")

        if "borrow_percentages" not in self.settings:
            raise MissingSettingsException("borrow_percentages")

        if "minimum_amounts" not in self.settings:
            raise MissingSettingsException("minimum_amounts")

        if "expiration" not in self.settings:
            self.settings["expiration"] = 60*60*24*7

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

        self.update_data()

        """ Check if there are no existing debt positions, creating the initial positions if none exist
        """
        if self.settings['borrow']:
            if len(self.debt_positions) == 0:
                self.place_initial_debt_positions()

        # Execute 1 tick before the websocket is activated
        self.tick()

    def update_data(self):
        self.ticker = self.dex.returnTicker()
        self.open_orders = self.dex.returnOpenOrders()
        self.debt_positions = self.dex.list_debt_positions()
        self.balances = self.dex.returnBalances()
        self.filled_orders = self.get_filled_orders()

    def tick(self):
        self.block_counter += 1
        if (self.block_counter % self.settings["skip_blocks"]) == 0:
            print("%s | Amount of blocks since bot has been started: %d" % (datetime.now(), self.block_counter))
            self.update_data()
            print("bid ask SILVER : BTS", self.price_bid_ask("SILVER : BTS"))
            print("feed SILVER : BTS", self.price_feed("SILVER : BTS"))
            print("filled SILVER : BTS", self.price_filled_orders("SILVER : BTS"))
            print("last SILVER : BTS", self.price_last("SILVER : BTS"))
            print("avg weighted SILVER : BTS", self.get_price("SILVER : BTS"))
            #for market in self.settings["markets"]:
                #self.check_and_replace(market)

    def check_and_replace(self, market):
        if market in self.open_orders:
            if len(self.open_orders[market]) == 0:
                self.place_orders(market)
            if len(self.open_orders[market]) == 1:
                if self.open_orders[market][0]['type'] == "sell":
                    self.place_orders(market, only_buy=True)
                elif self.open_orders[market][0]['type'] == "buy":
                    self.place_orders(market, only_sell=True)
            for o in self.open_orders[market]:
                order_feed_spread = math.fabs((o["rate"] - self.ticker[market]["settlement_price"]) / self.ticker[market]["settlement_price"] * 100)
                print("%s | Order: %s is %.3f%% away from feed" % (datetime.now(), o['orderNumber'], order_feed_spread))
                if order_feed_spread <= self.settings["allowed_spread_percentage"] / 2 or order_feed_spread >= (self.settings["allowed_spread_percentage"] + self.settings["spread_percentage"]) / 2:
                    self.cancel_orders(market)
                    self.place_orders(market)
                    return True
        if self.settings['borrow']:
            symbol, base = market.split(self.dex.market_separator)
            if symbol not in self.debt_positions:
                debt_amounts = self.get_debt_amounts()
                amount = debt_amounts[symbol]
                print("%s | Placing debt position for %s of %4.f" % (datetime.now(), symbol, amount))
                self.dex.borrow(amount, symbol, self.settings["ratio"])
            return False

    def orderFilled(self, oid):
        print("%s | Order %s filled or cancelled" % (datetime.now(), oid))

    def orderPlaced(self, oid):
        print("%s | Order %s placed." % (datetime.now(), oid))

    def place_orders(self, market='all', only_sell=False, only_buy=False):
        if market != "all":
            balances = self.dex.returnBalances()
            asset_ids = []
            amounts = {}
            for single_market in self.settings["markets"]:
                quote, base = single_market.split(self.config.market_separator)
                asset_ids.append(base)
                asset_ids.append(quote)
            assets_unique = list(set(asset_ids))
            for a in assets_unique:
                if a in balances:
                    amounts[a] = balances[a] * self.settings["volume_percentage"] / 100 / asset_ids.count(a)

            base_price = self.get_price(market)
            if not base_price:
                print("%s | No price for %s" % (datetime.now(), market))
                return

            buy_price = base_price * (1.0 - self.settings["spread_percentage"] / 200)
            sell_price = base_price * (1.0 + self.settings["spread_percentage"] / 200)

            quote, base = market.split(self.config.market_separator)
            if quote in amounts and not only_buy:
                if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_sell:
                    amount = min([amounts[quote], amounts[base] / buy_price]) if base in amounts else amounts[quote]
                    if amount >= self.settings['minimum_amounts'][quote]:
                        self.sell(market, sell_price, amount, self.settings["expiration"])
                else :
                    amount = amounts[quote]
                    if amount >= self.settings['minimum_amounts'][quote]:
                        self.sell(market, sell_price, amount, self.settings["expiration"])
            if base in amounts and not only_sell:
                if "symmetric_sides" in self.settings and self.settings["symmetric_sides"] and not only_buy:
                    amount = min([amounts[quote], amounts[base] / buy_price]) if quote in amounts else amounts[base] / buy_price
                    if amount >= self.settings['minimum_amounts'][quote]:
                        self.buy(market, buy_price, amount, self.settings["expiration"])
                else:
                    amount = amounts[base] / buy_price
                    if amount >= self.settings['minimum_amounts'][quote]:
                        self.buy(market, buy_price, amount, self.settings["expiration"])
        else:
            for market in self.settings["markets"]:
                self.place_orders(market)

    def cancel_orders(self, market='all'):
        """ Cancel all orders for all markets or a specific market
        """
        print("%s | Cancelling orders for %s market(s)" % (datetime.now(), market))

        if market != 'all':
            for order in self.open_orders[market]:
                try:
                    print("Cancelling %s" % order["orderNumber"])
                    self.dex.cancel(order["orderNumber"])
                except Exception as e:
                    print("An error has occured when trying to cancel order %s!" % order)
                    print(e)
        else:
            for market in self.settings["markets"]:
                self.cancel_orders(market)

    def place_initial_debt_positions(self):
        debt_amounts = self.get_debt_amounts()
        print("%s | No debt positions, placing them... " % datetime.now())
        for symbol, amount in debt_amounts.items():
            print("%s | Placing debt position for %s of %4.f" % (datetime.now(), symbol, amount))
            self.dex.borrow(amount, symbol, self.settings["ratio"])

    def get_debt_amounts(self,):
        total_bts = self.get_total_bts()
        quote_amounts = {}
        for m in self.settings["markets"]:
            quote, base = m.split(self.config.market_separator)
            quote_amount = (total_bts * (self.settings['borrow_percentages'][quote] / 100)) / self.ticker[m]['settlement_price']
            quote_amounts[quote] = quote_amount
        return quote_amounts

    def get_total_bts(self):
        total_collateral = sum([value['collateral'] for key, value in self.debt_positions.items() if value['collateral_asset'] == "BTS"])
        order_list = []
        for market in self.open_orders:
            order_list.extend(self.open_orders[market])
        bts_on_orderbook = sum([order['total'] for order in order_list if order['type'] == 'buy'])
        total_bts = total_collateral + self.balances["BTS"] + bts_on_orderbook
        return total_bts

    def formatTimeFromNow(self, secs=0):
        """ Properly Format Time that is `x` seconds in the future
            :param int secs: Seconds to go in the future (`x>0`) or the
                             past (`x<0`)
            :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
            :rtype: str
        """
        return datetime.utcfromtimestamp(time.time() + int(secs)).strftime('%Y-%m-%dT%H:%M:%S')

    def get_filled_orders(self):
        filled_orders_markets = {}
        for market in self.settings["markets"]:
            quote_symbol, base_symbol = market.split(self.config.market_separator)
            base_id = self.dex.rpc.get_asset(base_symbol)['id']
            quote_id = self.dex.rpc.get_asset(quote_symbol)['id']
            m = {"base": base_id, "quote": quote_id}
            filled_orders = self.dex.ws.get_fill_order_history(quote_id, base_id, 1000, api="history")
            price_list = []
            for order in filled_orders:
                timestamp = datetime.strptime(order['time'], "%Y-%m-%dT%H:%M:%S")
                seconds_ago = (datetime.now() - timestamp).total_seconds()
                op = order['op']
                if seconds_ago <= self.settings["filled_order_age"]:
                    price_data = {
                        "price": self.dex._get_price_filled(order, m),
                        "seconds_ago": (datetime.now() - timestamp).total_seconds(),
                        "volume": op['pays']['amount'] if op['pays']['asset_id'] == quote_id else op['receives']['amount']
                    }
                    price_list.append(price_data)
            filled_orders_markets[market] = price_list
        return filled_orders_markets

    def price_filled_orders(self, market):
        price_list = self.filled_orders[market]
        price_weight_total = sum([order['volume'] * (1 / (self.settings["time_weight_factor"] * order['seconds_ago'])) * order['price'] for order in price_list])
        weight_total = sum([order['volume'] * (1 / (self.settings["time_weight_factor"] * order['seconds_ago'])) for order in price_list])
        volume_total = sum([order['volume'] for order in price_list])
        try:
            price = (price_weight_total / weight_total)
        except ZeroDivisionError:
            return None
        else:
            if volume_total >= self.settings["minimum_volume"]:
                return price
            else:
                return None

    def price_feed(self, market):
        if "settlement_price" in self.ticker[market]:
            return(self.ticker[market]["settlement_price"] * (1 + self.settings["target_price_offset_percentage"] / 100))
        else:
            raise Exception("Pair %s does not have a settlement price!" % market)

    def price_target(self, market):
        return float(self.settings['target_price']) * (1 + self.settings["target_price_offset_percentage"] / 100)

    def price_bid_ask(self, market):
        return (self.ticker[market]['highestBid'] + self.ticker[market]['lowestAsk']) / 2

    def price_last(self, market):
        return self.ticker[market]['last']

    def get_price(self, market, target_price=None):
        if not target_price:
            target_price = self.settings['target_price']
        if isinstance(target_price, float) or isinstance(target_price, int):
            return self.price_target
        elif (isinstance(target_price, str) and
            target_price is "settlement_price" or
            target_price is "feed" or
            target_price is "price_feed"):
            return self.price_feed(market)
        elif (isinstance(target_price, str) and
            target_price is "filled_orders"):
            return self.price_filled_orders(market)
        elif (isinstance(target_price, str) and
            target_price is "bid_ask" or
            target_price is "gap"):
            return self.price_bid_ask(market)
        elif (isinstance(target_price, str) and
            target_price is "last"):
            return self.price_last(market)

        if isinstance(target_price, dict):
            price_weight_sum = sum([self.get_price(market, target_price=target) * weight for target, weight in target_price.items() if self.get_price(market, target_price=target) > 0])
            weight_sum = sum([weight for target, weight in target_price.items() if self.get_price(market, target_price=target) > 0])
            return price_weight_sum / weight_sum

