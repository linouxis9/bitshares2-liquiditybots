from grapheneapi import GrapheneAPI, GrapheneWebsocketRPC
from functools import reduce

rpc = GrapheneWebsocketRPC("wss://bitshares.openledger.info/ws", "", "")
markets = [
    ("CAD", "BTS"),
    ("EUR", "BTS"),
    ("SILVER", "BTS"),
    ("USD", "BTS")
]


get_asset_symbol = lambda asset_data: asset_data['symbol']
get_asset_id = lambda asset_data: asset_data['id']
get_all_of_op = lambda account_history, op: [operation['op'][1] for operation in account_history if operation['op'][0] == op]


def get_account_orders(account_name):
    account_order_book = {}
    account_history = rpc.getFullAccountHistory(account_name, 1)
    orders = get_all_of_op(account_history, 1)
    asset_ids = list(set([order['amount_to_sell']['asset_id'] for order in orders] + [order['min_to_receive']['asset_id'] for order in orders]))
    for asset_id in asset_ids:
        asset_data = rpc.get_asset(asset_id)
        if asset_id == "1.3.0":
            continue
        order_book = {}
        order_book['bids'] = [{
                'base': order['amount_to_sell']['amount'], 
                'quote': order['min_to_receive']['amount'],
                'price': (order['amount_to_sell']['amount'] / 10 ** 5) / (order['min_to_receive']['amount'] / asset_data['precision'])
        } for order in orders if order['min_to_receive']['asset_id'] == asset_id]
        order_book['asks'] = [
            {
                'base': order['amount_to_sell']['amount'], 
                'quote': order['min_to_receive']['amount'],
                'price': (order['min_to_receive']['amount'] / 10 ** 5) / (order['amount_to_sell']['amount'] / asset_data['precision'])
            } for order in orders if order['amount_to_sell']['asset_id'] == asset_id]
        account_order_book[(asset_data['symbol'], "BTS")] = order_book
    return account_order_book
    
    
def get_volume_at_spread_percentage(order_book, settlement_price, percentage):
    bids = order_book['bids']
    asks = order_book['asks']
    bids_at_percentage = [bid for bid in bids if (float(bid['price'])/settlement_price)*100 >= 100 - percentage]
    asks_at_percentage = [ask for ask in asks if (float(ask['price'])/settlement_price)*100 <= 100 + percentage]
    bids_volume_list = [float(bid['quote']) for bid in bids_at_percentage]
    asks_volume_list = [float(ask['quote']) for ask in asks_at_percentage]
    bids_volume_at_percentage =  reduce(lambda a,b: a + b, bids_volume_list) if len(bids_volume_list) != 0 else 0
    asks_volume_at_percentage = reduce(lambda a,b: a + b, asks_volume_list) if len(asks_volume_list) != 0 else 0
    return (bids_volume_at_percentage, asks_volume_at_percentage)

    
def get_exchange_rate(asset, in_asset=True, rpc=rpc):
    asset_data = rpc.get_asset(asset)
    bitasset_data = rpc.get_objects([asset_data['bitasset_data_id']])
    base = bitasset_data[0]['current_feed']['settlement_price']['base']['amount'] / 10 ** asset_data['precision']
    quote = bitasset_data[0]['current_feed']['settlement_price']['quote']['amount'] / 10 ** 5 # assuming BTS
    price = base / quote if in_asset else quote / base
    return price
    
    
def print_volume_data(volume_data):
    for market, market_volume_data in volume_data.items():
        print("")
        print("%s : %s" % (market[0], market[1]))
        for volume_percentage, volume in market_volume_data.items(): 
            print(volume_percentage, ("Bids: %.2f" % volume[0]).ljust(15), "| Asks: %.2f" % volume[1])
     
        
if __name__ == "__main__":
    volume_data = {}
    for market in markets:
        market_volume_data = {}
        order_book = rpc.get_order_book(market[0], market[1], 50)
        for percentage in range(0, 10, 1):
            market_volume_data[percentage] = get_volume_at_spread_percentage(order_book, get_exchange_rate(market[0]), percentage)
        volume_data[market] = market_volume_data

    #print(volume_data)
    #print(rpc.getFullAccountHistory('liquidity-bot-mauritso', 1))
    volume_data = {}
    account_volume_data = get_account_orders('liquidity-bot-mauritso')
    print(account_volume_data)
    for market in account_volume_data:
        market_volume_data = {}
        order_book = account_volume_data[market]
        print(order_book)
        for percentage in range(0, 10, 1):
            market_volume_data[percentage] = get_volume_at_spread_percentage(order_book, get_exchange_rate(market[0]), percentage)
        volume_data[market] = market_volume_data
    #print_volume_data(volume_data)
    #print(volume_data)