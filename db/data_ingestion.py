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

        for ticker in tickers:
            data = yf.download(ticker, start=start, end=end)
            data = data.resample('ME').mean()['Close']
            to_ingest = pd.DataFrame(columns=['asset_id', 'date', 'asset_price'])
            to_ingest['date'] = data.index.strftime(DATE_FORMAT)
            to_ingest['asset_price'] = data.values
            to_ingest['asset_id'] = ticker

            asset_info = pd.DataFrame(
                [[ticker, yf.Ticker(ticker).info['longName']]],
                columns=['asset_id', 'asset_name'])

            to_ingest.to_sql('asset_prices', conn, if_exists='append', index=False)
            asset_info.to_sql('assets', conn, if_exists='append', index=False)

def ingest_macroeconomic_data():

    with sqlite3.connect(f"db/{DB_NAME}") as conn:

        # Iterate through each zip file representing WorldBank indicator category (e.g. "Economy & Growth")
        for zip_file in [file for file in os.listdir('data') if file.endswith('.zip')]:

            # Open the zip file
            with zipfile.ZipFile(f"data/{zip_file}", 'r') as z:

                # Get the list of files in the zip folder
                file_list = z.namelist()

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

                            existing = pd.read_sql_query("SELECT * FROM factors", conn)
                            to_ingest = pd.concat([existing, to_ingest], ignore_index=True)
                            to_ingest = to_ingest.drop_duplicates().reset_index(drop=True)
                            to_ingest.to_sql('factors', conn, if_exists='replace', index=False)

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

                            df = pd.read_csv(f, skiprows=4)
                            logging.info(f"Loaded {file}")

                            df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()])
                            df = df.rename(columns={'Country Code' : 'region_id', 'Indicator Code' : 'factor_id'})

                            id_vars = ['region_id', 'factor_id']
                            value_vars = list(df.columns[4:])
                            var_name = 'date'
                            value_name = 'value'

                            df = df.melt(id_vars=id_vars, value_vars=value_vars, var_name=var_name, value_name=value_name)
                            df = df.dropna(subset=['value'])
                            df.index = pd.to_datetime(df['date'], format='%Y') + pd.offsets.YearEnd()
                            df = df.groupby(['region_id', 'factor_id'])['value'] \
                                .apply(lambda x: x.resample('ME').interpolate()) \
                                .reset_index()



                            to_ingest = pd.DataFrame(c)


def update_portfolio_and_weights():

    with sqlite3.connect(f"db/{DB_NAME}") as conn:
        assets = pd.read_sql_query("SELECT DISTINCT asset_id FROM assets", conn)
        portfolios = pd.DataFrame(
            [[DEFAULT_PORTFOLIO_ID, DEFAULT_PORTFOLIO_NAME]],
            columns=['portfolio_id', 'portfolio_name'])

        asset_allocation = pd.DataFrame(columns=['portfolio_id', 'asset_id', 'asset_weight'])
        asset_allocation['asset_id'] = assets['asset_id']
        asset_allocation['portfolio_id'] = DEFAULT_PORTFOLIO_ID
        asset_allocation['asset_weight'] = 1
        asset_allocation['asset_weight'] = (
                asset_allocation['asset_weight'] /
                asset_allocation.groupby('portfolio_id')['asset_weight'].transform(func='sum')
        )

        portfolios.to_sql('portfolios', conn, if_exists='replace', index=False)
        asset_allocation.to_sql('asset_allocation', conn, if_exists='replace', index=False)

def ingest_all_data():

    ingest_ticker_data()
    ingest_macroeconomic_data()
    update_portfolio_and_weights()


if __name__ == '__main__':

    os.chdir("..")
    # ingest_ticker_data()
    ingest_macroeconomic_data()
    # update_portfolio_and_weights()

