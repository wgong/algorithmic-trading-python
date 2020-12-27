"""
adapted from https://github.com/highfestiva/finplot/blob/master/finplot/example-snp500.py
"""
import datetime
from time import time
from io import StringIO
import os
import signal
import sys


# from sqlalchemy import create_engine

import psycopg2
from psycopg2 import Error

import pandas as pd
import requests

import yfinance as yf
from yahoofinancials import YahooFinancials
import finplot as fplt

import db_params
import api_token as gwg

NUM_OF_MONTHS = 18
MA_FAST = 15
MA_SLOW = 50
MA_LONG = 200
MACD_FAST = 12
MACD_SLOW = 26
MACD_AVG  = 9
MACD_FACTOR = 3

db_kwargs = db_params.get_db_params(
        db_name="gwgdb", 
        db_type="postgresql"
    )

connection = psycopg2.connect(**db_kwargs)


TABLE_NAME = "ticker"

today_str = datetime.datetime.now().strftime('%Y-%m-%d')

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
        fplt.screenshot(f)



def get_sector_profiles(symbols, connection):
    """
        Get sector,profile info from yfinance for missing symbol in local DB, 
        Add missing info to DB
        Query DB for all symbols, sort by sector,industry
    """

    cursor = connection.cursor()
    symbols_str = gwg.quote_tickers(symbols)
    
    select_sql = f"""select 
        symbol --,sector,industry,website,num_emp,profile 
        from ticker
        where symbol in {symbols_str}
        --order by sector,industry
        ;
    """
    cursor.execute(select_sql)
    query_results = cursor.fetchall()
    symbols_db = [i[0] for i in query_results]
    symbols_new = list(set(symbols).difference(set(symbols_db)))
    print(f"symbols_new = {symbols_new}")

    for symbol in symbols_new:
        sector = industry = website = profile = num_emp = None
        try:
            prof_data = YahooFinancials(symbol).get_stock_profile_data()[symbol]
        except Exception as ex:
            print(str(ex))

        if prof_data:
            sector,industry,website, profile, num_emp = \
                prof_data["sector"], prof_data["industry"], prof_data["website"], prof_data["longBusinessSummary"], prof_data["fullTimeEmployees"]

            print(f"sector={sector}")
            if profile or sector:
                try:
                    insert_query = f""" 
                        INSERT INTO ticker (symbol,sector,industry,website,num_emp,profile) 
                        VALUES ('{symbol}', '{sector}', '{industry}','{website}', num_emp, '{profile}')
                        ;
                    """    
                    cursor.execute(insert_query)
                    connection.commit()
                except Exception as ex:
                    print(str(ex))

    select_sql2 = f"""select 
        symbol,sector,industry,website,num_emp,profile 
        from ticker
        where symbol in {symbols_str}
        order by sector,industry,symbol
        ;
    """
    cursor.execute(select_sql2)
    query_results = cursor.fetchall()

    return query_results

def plt_chart(fa_info, save_chart=False, interactive=False):
    global df
    global symbol
    global file_png
    # load data and convert date

    symbol,sector,industry,website,num_emp,profile = fa_info

    return_result = (None, None)
    end_t = int(time()) 
    start_t = end_t - NUM_OF_MONTHS*30*24*60*60 # twelve months
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
        title = f"[{symbol}]       {website} - {sector} - {industry}           {last_date}"
        log_msg += title + "\n" + profile
    else:
        title = f"[{symbol}]           {last_date}"
        log_msg += title
    log_msg += "\n======================================================="

    print(log_msg)
    # with open("_finplot-watchlist.log", "a") as f:
    #     f.write(log_msg)

    # print(__file__)
    pardir = os.path.dirname(__file__)
    chart_dir = os.path.join(pardir, "charts", today_str)
    if not os.path.exists(chart_dir):
        os.mkdir(chart_dir)
    file_png = os.path.join(chart_dir, f"{symbol}_{today_str}.png")
    # print(file_png)


    ax,ax1,ax2 = fplt.create_plot(title, rows=3)

    # plot price 
    fplt.candlestick_ochl(df[['Date','Open','Close','High','Low']], ax=ax)
    hover_label = fplt.add_legend(symbol, ax=ax)
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
    fplt.plot(macd, ax=ax1)
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
    fplt.plot(df.Volume.ewm(span=20).mean(), ax=ax2, color=1)

    if interactive:
        fplt.set_time_inspector(update_legend_text, ax=ax, when='hover')
        fplt.add_crosshair_info(update_crosshair_text, ax=ax)

    if save_chart:
        fplt.timer_callback(save, 0.5, single_shot=True) # wait some until we're rendered

    chart_info = [symbol,file_png,sector,industry,website,profile, num_emp]
    # print(chart_info)
    return_result = (fplt, chart_info)
    return return_result

def generate_html(file_csv, chart_info):
    """generate a html file in $MOM101_HOME/research folder

    Args:
        file_csv - watchlist filename
        chart_info - 
            [symbol,file_png,sector,industry,website,profile, num_emp]

    Return:
        None    
    """
    root_dir = os.environ['MOM101_HOME']
    filename, _ = os.path.splitext(os.path.basename(file_csv))
    file_html = os.path.join(root_dir, "research", f"{filename}.html")
    with open(file_html, "a") as f:
        symbol,file_png,sector,industry,website,profile, num_emp = chart_info
        html_str = f"""
            <h3>{symbol} </h3>
            <table>
            <tr><td> <img src={file_png} width=1200> </td></tr>
        """
        if sector:
            html_str += f"""
                <tr><td> <b>URL:  </b> <a href={website}> {website}</a> - <b>Sector: </b>{sector} - <b>Industry: </b> {industry} - <b>Employes: </b> {num_emp}</td></tr>
                <tr><td> <b>Profile: </b> {profile} </td></tr>
            """
        html_str += "</table>"
        f.write(html_str)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            for file_csv in sys.argv[1:]:
                # symbols = pd.read_csv(file_csv)["Ticker"].tolist()
                symbols = gwg.read_ticker(file_csv)

                fa_results = get_sector_profiles(symbols, connection)
                num_symbols = len(fa_results)

                for i, fa_info in enumerate(fa_results):
                    print(f"\n==========   {i+1} / {num_symbols}   =========================\n")
                    po, chart_info = plt_chart(fa_info, save_chart=True, interactive=False)

                    if chart_info:
                        generate_html(file_csv, chart_info)

                    if po:
                        po.show()


    except KeyboardInterrupt:
        sys.exit()