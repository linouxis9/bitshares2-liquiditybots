from __future__ import print_function
from grapheneapi import GrapheneAPI, GrapheneWebsocketRPC
from functools import reduce
import requests

in_asset = "BTS" # Needs to have a market with every asset the bot owns.
rpc = GrapheneWebsocketRPC("wss://bitshares.openledger.info/ws", "", "")
bots = {
    # account name
	'liquidity-bot-mauritso': {
        # spread % set in bot config.py (for display purposes)
        "spread": 8,
        # interval in hours the bot runs at (for display purposes)
        "interval": 24,
        # volume % the bot is set to (for display purposes)
        "volume": 50,
	},
	'liquidity-bot-mauritso2' : {
        "spread": 5,
        "interval": 24,
        "volume": 50,
    },
}


def get_symbol_amount(asset_id, amount):
    asset = rpc.get_assets([asset_id])
    amount = amount / 10 ** asset[0]['precision']
    symbol = asset[0]['symbol']
    return (symbol, amount)
    
   
def get_all_received_transactions(account_name, rpc=rpc):
    account_history = rpc.getFullAccountHistory(account_name, 1)
    received = [operation['op'][1] for operation in account_history if operation['op'][0] == 0]
    return received


def get_total_send_to_account(account_name):
    symbol_amount_dict = {}
    received_transactions = get_all_received_transactions(account_name)
    for transaction in received_transactions:
        symbol_amount = get_symbol_amount(transaction['amount']['asset_id'], transaction['amount']['amount'])
        symbol_amount_dict[symbol_amount[0]] = symbol_amount[1]
    return symbol_amount_dict
    

def get_equivalent_asset(asset, amount, in_asset, price):
    price_in_asset = None if asset == in_asset else price
    equivalent_amount = amount if asset == in_asset else amount * price_in_asset
    return equivalent_amount
    
    
def get_asset_stats(bot, asset, balances):
    total_received = get_total_send_to_account(bot)
    market_information_request = requests.get("https://cryptofresh.com/api/asset/markets?asset=%s" % asset)
    market_information = market_information_request.json()
    balance = balances['balance']
    orders = balances['orders']
    total = balance + orders
    equivalent_amount = total if asset == in_asset else get_equivalent_asset(asset, total, in_asset, market_information[in_asset]['price'])
    change_percentage = ((total / total_received[asset]) * 100) - 100
    
    asset_data = {
        'balance': balance,
        'orders': orders,
        'total': total,
        'equivalent_amount': equivalent_amount,
        'change_percentage': change_percentage,
        'total_received' : total_received[asset],
    }
    
    return asset_data

    
def get_bot_data(bot, bots=bots):
    bot_data = {}
    account_request = requests.get("https://cryptofresh.com/api/account/balances?account=%s" % bot)
    account_balances = account_request.json()
    
    for asset, balances in account_balances.items(): 
        bot_data[asset] = get_asset_stats(bot, asset, balances)
        
    equivalent_bts_list = [bot_data[asset]['equivalent_amount'] for asset in bot_data]
    total_equivalent_bts = reduce(lambda a,b: a + b, equivalent_bts_list)
    bot_data['total_equivalent_bts'] = total_equivalent_bts
    
    return bot_data

    
def print_data(bot_data):
    print("")
    print ("Bot: ", bot.ljust(25), "Settings: %d%% spread running every %d hours with %d%% of the available funds" % (bots[bot]['spread'], bots[bot]['interval'], bots[bot]['volume']))
    
    for asset, stats in bot_data.items():
        if asset == 'total_equivalent_bts':
            continue
        print (
            asset.ljust(6), 
            ("Balance: %.4f" % stats['balance']).ljust(21), 
            ("Orders: %.4f" % stats['orders']).ljust(20),
            ("Total: %.4f" % stats['total']).ljust(19),
            ("Change: %.2f%%" % stats['change_percentage']).ljust(15), 
            "%s equivalent: %.1f" % (in_asset, stats['equivalent_amount'])
        )
        
    print("Total equivalent BTS for bot %s: %6.f" % (bot, bot_data['total_equivalent_bts']))
    
if __name__ == "__main__":
    for bot in bots:
        bot_data = get_bot_data(bot)
        print_data(bot_data)    
    print("")