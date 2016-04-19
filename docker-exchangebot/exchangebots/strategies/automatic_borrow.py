from .basestrategy import BaseStrategy
from datetime import datetime
import math


class AutomaticBorrow(BaseStrategy):
    """ Automatically borrows bitAssets and adjusts the positions when outside of the minimum_change_percentage threshold.
        **Settings**:
        
        * **minimum_change_percentage**: minimum difference between the current and calculated position to trigger an update
        * **ratio**: The desired collateral ratio (if you combine this bot with MaintainCollateralRatio set this to target_ratio
        * **skip_blocks**: Checks the collateral ratio only every x blocks
        
        .. code-block:: python

            from strategies import AutomaticBorrow
            bots["AutomaticBorrow"] = {"bot" : AutomaticBorrow,
                                 "markets" : ["USD : BTS"],
                                 "ratio" : 2.5,
                                 "minimum_change_percentage" : 10,
                                 "skip_blocks" : 5,
                                 }


    """
    
    block_counter = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init(self):
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

        """ After startup, execute one tick()
        """
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
        total_bts = total_collateral + balances["BTS"]

        ticker = self.dex.returnTicker()
        quote_amounts = {}
        for m in self.settings["markets"]:
            quote, base = m.split(self.config.market_separator)
            quote_amount = total_bts * (self.config.borrow_percentages[quote] / 100) * ticker[m]['settlement_price']
            quote_amounts[quote] = quote_amount
        return quote_amounts

    def tick(self):
        self.block_counter += 1
        if (self.block_counter % self.settings["skip_blocks"]) == 0:
            print("%s | Amount of blocks since bot has been started: %d" % (datetime.now(), self.block_counter))

            debt_positions = self.dex.list_debt_positions()
            quote_amounts = self.calculate_quote_amounts(debt_positions)

            if len(debt_positions) == 0:
                print("%s | No debt positions, placing them... " % datetime.now())
                for symbol, amount in quote_amounts.items():
                    self.dex.borrow(amount, symbol, self.settings["ratio"])
            elif len(debt_positions) == 3:
                for symbol, amount in quote_amounts.items():
                    change_percentage = math.fabs((amount/debt_positions[symbol]['debt']) - 1)
                    print("%s | Calculated amount: %.4f | Current amount: %.4f | Change: %.2f " % (datetime.now(), amount, debt_positions[symbol]['debt'], change_percentage))
                    if change_percentage >= self.settings("minimum_change_percentage"):
                        delta_amount = amount - debt_positions[symbol]['debt']
                        self.adjust_debt_amount(delta_amount, symbol)
            else:
                print("%s | Something is wrong, %d amount of debt positions " % (datetime.now(), len(debt_positions)))