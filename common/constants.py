from datetime import datetime as dt

DB_NAME = 'database.db'

DEFAULT_TICKERS = ['^GSPC', '^FTSE', '^BSESN', '^NSEI', '^MXX', '^N225']

DEFAULT_START_DATE = '2000-01-01'
DEFAULT_START_DATE_DT = dt.strptime(DEFAULT_START_DATE, '%Y-%m-%d')
DEFAULT_RET_ATTR_START_DATE_DT = dt.strptime('2010-01-01', '%Y-%m-%d')

DEFAULT_END_DATE = '2024-06-30'
DEFAULT_END_DATE_DT = dt.strptime(DEFAULT_END_DATE, '%Y-%m-%d')
DEFAULT_RET_ATTR_END_DATE_DT = dt.strptime('2012-12-31', '%Y-%m-%d')

DATE_FORMAT = '%Y-%m'

DEFAULT_PORTFOLIO_ID = 'PF_01'
DEFAULT_PORTFOLIO_NAME = 'Portfolio_01'