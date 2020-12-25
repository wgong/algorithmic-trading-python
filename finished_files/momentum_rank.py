#!/usr/bin/env python
# coding: utf-8

# # Quantitative Momentum Strategy
# 
# "Momentum investing" means investing in the stocks that have increased in price the most.
# 
# Adapted from https://github.com/nickmccullum/algorithmic-trading-python/blob/master/finished_files/002_quantitative_momentum_strategy.ipynb

import numpy as np #The Numpy numerical computing library
import pandas as pd #The Pandas data science library
import requests #The requests library for HTTP requests in Python
import xlsxwriter #The XlsxWriter libarary for 
import math #The Python math module
from scipy import stats #The SciPy stats module
from statistics import mean

import datetime
import sys

import api_token  as gwg # handle iexcloud API tokens


env = "cloud" # "sandbox"  # 
BASE_URL, IEX_CLOUD_API_TOKEN = gwg.get_base_url(env=env), gwg.get_api_token(env=env)

BATCH_SIZE = 100




def momentum_rank(file_csv, TOP_N=100, WRITE_ALL_DF=False):
    """Given a csv file with a list of Tickers, rank them by price momentum

    2-3 Output files are generated:
        - f"watchlist_{filename}_top{TOP_N}_{today.strftime('%Y-%m-%d')}.csv"
        - f"spreadsheet_{filename}_top{TOP_N}_{today.strftime('%Y-%m-%d')}.xlsx"
        - f"spreadsheet_{filename}_all_{today.strftime('%Y-%m-%d')}.xlsx"  (if df size > TOP_N and WRITE_ALL_DF=True)
    """
    filename = file_csv.replace(".csv", "").replace(".txt", "")

    # prepare output file-names
    today = datetime.datetime.now()
    xlsx_file = f"spreadsheet_{filename}_top{TOP_N}_{today.strftime('%Y-%m-%d')}.xlsx"
    xlsx_file_all = f"spreadsheet_{filename}_all_{today.strftime('%Y-%m-%d')}.xlsx"
    watchlist_file = f"watchlist_{filename}_top{TOP_N}_{today.strftime('%Y-%m-%d')}.csv"

    time_periods = [
        'Five-Day',
        'One-Month',
        'Three-Month',
        'Six-Month',
        'One-Year'
    ]
    price_return_cols = [f'{time_period} Price Return' for time_period in time_periods]
    # price_return_cols

    hqm_columns = [
        'Ticker', 
        'Name',
        'Number of Shares to Buy', 
        'Price', 
        'Five-Day Price Return',
        'One-Month Price Return',
        'Three-Month Price Return',
        'Six-Month Price Return',
        'One-Year Price Return', 
        'Five-Day Return Percentile',
        'One-Month Return Percentile',
        'Three-Month Return Percentile',
        'Six-Month Return Percentile',
        'One-Year Return Percentile',
        'HQM Score'
    ]


    # ## Load Stock Ticker
    # header = "Ticker, Name, Sector_File, TopN, WRITE_ALL"
    df = pd.read_csv(
        file_csv 
        # names=[c.strip() for c in header.split(",")],
        # skiprows=[0]
    )

    stocks = list(set(df["Ticker"].values.tolist()))  # dedup

    symbol_groups = list(gwg.chunks(stocks, BATCH_SIZE))
    symbol_strings = []
    for i in range(0, len(symbol_groups)):
        symbol_strings.append(','.join(symbol_groups[i]))

    hqm_df = pd.DataFrame(columns = hqm_columns)

    for symbol_string in symbol_strings:
        batch_api_call_url = f'{BASE_URL}/stable/stock/market/batch/?types=stats,quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
        data = requests.get(batch_api_call_url).json()
        for symbol in symbol_string.split(','):
            try:
                hqm_df = hqm_df.append(
                    pd.Series([
                        symbol, 
                        data[symbol]['stats']['companyName'],
                        'N/A',
                        data[symbol]['quote']['latestPrice'],
                        data[symbol]['stats']['day5ChangePercent'],
                        data[symbol]['stats']['month1ChangePercent'],
                        data[symbol]['stats']['month3ChangePercent'],
                        data[symbol]['stats']['month6ChangePercent'],
                        data[symbol]['stats']['year1ChangePercent'],
                        'N/A',
                        'N/A',
                        'N/A',
                        'N/A',
                        'N/A',
                        'N/A'
                    ], 
                    index = hqm_columns
                    ), 
                    ignore_index = True
                )
            except Exception as ex:
                print(f"symbol = {symbol}\n Error={str(ex)}")


    hqm_df = hqm_df.dropna(how='any', 
                    subset=price_return_cols)
    # hqm_df[hqm_df["One-Year Price Return"].isnull()]

    if hqm_df.shape[0] < TOP_N and WRITE_ALL_DF:
        WRITE_ALL_DF = False

    # ## Calculating Momentum Percentiles
    for row in hqm_df.index:
        for time_period in time_periods:
            hqm_df.loc[row, f'{time_period} Return Percentile'] = 0.01*stats.percentileofscore(hqm_df[f'{time_period} Price Return'], hqm_df.loc[row, f'{time_period} Price Return'])


    # ## Calculating the HQM Score
    # The `HQM Score` will be the arithmetic mean of the momentum percentile scores 
    for row in hqm_df.index:
        momentum_percentiles = []
        for time_period in time_periods:
            momentum_percentiles.append(hqm_df.loc[row, f'{time_period} Return Percentile'])
        hqm_df.loc[row, 'HQM Score'] = mean(momentum_percentiles)


    # ## Selecting the Best Momentum Stocks
    # As before, we can identify the 50 best momentum stocks in our universe by sorting the DataFrame on the `HQM Score` column and dropping all but the top 50 entries.
    hqm_df.sort_values(by = 'HQM Score', ascending = False, inplace=True)

    if WRITE_ALL_DF:
        hqm_df_all = hqm_df.copy()
        
    hqm_df = hqm_df[:(TOP_N+1)]

    hqm_df.reset_index(drop = True, inplace = True)


    # ## Formatting .xlsx File
    # 
    # * String format for tickers
    # * \$XX.XX format for stock prices
    # * \$XX,XXX format for market capitalization
    # * Integer format for the number of shares to purchase

    writer = pd.ExcelWriter(xlsx_file, engine='xlsxwriter')

    background_color = '#0a0a23'
    font_color = '#ffffff'

    string_template = writer.book.add_format(
            {
                'font_color': font_color,
                'bg_color': background_color,
                'border': 1
            }
        )

    dollar_template = writer.book.add_format(
            {
                'num_format':'$0.00',
                'font_color': font_color,
                'bg_color': background_color,
                'border': 1
            }
        )

    integer_template = writer.book.add_format(
            {
                'num_format':'0',
                'font_color': font_color,
                'bg_color': background_color,
                'border': 1
            }
        )

    percent_template = writer.book.add_format(
            {
                'num_format':'0.0%',
                'font_color': font_color,
                'bg_color': background_color,
                'border': 1
            }
        )

    column_formats = { 
            'A': ['Ticker', string_template],
            'B': ['Name', string_template], 
            'C': ['Number of Shares to Buy', integer_template],
            'D': ['Price', dollar_template],
            'E': ['Five-Day Price Return', percent_template], 
            'F': ['One-Month Price Return', percent_template], 
            'G': ['Three-Month Price Return', percent_template],
            'H': ['Six-Month Price Return', percent_template],
            'I': ['One-Year Price Return', percent_template],
            'J': ['Five-Day Return Percentile', percent_template],
            'K': ['One-Month Return Percentile', percent_template],
            'L': ['Three-Month Return Percentile', percent_template],
            'M': ['Six-Month Return Percentile', percent_template],
            'N': ['One-Year Return Percentile', percent_template], 
            'O': ['HQM Score', percent_template]
    }
    hqm_df.to_excel(writer, sheet_name='Momentum Strategy', index = False)

    for column in column_formats.keys():
        writer.sheets['Momentum Strategy'].set_column(f'{column}:{column}', 10, column_formats[column][1])
        writer.sheets['Momentum Strategy'].write(f'{column}1', column_formats[column][0], string_template)

    writer.save()

    if WRITE_ALL_DF:
        writer = pd.ExcelWriter(xlsx_file_all, engine='xlsxwriter')
        hqm_df_all.to_excel(writer, sheet_name='Momentum Strategy', index = False)

        for column in column_formats.keys():
            writer.sheets['Momentum Strategy'].set_column(f'{column}:{column}', 10, column_formats[column][1])
            writer.sheets['Momentum Strategy'].write(f'{column}1', column_formats[column][0], string_template)

        writer.save()


    # ### save watchlist
    tickers = hqm_df[['Ticker']]
    tickers.to_csv(watchlist_file, index=False)

    return watchlist_file


if __name__ == "__main__":

    if len(sys.argv) > 1:
        for file_csv in sys.argv[1:]:
            print(f"file_csv = {file_csv}")
            wl = momentum_rank(file_csv, TOP_N=100, WRITE_ALL_DF=True)
            print(f"watchlist file = {wl}")

    else:

        WRITE_ALL_DF = True
        TOP_N = 20
        file_csv = "stocks-ETF-sectors.csv"
        # First, rank sectors
        print(f"file_csv = {file_csv}")
        momentum_rank(file_csv, TOP_N=TOP_N, WRITE_ALL_DF=WRITE_ALL_DF)

        # loop over each sector to identify top stocks within
        header = "Ticker, Name, Sector_File, TopN, WRITE_ALL"
        ETF_COLS = [c.strip() for c in header.split(",")]
        df = pd.read_csv("stocks-ETF-sectors.csv",
                names=ETF_COLS, 
                skiprows=[0])

        df = df[["Sector_File", "TopN", "WRITE_ALL"]]
        watchlists = []
        for row in df.index:
            file_csv, TOP_N, WRITE_ALL = df.loc[row,:].tolist()
            print(f"Momentum Ranking ... {file_csv.strip()}, {TOP_N}, {bool(WRITE_ALL)}")

            wl=momentum_rank(file_csv.strip(), TOP_N=TOP_N, WRITE_ALL_DF=bool(WRITE_ALL))
            watchlists.append(wl)

        df_combined = pd.read_csv(watchlists[0])
        tmp_sector = watchlists[0].replace(".csv", "")
        df_combined["Sector"] = tmp_sector
        dt_str = tmp_sector.split("_")[-1]
        for i in range(1,len(watchlists)):
            df = pd.read_csv(watchlists[i])
            df["Sector"] = watchlists[i].replace(".csv", "")
            df_combined = pd.concat([df_combined, df], ignore_index=True)

        file_combined = f"watchlist_combined_{dt_str}.csv"
        df_combined.to_csv(file_combined, index=False)
        file_combined = f"combined.csv"
        df_combined.to_csv(file_combined, index=False)

        # aggregate watchlist
        momentum_rank(file_combined, TOP_N=50, WRITE_ALL_DF=True)








