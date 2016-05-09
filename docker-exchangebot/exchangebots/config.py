# Faucet used for the registration of the bot's account on the blockchain
faucet = "https://bitshares.openledger.info/"

# Referrer used for the faucet registration
referrer = "bitshares-munich"


# Xeroc's bot config
# Wallet RPC connection details
wallet_host = "cli-wallet"
wallet_port = 8092
wallet_user = ""
wallet_password = "put in a password"

# Your account that executes the trades
account = "liquidity-bot-"  # prefix liquidity-bot-

# Websocket URL
witness_url = "wss://bitshares.openledger.info/ws"

# Set of ALL markets that you inted to serve
watch_markets = [
    "EUR : BTS",
    "CAD : BTS",
    "SILVER : BTS"
]
market_separator = " : "  # separator between assets


# If this flag is set to True, nothing will be done really
safe_mode = False


# Load the strategies
from strategies.liquidity_wall import LiquiditySellBuyWalls
from strategies.maintain_collateral_ratio import MaintainCollateralRatio
# Each bot has its individual name and carries the strategy and settings
bots = {}

bots["LiquidityWall"] = {
    "bot": LiquiditySellBuyWalls,
    "markets": [
        "EUR : BTS",
        "CAD : BTS",
        "SILVER : BTS"
    ],
    # Automatically borrow bitassets?
    "borrow": True,
    # How the BTS is divided for the debts. 12% means 12% of the bts is used to lend EUR.
    "borrow_percentages": {
        "EUR": 12,
        "CAD": 12,
        "SILVER": 12,
        "BTS": 64
    },
    # Minimum amount an order has to be to get placed
    "minimum_amounts": {
        "EUR": 0.20,
        "CAD": 0.30,
        "SILVER": 0.02,
    },
    "target_price": "feed",
    # the percentage the order will be placed at in relation to target_price
    "spread_percentage": 2,
    # the percentage the order may drift from spread_percentage.
    "allowed_spread_percentage": 1,
    # the percentage of the available funds to put on the market
    "symmetric_sides": False,
    "volume_percentage": 70,
    # expiration time for the orders placed by the bot in seconds
    "expiration": 60 * 60 * 3,
    # the bot runs every skip_blocks blocks (every 5 blocks means every 5*3=15 seconds)
    "skip_blocks": 5,
    # collateral ratio for the debts placed by the bot (same as target_ratio below)
    "ratio": 2.5,
}


# Turn this bot off if you don't borrow bitassets on the bot.
bots["Collateral"] = {
    "bot" : MaintainCollateralRatio,
    "markets" : ["EUR : BTS", "SILVER : BTS", "CAD : BTS"],
    "target_ratio" : 2.5,
    "lower_threshold" : 2.3,
    "upper_threshold" : 2.7,
    "skip_blocks" : 1,
}
