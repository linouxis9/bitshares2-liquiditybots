import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def graph_market_stats(volume_data, trading_pair, path):
    bot_ask_volume, bot_bid_volume, other_ask_volume, other_bid_volume = [], [], [], []
    percents = []
    for percent, volumes in volume_data[trading_pair].items():
        percents.append(percent)
        other_bid_volume.append(volumes[0] - volumes[2])
        other_ask_volume.append(volumes[1] - volumes[3])
        bot_bid_volume.append(volumes[2])
        bot_ask_volume.append(volumes[3])

    width = 0.5
    ax = plt.axes()        
    ax.yaxis.grid()

    bot_bid_volume = list(reversed(bot_bid_volume)) + bot_ask_volume
    other_bid_volume = list(reversed(other_bid_volume)) + other_ask_volume
    print (other_bid_volume)
    print(bot_bid_volume)
    percents = list([a * -1 for a in reversed(percents)]) + percents
    print(percents)
    p1 = plt.bar(percents, bot_bid_volume, width, color='#FF7F0E', bottom=other_bid_volume, linewidth=0)
    p2 = plt.bar(percents, other_bid_volume, width, color='#1F77B4', linewidth=0)

    plt.ylabel('Liquidiy (BTS)')
    plt.xlabel('<- Bids | Spread percentage (%) | Asks ->')
    plt.title('%s:%s orders at spread percentage' % (trading_pair[0], trading_pair[1]))
    plt.xticks(percents)
    plt.yticks(np.arange(0, 11000, 1000))
    plt.legend((p1[0], p2[0]), ('Bot orders', 'Other orders'))
    
    ax.set_yscale('log')

    plt.draw()
    plt.savefig(path, dpi=400)