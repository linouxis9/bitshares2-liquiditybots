# Faucet used for the registration of the bot's account on the blockchain
faucet                = "https://bitshares.openledger.info/"

# Referrer used for the faucet registration
referrer              = "bitshares-munich"

# Interval to run the bot in hours
interval              = 1

# Xeroc's bot config
# Wallet RPC connection details
wallet_host           = "cli-wallet"
wallet_port           = 8092
wallet_user           = ""
wallet_password       = "reallyhardpasswordbecuasemultipleenglishwordbutnotspelcorrectly"

# Your account that executes the trades
account = "liquidity-bot-xdfx6" # prefix liquidity-bot-

# Websocket URL
witness_url           = "wss://bitshares.openledger.info/ws"

# Set of ALL markets that you inted to serve
watch_markets         = ["EUR : BTS", "CAD : BTS", "SILVER : BTS"]
market_separator      = " : "  # separator between assets

# If this flag is set to True, nothing will be done really
safe_mode             = False

# The Bots:

# Load the strategies
from strategies.maker import LiquiditySellBuyWalls

# Each bot has its individual name and carries the strategy and settings
bots = {}

bots["LiquidityWall"] = {"bot" : LiquiditySellBuyWalls,
                     "markets" : ["EUR : BTS", "CAD : BTS", "SILVER : BTS"],
                     "target_price" : "feed",
                     "target_price_offset_percentage" : 0,
                     "spread_percentage" : 4,
                     "allowed_spread_percentage" : 2,
                     "volume_percentage" : 40,
                     "symmetric_sides" : False,
                     "only_buy" : False,
                     "only_sell" : False,
                     "expiration" : 60 * 60 * 6
                     }