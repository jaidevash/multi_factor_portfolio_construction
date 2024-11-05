import os
import sqlite3
import yfinance as yf
import zipfile
import pandas as pd
import logging

logging.basicConfig(
    # filename='app.log', # Log to this file
    level=logging.INFO, # Set the logging level format
    format='%(asctime)s %(name)s [%(levelname)s]: %(message)s'
)

from common.constants import *


def ingest_ticker_data(tickers=DEFAULT_TICKERS, **kwargs):

    start = kwargs.get('start', DEFAULT_START_DATE)
    end = kwargs.get('end', DEFAULT_END_DATE)

    with sqlite3.connect(f"db/{DB_NAME}") as conn:

        existing_tickers = pd.read_sql_query("SELECT DISTINCT asset_id FROM asset_prices", conn).iloc[:, 0].values
        tickers = [ticker for ticker in tickers if ticker not in existing_tickers]
        logging.info(f"Loading tickers: {', '.join(tickers)}")

        for ticker in tickers:
            data = yf.download(ticker, start=start, end=end)
            data = data.resample('ME').mean()['Close']
            to_ingest = pd.DataFrame(columns=['asset_id', 'date', 'asset_price'])
            to_ingest['date'] = data.index.strftime(DATE_FORMAT)
            to_ingest['asset_price'] = data.values
            to_ingest['asset_id'] = ticker

            try:
                ticker_name = yf.Ticker(ticker).info['longName']
            except:
                ticker_name = ''

            asset_info = pd.DataFrame(
                [[ticker, ticker_name]],
                columns=['asset_id', 'asset_name'])

            to_ingest.to_sql('asset_prices', conn, if_exists='append', index=False)
            asset_info.to_sql('assets', conn, if_exists='append', index=False)

def ingest_macroeconomic_data():

    selected_indicators = pd.read_csv('config/selected_macroeconomic_indicators.csv')
    c = selected_indicators['Selected for analysis (Y/N)'].eq('Y')
    selected_indicators = selected_indicators[c]['INDICATOR_CODE'].tolist()

    with (sqlite3.connect(f"db/{DB_NAME}") as conn):

        # Iterate through each zip file representing WorldBank indicator category (e.g. "Economy & Growth")
        for zip_file in [file for file in os.listdir('data') if file.endswith('.zip')]:

            # Open the zip file
            with zipfile.ZipFile(f"data/{zip_file}", 'r') as z:

                # Get the list of files in the zip folder
                file_list = z.namelist()

                # Reorder file_list to parse in the sequence Indicator Metadata > Country Metadata > Indicator Data
                file_list = (
                    [file for file in file_list if 'metadata_indicator' in file.lower()]
                    +
                    [file for file in file_list if 'metadata_country' in file.lower()]
                    +
                    [file for file in file_list if 'metadata_indicator' not in file.lower() and 'metadata_country' not in file.lower()]
                )

                # Iterate through each file
                for file in file_list:

                    # Open the specific file
                    with z.open(file) as f:

                        # There are 3 types of tables in the zip folder - they all need to be treated in a different way

                        # Factor (Indicator) metadata
                        if 'metadata_indicator' in file.lower():
                            df = pd.read_csv(f)
                            logging.info(f"Loaded {file}")

                            to_ingest = pd.DataFrame(columns=['factor_id', 'factor_name'])
                            to_ingest['factor_id'] = df['INDICATOR_CODE'].values
                            to_ingest['factor_name'] = df['INDICATOR_NAME'].values
                            loaded_indicators = pd.read_sql_query("SELECT DISTINCT factor_id FROM factors", conn)['factor_id'].tolist()
                            c1 = to_ingest['factor_id'].isin(selected_indicators)
                            c2 = ~ to_ingest['factor_id'].isin(loaded_indicators)
                            to_ingest = to_ingest[c1 & c2].reset_index(drop=True)

                            # existing = pd.read_sql_query("SELECT * FROM factors", conn)
                            # to_ingest = pd.concat([existing, to_ingest], ignore_index=True)
                            # to_ingest = to_ingest.drop_duplicates().reset_index(drop=True)
                            to_ingest.to_sql('factors', conn, if_exists='append', index=False)

                        # Region (Country) metadata
                        elif 'metadata_country' in file.lower():
                            df = pd.read_csv(f)
                            logging.info(f"Loaded {file}")

                            to_ingest = pd.DataFrame(columns=['region_id', 'region_name'])
                            to_ingest['region_id'] = df['Country Code'].values
                            to_ingest['region_name'] = df['TableName'].values

                            existing = pd.read_sql_query("SELECT * FROM regions", conn)
                            to_ingest = pd.concat([existing, to_ingest], ignore_index=True)
                            to_ingest = to_ingest.drop_duplicates().reset_index(drop=True)
                            to_ingest.to_sql('regions', conn, if_exists='replace', index=False)

                        # Factor data - this needs to be first melted and then downscaled from yearly to monthly frequency
                        else:
                            count=0
                            df = pd.read_csv(f, skiprows=4)
                            logging.info(f"Loaded {file}")

                            df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()])
                            df = df.rename(columns={'Country Code' : 'region_id', 'Indicator Code' : 'factor_id'})
                            selected_indicators = pd.read_sql_query("SELECT DISTINCT factor_id FROM factors", conn)[
                                'factor_id'].tolist()
                            c = df['factor_id'].isin(selected_indicators)
                            df = df[c].reset_index(drop=True)

                            id_vars = ['region_id', 'factor_id']
                            value_vars = list(df.columns[4:])
                            var_name = 'date'
                            value_name = 'value'

                            to_ingest = df[id_vars + value_vars].set_index(id_vars).T
                            to_ingest.index = pd.to_datetime(to_ingest.index, format='%Y') + pd.offsets.YearEnd()
                            to_ingest = to_ingest.resample('ME').interpolate(method='linear')

                            c1 = to_ingest.index >= DEFAULT_START_DATE
                            c2 = to_ingest.index <= DEFAULT_END_DATE
                            to_ingest = to_ingest[c1&c2]
                            to_ingest.index = to_ingest.index.strftime("%Y-%m")
                            to_ingest = to_ingest.T.reset_index()

                            to_ingest = to_ingest.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)

                            to_ingest = to_ingest[['factor_id', 'region_id', 'date', 'value']]

                            to_ingest.to_sql('factor_data', conn, if_exists='append', index=False)

    logging.info("Macro data loaded")

def rebalance_asset_weights():
    with sqlite3.connect(f"db/{DB_NAME}") as conn:
        asset_allocation = pd.read_sql_query("SELECT * FROM asset_allocation", conn)
        if len(asset_allocation) > 0:
            asset_allocation['asset_weight'] = (
                    asset_allocation['asset_weight'] /
                    asset_allocation.groupby('portfolio_id')['asset_weight'].transform(func='sum')
            )
        asset_allocation.to_sql('asset_allocation', conn, index=False, if_exists='replace')

def update_portfolio_and_weights():

    with sqlite3.connect(f"db/{DB_NAME}") as conn:
        asset_allocation = pd.read_sql_query("SELECT * FROM asset_allocation", conn)
        assets = pd.read_sql_query("SELECT DISTINCT asset_id FROM assets", conn)
        portfolios = pd.read_sql_query("SELECT * FROM portfolios", conn)

        if len(asset_allocation) == 0:  # First time initialization -> resort to defaults
            portfolios = pd.DataFrame(
                [[DEFAULT_PORTFOLIO_ID, DEFAULT_PORTFOLIO_NAME]],
                columns=['portfolio_id', 'portfolio_name'])

            asset_allocation = pd.DataFrame(columns=['portfolio_id', 'asset_id', 'asset_weight'])
            asset_allocation['asset_id'] = assets['asset_id']
            asset_allocation['portfolio_id'] = DEFAULT_PORTFOLIO_ID
            asset_allocation['asset_weight'] = 1
        else:
            portfolios = pd.concat([portfolios, asset_allocation['portfolio_id'].to_frame()], ignore_index=True)
            portfolios = portfolios.drop_duplicates(subset='portfolio_id').reset_index(drop=True)

        portfolios.to_sql('portfolios', conn, if_exists='replace', index=False)
        asset_allocation.to_sql('asset_allocation', conn, if_exists='replace', index=False)

        rebalance_asset_weights()

def ingest_all_data():

    ingest_ticker_data()
    ingest_macroeconomic_data()
    update_portfolio_and_weights()


if __name__ == '__main__':

    os.chdir("..")
    ingest_ticker_data()
    ingest_macroeconomic_data()
    update_portfolio_and_weights()

