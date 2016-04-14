import matplotlib as mpl
mpl.use('Cairo')
import matplotlib.pyplot as plt
import numpy as np
from numpy import ma


def graph_market_stats_v2(order_data, trading_pair, path):
    plt.clf()
    Xa = list(order_data['asks'].keys())
    Ya = list(order_data['asks'].values())
    Y2a = [tuple[0] for tuple in Ya]
    Y1a = [tuple[1] for tuple in Ya]

    Xb = list(order_data['bids'].keys())
    Yb = list(order_data['bids'].values())
    Y2b = [tuple[0] for tuple in Yb]
    Y1b = [tuple[1] for tuple in Yb]
   
    p1 = plt.plot(Xa, Y1a, color='#FF7F0E', drawstyle='steps-post')
    p2 = plt.plot(Xa, Y2a, color='#1F77B4', drawstyle='steps-post')
    p3 = plt.plot(Xb, Y1b, color='#FF7F0E', drawstyle='steps-post')
    p4 = plt.plot(Xb, Y2b, color='#1F77B4', drawstyle='steps-post')
    ax = plt.gca()
    
    fill_between_steps(ax, Xa, Y1a, 0, step_where='post', color='#FF7F0E')
    fill_between_steps(ax, Xa, Y2a, Y1a, step_where='post', color='#1F77B4')
    fill_between_steps(ax, Xb, Y1b, 0, step_where='post', color='#FF7F0E')
    fill_between_steps(ax, Xb, Y2b, Y1b, step_where='post', color='#1F77B4')
    
    plt.xlim((-5,5))
    plt.ylim((0,50000))
    plt.xticks(range(-5,6))
    plt.grid()
    plt.ylabel('Liquidiy (BTS)')
    plt.xlabel('<- Bids | Spread percentage (%) | Asks ->')
    plt.title('%s:%s orders at spread percentage' % (trading_pair[0], trading_pair[1]))
    leg = plt.legend((p1[0], p2[0]), ('Bot orders', 'All orders'))
    
    for legobj in leg.legendHandles:
        legobj.set_linewidth(10.0)

    plt.draw()
    plt.savefig(path, dpi=400)

    
def graph_market_stats(volume_data, trading_pair, path):
    bot_ask_volume, bot_bid_volume, other_ask_volume, other_bid_volume = [], [], [], []
    percents = []
    for percent, volumes in volume_data[trading_pair].items():
        percents.append(percent)
        other_bid_volume.append(volumes[0] - volumes[2])
        other_ask_volume.append(volumes[1] - volumes[3])
        bot_bid_volume.append(volumes[2])
        bot_ask_volume.append(volumes[3])
    bot_bid_volume = list(reversed(bot_bid_volume)) + bot_ask_volume
    other_bid_volume = list(reversed(other_bid_volume)) + other_ask_volume
    percents = list([a * -1 for a in reversed(percents)]) + percents

    p1 = plt.bar(percents, other_bid_volume, width, color='#1F77B4', linewidth=0)
    p2 = plt.bar(percents, bot_bid_volume, width, color='#FF7F0E', bottom=other_bid_volume, linewidth=0)
    
    width = 0.5
    ax = plt.axes()        
    ax.yaxis.grid()
    plt.ylabel('Liquidiy (BTS)')
    plt.xlabel('<- Bids | Spread percentage (%) | Asks ->')
    plt.title('%s:%s orders at spread percentage' % (trading_pair[0], trading_pair[1]))
    plt.legend((p1[0], p2[0]), ('Bot orders', 'Other orders'))

    plt.draw()
    plt.savefig(path, dpi=400)
    

def fill_between_steps(ax, x, y1, y2=0, step_where='pre', **kwargs):
    ''' fill between a step plot and 

    Parameters
    ----------
    ax : Axes
       The axes to draw to

    x : array-like
        Array/vector of index values.

    y1 : array-like or float
        Array/vector of values to be filled under.
    y2 : array-Like or float, optional
        Array/vector or bottom values for filled area. Default is 0.

    step_where : {'pre', 'post', 'mid'}
        where the step happens, same meanings as for `step`

    **kwargs will be passed to the matplotlib fill_between() function.

    Returns
    -------
    ret : PolyCollection
       The added artist

    '''
    if step_where not in {'pre', 'post', 'mid'}:
        raise ValueError("where must be one of {{'pre', 'post', 'mid'}} "
                         "You passed in {wh}".format(wh=step_where))

    # make sure y values are up-converted to arrays 
    if np.isscalar(y1):
        y1 = np.ones_like(x) * y1

    if np.isscalar(y2):
        y2 = np.ones_like(x) * y2

    # temporary array for up-converting the values to step corners
    # 3 x 2N - 1 array 

    vertices = np.vstack((x, y1, y2))

    # this logic is lifted from lines.py
    # this should probably be centralized someplace
    if step_where == 'pre':
        steps = ma.zeros((3, 2 * len(x) - 1), np.float)
        steps[0, 0::2], steps[0, 1::2] = vertices[0, :], vertices[0, :-1]
        steps[1:, 0::2], steps[1:, 1:-1:2] = vertices[1:, :], vertices[1:, 1:]

    elif step_where == 'post':
        steps = ma.zeros((3, 2 * len(x) - 1), np.float)
        steps[0, ::2], steps[0, 1:-1:2] = vertices[0, :], vertices[0, 1:]
        steps[1:, 0::2], steps[1:, 1::2] = vertices[1:, :], vertices[1:, :-1]

    elif step_where == 'mid':
        steps = ma.zeros((3, 2 * len(x)), np.float)
        steps[0, 1:-1:2] = 0.5 * (vertices[0, :-1] + vertices[0, 1:])
        steps[0, 2::2] = 0.5 * (vertices[0, :-1] + vertices[0, 1:])
        steps[0, 0] = vertices[0, 0]
        steps[0, -1] = vertices[0, -1]
        steps[1:, 0::2], steps[1:, 1::2] = vertices[1:, :], vertices[1:, :]
    else:
        raise RuntimeError("should never hit end of if-elif block for validated input")

    # un-pack
    xx, yy1, yy2 = steps

    # now to the plotting part:
    return ax.fill_between(xx, yy1, y2=yy2, **kwargs)