#!/usr/bin/env python3

"""
adapted from https://github.com/highfestiva/finplot/blob/master/finplot/example-snp500.py
"""

import finplot as fplt
import pandas as pd
import requests
from io import StringIO
from time import time
import datetime

global symbol
# symbol = 'SPY'
NUM_OF_MONTHS = 18
MA_FAST = 15
MA_SLOW = 50
MA_LONG = 200
MACD_FAST = 12
MACD_SLOW = 26
MACD_AVG  = 9
MACD_FACTOR = 3

#######################################################
## update crosshair and legend when moving the mouse ##
def update_legend_text(x, y):
    global df
    global symbol
    row = df.loc[df.Date==x]
    # format html with the candle and set legend
    # fmt = '<span style="color:#%s">%%.2f</span>' % ('0bb' if (row.Open<row.Close).all() else 'a00')
    hover_label.setText('%s (%d mon) <br> O:%.2f<br> C:%.2f <br> H:%.2f <br> L:%.2f' % (symbol, NUM_OF_MONTHS, row.Open, row.Close, row.High, row.Low))
    # rawtxt = '<span style="font-size:10px">%%s %%s</span> &nbsp; O:%s<br> C:%s <br> H:%s <br> L:%s' % (fmt, fmt, fmt, fmt)
    # hover_label.setText(rawtxt % (symbol, interval.upper(), row.Open, row.Close, row.High, row.Low))

def update_crosshair_text(x, y, xtext, ytext):
    global df
    ytext = '%s (Close%+.2f)' % (ytext, (y - df.iloc[x].Close))
    return xtext, ytext

def save():
    global symbol
    png_file = f"{symbol}_{datetime.datetime.now().strftime('%Y-%m-%d')}.png"
    fplt.screenshot(open(png_file, 'wb'))


def plt_chart(save_chart=False, interactive=False):
    global df
    global symbol
    # load data and convert date
    end_t = int(time()) 
    start_t = end_t - NUM_OF_MONTHS*30*24*60*60 # twelve months
    interval = '1d'
    url = 'https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=%s&events=history' % (symbol, start_t, end_t, interval)
    r = requests.get(url)
    df = pd.read_csv(StringIO(r.text))
    df['Date'] = pd.to_datetime(df['Date']).astype('int64') # use finplot's internal representation, which is ns

    ax,ax1,ax2 = fplt.create_plot(f"{symbol}", rows=3)

    # plot price 
    fplt.candlestick_ochl(df[['Date','Open','Close','High','Low']], ax=ax)
    hover_label = fplt.add_legend('', ax=ax)
    ma15=df.Close.ewm(span=MA_FAST).mean()
    ma50=df.Close.ewm(span=MA_SLOW).mean()
    ma200=df.Close.ewm(span=MA_LONG).mean()
    fplt.plot(ma15, ax=ax)
    fplt.plot(ma50, ax=ax)
    fplt.plot(ma200, ax=ax)

    # plot macd with standard colors first
    macd = df.Close.ewm(span=MACD_FAST).mean() - df.Close.ewm(span=MACD_SLOW).mean()
    signal = macd.ewm(span=MACD_AVG).mean()
    df['macd_diff'] = MACD_FACTOR*(macd - signal)
    fplt.volume_ocv(df[['Date','Open','Close','macd_diff']], ax=ax1, colorfunc=fplt.strength_colorfilter)
    fplt.plot(macd, ax=ax1, legend='MACD')
    # fplt.plot(signal, ax=ax1, legend='Signal')
    fplt.plot(macd, ax=ax1)
    fplt.plot(signal, ax=ax1)

    # # change to b/w coloring templates for next plots
    # fplt.candle_bull_color = fplt.candle_bear_color = '#000'
    # fplt.volume_bull_color = fplt.volume_bear_color = '#333'
    # fplt.candle_bull_body_color = fplt.volume_bull_body_color = '#fff'


    # plot volume
    # axo = ax.overlay()
    vol_factor = 100000
    df['Volume'] = df['Volume']/vol_factor
    fplt.volume_ocv(df[['Date','Open','Close','Volume']], ax=ax2)
    fplt.plot(df.Volume.ewm(span=20).mean(), ax=ax2, color=1, legend="Volume")

    if interactive:
        fplt.set_time_inspector(update_legend_text, ax=ax, when='hover')
        fplt.add_crosshair_info(update_crosshair_text, ax=ax)

    if save_chart:
        fplt.timer_callback(save, 0.5, single_shot=True) # wait some until we're rendered

    return fplt

if __name__ == "__main__":

    for symbol in "SPY QQQ".split():
        # symbol = 'SPY'
        # fplt = plt_chart()
        fplt = plt_chart(save_chart=True, interactive=False)
        fplt.show()
