# Project MoM 101


## Momentum Ranking 

This is manual top-down approach to rank 5000 stocks based on Momentum scores.
It uses IEX cloud API.

### Daily Workflow

1) cd ~/projects/algorithmic-trading-python/mom101
2) momscan
3) cd scan/2020-12-28
4) finplot watchlist_stocks-ETF-sectors_20.csv
5) finplot watchlist_combined_50.csv
6) 


#### Details
`$ python3 momentum_rank.py`

sh script: `momscan`

which is based on `algorithmic-trading-python/finished_files/002_momentum_play-gwg-v2.ipynb`


- rank market/sector ETFs

  'stocks-ETF-sectors.csv':
  'stocks-DOW30.csv',
  'stocks-NASDAQ100.csv',
  'stocks-SP500.csv',
  'stocks-RUSSELL2000.csv',

  'sector-GOLD-miner.csv',
  'sector-SILVER-miner.csv',

  'sector-consumer-cyclical.csv',
  'sector-financial-services.csv',
  'sector-energy.csv',
  'sector-utilities.csv',
  'sector-industrials.csv',
  'sector-basic-materials.csv',
  'sector-healthcare.csv',
  'sector-technology.csv',
  'sector-consumer-defensive.csv',
  'sector-communication-services.csv'
  'sector-real-estate.csv',

  'sector-unknown.csv',

- scan each sector listed above and pick top-N stocks
  save them into scan folder
- watchlist_<sector>_(all|topN)_<date>.xlsx
- spreadsheet_<sector>_<date>.xlsx

an aggregate file called:

- watchlist_combined_(all|topN)_<date>.xlsx
- spreadsheet_combined_<date>.xlsx


## Automated Scan

- Download daily quotes from yahoo finance (via `yfinance`) into PostgreSQL DB;
- Perform processing and quantitative analysis, e.g. Tangents, time-series similarity;
- Pick a small set of stocks to trade

### Workflow

- download data daily
- save to PostgreSQL DB
- calculate TA using pandas and/or db stored_proc
- scan for patterns
- plot
- review to select top-20 stocks


#### Schema
- `gwgdb_schema_queries.ipynb`


#### Fundamental Analytical data - FA 
- `yfinance-download-fa.ipynb`
    - took 4 hrs to download FA data for 5000 stocks (pretty slow)
    - this is very fast: 50 sec downloaded 100 tickers for 750 days

#### Quote data - initial
- `yfinance-download-price-initial.ipynb`

#### Quote data - incremental
- `yfinance-download-price-delta.ipynb`

#### TA Processing

- ta_db_initial.ipynb
- `ta_db_initial-2.ipynb`
- `ta_db_delta.ipynb`

#### Charting

- `finplot-db.ipynb` - create chart using data from DB

- sh script: `finplot list1.csv`

    research\list1.html will be created

`$ python3 finplot-watchlist.py <watchlist.csv>`
in charts\<date> subfolder

on Windows:

    git clone https://github.com/highfestiva/finplot.git
    python setup.py install
    pip install yfinance

    cd C:\Users\19197\projects\algorithmic-trading-python\mom101
    python finplot-nodb.py test_tickers.csv

- [TODO] generate chart in background (headless) because `finplot` is for interactive charting

#### Stock Selection

`$ python3 yfinance-download-price-delta.py`
`$ python3 ta_db_initial-2.py`
`$ python3 ta_db_delta.py`

#### Tools

- `algorithmic-trading-python/mom101/gwg_utils.py`
- `algorithmic-trading-python/mom101/api_token.py`

#### Experiment

- `yfinance.ipynb` : learn yfinance
- `ta-smooth-test.ipynb`  : calculate TA and plot

- `utils.ipynb` : playground


## References

### Time-series similarity measures
- https://quant.stackexchange.com/questions/848/time-series-similarity-measures

- https://mail.google.com/mail/u/0/?hl=en&shva=1#sent?projector=1

- [A Tutorial on Cepstrum and LPCCs](http://practicalcryptography.com/miscellaneous/machine-learning/tutorial-cepstrum-and-lpccs/)


### Python library for common tasks in Music Information Retrieval (MIR)
https://github.com/jsawruk/pymir
https://github.com/jsawruk/pymir/blob/master/pymir/MFCC.py

### python_speech_features

- https://github.com/jameslyons/python_speech_features
- https://github.com/pchao6/Speech_Feature_Extraction

### Yahoo Finance

- [Intro](https://towardsdatascience.com/a-comprehensive-guide-to-downloading-stock-prices-in-python-2cd93ff821d4)

- [yfinance](https://github.com/ranaroussi/yfinance)
    Very easy to use

- [yahoofinancials](https://github.com/JECSand/yahoofinancials)
    A python module that returns stock, cryptocurrency, forex, mutual fund, commodity futures, ETF, and US Treasury financial data from Yahoo Finance.

- [Fundamental Analysis](https://pypi.org/project/FundamentalAnalysis/)


### IEX Cloud


### finplot_venv

to resolve core dump issue with finplot, 
install it into a venv:

```
sudo apt-get install python3-venv

python3 -m venv finplot_venv

source finplot_venv/bin/activate

cd ~/projects/finplot

python3 setup.py install

pip3 install requests yfinance

```

Python 3.8.5 (default, Jul 28 2020, 12:59:40) 

Finished processing dependencies for finplot==1.5.0
```
cd ~/projects/algorithmic-trading-python/mom101
finplot stocks-metals.csv
```
