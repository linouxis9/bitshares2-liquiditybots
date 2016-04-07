from __future__ import print_function
import requests


bots = {
	'liquidity-bot-mauritso': { # account name
		"BTS": 8000, # asset : amount of the asset the account was funded with
		"EUR": 10.65,
		"CAD": 15.8,
		"SILVER": 0.802,
        "spread": 8, # spread % set in bot config.py (for display purposes)
        "interval": 24, # interval in hours the bot runs at (for display purposes)
        "volume": 50, # volume % the bot is set to (for display purposes)
	},
	'liquidity-bot-mauritso2' : {
        "BTS": 6000,
        "EUR": 14.988,
        "CAD": 22.29,
        "spread": 5,
        "interval": 24,
        "volume": 50,
    },
}


def get_asset_stats(asset, balances):
    market_information_request = requests.get("https://cryptofresh.com/api/asset/markets?asset=%s" % asset)
    market_information = market_information_request.json()
    balance = balances['balance']
    orders = balances['orders']
    total = balance + orders
    price_in_bts = None if asset == "BTS" else market_information['BTS']['price']
    equivalent_bts = total if asset == "BTS" else total * price_in_bts
    change_percentage = ((total / bots[bot][asset]) * 100) - 100
    
    asset_data = {
        'balance': balance,
        'orders': orders,
        'total': total,
        'equivalent_bts': equivalent_bts,
        'change_percentage': change_percentage,
        'price_in_bts': price_in_bts,
    }
    
    return asset_data

    
def get_bot_data(bot, bots=bots):
    bot_data = {}
    account_request = requests.get("https://cryptofresh.com/api/account/balances?account=%s" % bot)
    account_balances = account_request.json()
    
    for asset, balances in account_balances.iteritems(): 
        bot_data[asset] = get_asset_stats(asset, balances)
        
    equivalent_bts_list = [bot_data[asset]['equivalent_bts'] for asset in bot_data]       
    total_equivalent_bts = reduce(lambda a,b: a + b, equivalent_bts_list)
    bot_data['total_equivalent_bts'] = total_equivalent_bts
    
    return bot_data

    
def print_data(bot_data):
    print("")
    print ("Bot: ", bot.ljust(25), "Settings: %d%% spread running every %d hours with %d%% of the available funds" % (bots[bot]['spread'], bots[bot]['interval'], bots[bot]['volume']))
    
    for asset, stats in bot_data.iteritems():
        if asset == 'total_equivalent_bts':
            continue
        print (
            asset.ljust(6), 
            ("Balance: %.4f" % stats['balance']).ljust(21), 
            ("Orders: %.4f" % stats['orders']).ljust(20),
            ("Total: %.4f" % stats['total']).ljust(19),
            ("Change: %.2f%%" % stats['change_percentage']).ljust(15), 
            "BTS equivalent: %.1f" % stats['equivalent_bts']
        )
        
    print("Total equivalent BTS for bot %s: %6.f" % (bot, bot_data['total_equivalent_bts']))
    
    
if __name__ == "__main__":
    for bot in bots:
        bot_data = get_bot_data(bot)
        print_data(bot_data)