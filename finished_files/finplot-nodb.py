"""
adapted from https://github.com/highfestiva/finplot/blob/master/finplot/example-snp500.py
"""
import datetime
from time import time
from io import StringIO
import os, os.path
import signal
import sys

import re
# https://stackoverflow.com/questions/56820110/how-can-i-sanitize-a-string-so-that-it-only-contains-only-printable-ascii-chars

from importlib import reload


# from sqlalchemy import create_engine

import pandas as pd
import requests

import yfinance as yf

import finplot
from importlib import reload
# https://stackoverflow.com/questions/437589/how-do-i-unload-reload-a-python-module
# workaround issue
# Segmentation fault      (core dumped) python3 $MOM101_HOME/finplot-watchlist.py $*

global fa_results

def read_ticker(file_csv):
    """Read tickers from a CSV or text file,
    assuming 1st line is header, 1st column named 'Ticker'
    otherwise, treat it as a Symbol
    All other linese, 1st item is considered a ticker
    """
    tickers = []
    with open(file_csv) as f:
        all_lines = f.read().split("\n")
        all_lines = [l.strip() for l in all_lines if l.strip()]
    for n, line in enumerate(all_lines):
        cols = [c.strip().upper() for c in line.split(",") if c.strip()]
        if n == 0 and cols[0] in ["TICKER", "SYMBOL"]:
            continue
        tickers.append(cols[0])
    return list(set(tickers))


def sanitize(s):
    """Sanitize a string to contain ASCII only"""
    s = s.replace("\t", "    ")
    return re.sub(r"[^ -~]", "", s)



NUM_OF_MONTHS = 18
MA_FAST = 15
MA_SLOW = 50
MA_LONG = 200
MACD_FAST = 12
MACD_SLOW = 26
MACD_AVG  = 9
MACD_FACTOR = 3
TREND_FACTOR = 0.4



TABLE_NAME = "ticker"

today_str = datetime.datetime.now().strftime('%Y-%m-%d')

color_names = "blue       orange     green      red        purple     brown        pink     black      yellow    light-blue"
colors = [c.strip() for c in color_names.split(" ") if c.strip()]
COLOR_IDX = {}
for i,c in enumerate(colors):
    COLOR_IDX[c] = i


def keyboardInterruptHandler(signal, frame):
    print("KeyboardInterrupt (ID: {}) has been caught. Quit...".format(signal))
    exit(0)

signal.signal(signal.SIGINT, keyboardInterruptHandler)
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
    global file_png
    # # print(__file__)
    # pardir = os.path.dirname(__file__)
    # chart_dir = os.path.join(pardir, "charts", today_str)
    # if not os.path.exists(chart_dir):
    #     os.mkdir(chart_dir)
    # file_png = os.path.join(chart_dir, f"{symbol}_{today_str}.png")
    # print(file_png)
    with open(file_png, 'wb') as f:
        finplot.screenshot(f)



def get_sector_profiles_nodb(symbols):
    """
        Get sector,profile info from yfinance
    """

    print(f"symbols = {symbols}")

    query_results = []
    for symbol in symbols:
        sector = industry = website = profile = num_emp = pct_shorts = book_value = prof_data = None
        try:
            # use yfinance
            # prof_data = YahooFinancials(symbol).get_stock_profile_data()[symbol]
            prof_data = yf.Ticker(symbol).info
            sector = prof_data.get("sector", "N/A")
            industry = prof_data.get("industry", "N/A")
            website = prof_data.get("website", "N/A")
            num_emp = prof_data.get("fullTimeEmployees", 0)
            profile = prof_data.get("longBusinessSummary", "N/A")
            pct_shorts = 100*prof_data.get("sharesPercentSharesOut", 0)
            book_value = prof_data.get("bookValue", 0)
            query_results.append([symbol,sector,industry,website,num_emp,profile,pct_shorts,book_value])
        except Exception as ex:
            print(str(ex))

    return query_results



def plt_chart(fa_info, save_chart=False, interactive=False):
    global df
    global symbol
    global file_png
    # load data and convert date

    file_png = ""
    symbol,sector,industry,website,num_emp,profile,pct_shorts,book_value = fa_info

    return_result = (None, None)
    end_t = int(time()) 
    start_t = end_t - NUM_OF_MONTHS*30*24*60*60 
    interval = '1d'
    url = 'https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=%s&events=history' % (symbol, start_t, end_t, interval)

    try:
        r = requests.get(url)
        df = pd.read_csv(StringIO(r.text))
        if df.empty:
            print(f"[Warn] symbol {symbol} has no data")
            return return_result

        if df.shape[0] < MA_SLOW:
            print(f"[Warn] symbol {symbol} has fewer than {MA_SLOW} data points")
            return return_result

    except Exception as ex:
        print(f"[Error] failed to download quote from Yahoo finance for {symbol}")
        return return_result

    last_date = str(df.tail(1)['Date'].values[0]).split("T")[0]

    df['Date'] = pd.to_datetime(df['Date']).astype('int64') # use finplot's internal representation, which is ns

    log_msg = ""
    if sector:
        title = f"[{symbol}]       {website} - {sector} - {industry} - emp: {num_emp} - shorts: {pct_shorts}% - book: {book_value}          {last_date}"
        log_msg += title + "\n" + sanitize(profile) 
    else:
        title = f"[{symbol}]           {last_date}"
        log_msg += title
    log_msg += "\n======================================================="

    # print(log_msg)
    # with open("_finplot-watchlist.log", "a") as f:
    #     f.write(log_msg)

    ax,ax1,ax2 = finplot.create_plot(title, rows=3)

    # plot price 
    finplot.candlestick_ochl(df[['Date','Open','Close','High','Low']], ax=ax)
    hover_label = finplot.add_legend(symbol, ax=ax)
    ma15=df.Close.ewm(span=MA_FAST).mean()
    ma50=df.Close.ewm(span=MA_SLOW).mean()
    ma200=df.Close.ewm(span=MA_LONG).mean()
    finplot.plot(ma15, ax=ax, color=COLOR_IDX["blue"], width=1)
    finplot.plot(ma50, ax=ax, color=COLOR_IDX["red"], width=2)
    finplot.plot(ma200, ax=ax, color=COLOR_IDX["green"], width=3)

    # plot macd with standard colors first
    macd = ma15-ma50
    signal = macd.ewm(span=MACD_AVG).mean()
    trend = TREND_FACTOR*(ma50-ma200)
    df['macd_diff'] = MACD_FACTOR*(macd - signal)

    finplot.volume_ocv(df[['Date','Open','Close','macd_diff']], ax=ax1, colorfunc=finplot.strength_colorfilter)
    finplot.plot(macd, ax=ax1)
    # finplot.plot(signal, ax=ax1, legend='Signal')
    finplot.plot(macd, ax=ax1, width=COLOR_IDX["red"])
    finplot.plot(signal, ax=ax1, color=COLOR_IDX["black"])
    finplot.plot(trend, ax=ax1, width=2, color=COLOR_IDX["blue"])

    # # change to b/w coloring templates for next plots
    # finplot.candle_bull_color = finplot.candle_bear_color = '#000'
    # finplot.volume_bull_color = finplot.volume_bear_color = '#333'
    # finplot.candle_bull_body_color = finplot.volume_bull_body_color = '#fff'


    # plot volume
    # axo = ax.overlay()
    vol_factor = 100000
    df['Volume'] = df['Volume']/vol_factor
    finplot.volume_ocv(df[['Date','Open','Close','Volume']], ax=ax2)
    finplot.plot(df.Volume.ewm(span=20).mean(), ax=ax2, color=COLOR_IDX["black"], width=2)

    # if interactive:
    #     finplot.set_time_inspector(update_legend_text, ax=ax, when='hover')
    #     finplot.add_crosshair_info(update_crosshair_text, ax=ax)

    if save_chart:

        # print(__file__)
        pardir = os.path.dirname(__file__)
        chart_dir = os.path.join(pardir, "charts", today_str)
        if not os.path.exists(chart_dir):
            os.mkdir(chart_dir)
        file_png = os.path.join(chart_dir, f"{symbol}_{today_str}.png")
        # print(file_png)

        finplot.timer_callback(save, 0.5, single_shot=True) # wait some until we're rendered

    # print(chart_info)
    return file_png, log_msg

def generate_html(file_csv, file_png, i):  
    """generate a html file in $MOM101_HOME/research folder

    Args:
        file_csv - watchlist filename
        file_png - 

    Return:
        None    
    """
    global fa_results
    global df_symbol, fa_dict



    if i:
        html_mode = "a"
    else:
        html_mode = "w"
    # root_dir = os.environ['MOM101_HOME']
    root_dir = os.path.dirname(__file__)
    filename, _ = os.path.splitext(os.path.basename(file_csv))
    file_html = os.path.join(root_dir, "research", f"{filename}.html")
    with open(file_html, html_mode) as f:
        # create a summary table at the top
        if i == 0:
            table_str = f"""
            <h3><a name=summary>Summary</a></h3>

            <table border="ipx">
            <tr><th>Symbol</th>
                <th>Sector</th>
                <th>Industry</th>
                <th>URL</th>
                <th>#Employees</th>
                <th>%Shorts</th>
                <th>Book</th>
                <th>Score</th>
                </tr>
            """
            for idx in df_symbol.index:
                symbol = df_symbol.loc[idx, "Ticker"]
                score  = df_symbol.loc[idx, "HQM Score"]

                symbol,sector,industry,website,num_emp,profile,pct_shorts,book_value = \
                    fa_dict.get(symbol, [symbol,"N/A","N/A","N/A",0,"N/A",0,0])


                table_str += f"""
                    <tr><td><a href="#{symbol}">{symbol}</a></td>
                        <td>{sector}</td>
                        <td>{industry}</td>
                        <td><a href={website}>{website}</a></td>
                        <td>{num_emp}</td>
                        <td>{score:.1f}</td>
                        <td>{pct_shorts}%</td>
                        <td>{book_value}</td>
                        </tr>
                """

            table_str += "</table>"
            f.write(table_str)

        symbol = df_symbol.loc[i, "Ticker"]
        symbol,sector,industry,website,num_emp,profile,pct_shorts,book_value = \
            fa_dict.get(symbol, [symbol,"N/A","N/A","N/A",0,"N/A",0,0])

        html_str = f"""
            <h3><a name="{symbol}" href="https://finviz.com/quote.ashx?t={symbol}">{symbol}</a> </h3>
            <table>
            <tr><td> <img src={file_png} width=1200> </td></tr>
        """
        if sector:
            html_str += f"""
                <tr><td> <b>URL:  </b> <a href={website}> {website}</a> - <b>Sector: </b>{sector} - <b>Industry: </b> {industry} - <b>Employes: </b> {num_emp}   </td></tr>
                <tr><td> <b>Profile: </b> {profile}  </td></tr>
            """
        html_str += "</table>  <a href=#summary> [Summary] </a>"
        f.write(html_str)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            for file_csv in sys.argv[1:]:
                try:
                    df_symbol = pd.read_csv(file_csv)[['Ticker','HQM Score']]
                except:
                    df_symbol = pd.DataFrame(read_ticker(file_csv), columns=['Ticker'])
                    df_symbol["HQM Score"] = 0

                symbols = df_symbol['Ticker'].tolist()
                num_symbols = len(symbols)

                fa_dict = {}
                fa_results = get_sector_profiles_nodb(symbols)
                for row in fa_results:
                    fa_dict[row[0]] = row

                for i in df_symbol.index:

                    if not i % 5:
                        finplot = reload(finplot)
                    
                    print(f"\n==========   {i+1} / {num_symbols}   =========================\n")
                    symbol = df_symbol.loc[i, "Ticker"]
                    fa_info = fa_dict.get(symbol, [symbol,"N/A","N/A","N/A",0,"N/A",0,0])
                    file_png, log_msg = plt_chart(fa_info, save_chart=True, interactive=False)

                    if file_png:
                        print(log_msg)
                        generate_html(file_csv, file_png, i)

                    finplot.show()


    except KeyboardInterrupt:
        sys.exit()
