#!/usr/bin/env python
# coding: utf-8

import os.path
import json
token_path = os.path.expanduser("~/.api_tokens/.iex_cloud_config.json")
with open(token_path) as f:
    configs = json.loads(f.read())


def get_base_url(env="sandbox"):
    return configs[env]["BASE_URL"]


def get_api_token(type="PUBLISHABLE", env="sandbox"):
    return configs[env]["API_TOKEN"][type]


def get_token(env="cloud"):
    token = None
    token_path = os.path.expanduser("~/.api_tokens/.quandl_config.json")
    with open(token_path) as f:
        configs = json.loads(f.read())
        token = configs[env]["API_TOKEN"]["SECRET"]
    return token

# Function sourced from 
# https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]   


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

def quote_tickers(tickers):
    return f"{tuple([f'{t}' for t in tickers])}"