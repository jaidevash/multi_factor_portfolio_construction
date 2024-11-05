import os
import sys
import streamlit as st
import pandas as pd
import sqlite3

from common.constants import *
from db.data_ingestion import ingest_ticker_data, rebalance_asset_weights, update_portfolio_and_weights


# Retrieve and show current state of the portfolio and assets
# Make this an editable so it reads/writes from/to DB dynamically

class DashboardAssetAlloc:

    def __init__(self) -> None:
        self.db_path = f"db/{DB_NAME}"
        self.tables = {}
        self.edited_tables = {}
        self.set_page_config()
        self.expose_db()
        st.divider()

    @staticmethod
    def set_page_config() -> None:
        st.set_page_config(
            layout="wide",
            page_title="Dashboard - by Jaidev Ashok",
            page_icon=":chart_with_upwards_trend:"
        )

    def expose_db(self):

        with sqlite3.connect(self.db_path) as conn:

            st.title("Asset Allocation")
            st.write('#### Edits can be made directly to the tables below. ')
            st.divider()

            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                self.tables[table_name] = df

            cols = st.columns(3)

            with cols[0]:
                tbl = 'asset_allocation'
                st.subheader(f"Table: {tbl}")
                self.edited_tables[tbl] = st.data_editor(self.tables[tbl], num_rows='dynamic')

                # Warnings to display
                if self.edited_tables[tbl].groupby('portfolio_id')['asset_weight'].sum().ne(1).any():
                    st.warning("Portfolio weights require rebalancing!")

                assets_price_unavailable = list(
                    set(self.edited_tables[tbl]['asset_id'].dropna().values)
                    -
                    set(self.tables['asset_prices']['asset_id'].values)
                )

                if len(assets_price_unavailable) > 0:
                    st.warning(
                        f"Database needs to be updated with prices of new assets: "
                        f"{', '.join(assets_price_unavailable)}"
                    )

                tbl = 'portfolios'
                st.subheader(f"Table: {tbl}")
                self.edited_tables[tbl] = st.data_editor(self.tables[tbl], num_rows='dynamic')

                tbl = 'assets'
                st.subheader(f"Table: {tbl}")
                st.write("_(asset_id refers to trading ticker)_")
                self.edited_tables[tbl] = st.data_editor(self.tables[tbl], num_rows='dynamic')

                clicked = st.button('Update database and rebalance weights', type='primary')

                if clicked:
                    for k, df in self.edited_tables.items():
                        df.to_sql(k, conn, index=False, if_exists='replace')

                    # Ingestion of new ticker data always the first thing to do
                    ingest_ticker_data(self.edited_tables['asset_allocation']['asset_id'].values)
                    update_portfolio_and_weights()

            with cols[1]:
                self.show_corr_analysis()

    def show_corr_analysis(self):
        st.subheader('Index correlation analysis')
        st.write("_(comparison with macro variables in the next section)_")


DashboardAssetAlloc()