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
from strategies.maker import MakerRamp, MakerSellBuyWalls

# Each bot has its individual name and carries the strategy and settings
bots = {}

#############################
# MakerSellBuyWalls
#############################
bots["MakerWall"] = {"bot" : MakerSellBuyWalls,
                     # markets to serve
                     "markets" : ["EUR : BTS", "CAD : BTS", "SILVER : BTS"],
                     # target_price to place Ramps around (floating number or "feed")
                     "target_price" : "feed",
                     # +-percentage offset from target_price
                     "target_price_offset_percentage" : 0,
                     # allowed spread, your lowest orders will be placed here
                     "spread_percentage" : 2,
                     # The amount of funds (%) you want to use
                     "volume_percentage" : 50,
                     # Place symmetric walls on both sides?
                     "symmetric_sides" : False,
                     # Serve only on of both sides
                     "only_buy" : False,
                     "only_sell" : False,
                     # Order expiry time in seconds
                     "expiration" : 2*60*60*interval # expiry time is 2 times the interval the bot runs at.
                     }