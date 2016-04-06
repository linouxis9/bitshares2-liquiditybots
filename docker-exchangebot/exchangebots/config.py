# additional config:
# headers used in the openledger faucet post request
headers = {
	"Accept": "application/json",
	"Content-type": "application/json"
}

# referrer used for openledger registration
referrer = "bitshares-munich"

# Interval to run the bot in hours
interval = 1

# Xeroc's bot config
# Wallet RPC connection details
wallet_host           = "cli-wallet"
wallet_port           = 8092
wallet_user           = ""
wallet_password       = "reallyhardpasswordbecuasemultipleenglishwordbutnotspelcorrectly"

# Your account that executes the trades
account = "liquidity-bot-xdfx6" # prefix liquidity-bot-

# Websocket URL
#witness_url           = "wss://bitshares.openledger.info/ws"
witness_url           = "ws://146.185.144.55:8090"

# Set of ALL markets that you inted to serve
watch_markets         = ["EUR : BTS", "CAD : BTS"]
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
bots["MakerRexp"] = {"bot" : MakerRamp,
                     # markets to serve
                     "markets" : ["EUR : BTS" , "CAD : BTS"],
                     # target_price to place Ramps around (floating number or "feed")
                     "target_price" : "feed",
                     # +-percentage offset from target_price
                     "target_price_offset_percentage" : 0,
                     # allowed spread, your lowest orders will be placed here
                     "spread_percentage" : 12,
                     # The amount of funds (%) you want to use
                     "volume_percentage" : 100,
                     # Ramp goes up with volume up to a price increase of x%
                     "ramp_price_percentage" : 16,
                     # from spread/2 to ramp_price, place an order every x%
                     "ramp_step_percentage" : 3,
                     # "linear" ramp (equal amounts) or "exponential"
                     # (linearily increasing amounts)
                     "ramp_mode" : "exponential",
                     # Serve only on of both sides
                     "only_buy" : False,
                     "only_sell" : False,
                     }
