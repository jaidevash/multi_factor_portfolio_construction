import os
import sys
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

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
        self.show_all()
        st.divider()

    @staticmethod
    def set_page_config() -> None:
        st.set_page_config(
            layout="wide",
            page_title="Dashboard - by Jaidev Ashok",
            page_icon=":chart_with_upwards_trend:"
        )

    def show_all(self):

        with sqlite3.connect(self.db_path) as conn:
            self.conn = conn

            st.title("Asset Allocation")
            st.write('#### Edits can be made directly to the tables below. ')
            st.divider()

            # Get a full list of tables from the DB, then read them into a dictionary (class attr)
            self.extract_all_db_tables()

            # Split the page into 2 columns
            cols = st.columns(2)

            # Column 1
            with cols[0]:
                commit_required = self.expose_db()

                # If button clicked, commit edited tables to DB
                if commit_required:
                    self.commit_edited_tables_to_db()

            # Column 2
            with cols[1]:
                self.show_portfolio_visualization()

    def extract_all_db_tables(self):

        conn = self.conn
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            self.tables[table_name] = df

    def display_warnings(self):

        # If weights in the asset_allocation table don't add up to 100% within a portfolio
        if self.edited_tables['asset_allocation'].groupby('portfolio_id')['asset_weight'].sum().ne(1).any():
            st.warning("Portfolio weights require rebalancing!")

        assets_price_unavailable = list(
            set(self.edited_tables['asset_allocation']['asset_id'].dropna().values)
            -
            set(self.tables['asset_prices']['asset_id'].values)
        )

        # If there are assets provided for which price data hasn't yet been loaded into the DB
        if len(assets_price_unavailable) > 0:
            st.warning(
                f"Database needs to be updated with prices of new assets: "
                f"{', '.join(assets_price_unavailable)}"
            )

    def expose_db(self):

        # Show asset allocation table - make it editable
        tbl = 'asset_allocation'
        st.subheader(f"Table: {tbl} (editable)")
        self.edited_tables[tbl] = st.data_editor(self.tables[tbl], num_rows='dynamic')

        # Warnings to display - e.g. if portfolio weights need rescaling
        self.display_warnings()

        # Show asset allocation table - make it editable
        tbl = 'portfolios'
        st.subheader(f"Table: {tbl} (editable)")
        self.edited_tables[tbl] = st.data_editor(self.tables[tbl], num_rows='dynamic')

        button_msg = 'Update Database and Rebalance Weights'
        button_clicked = st.button(button_msg, type='primary')

        # Add a reference table for asset tickers and names
        tbl = 'assets'
        st.subheader(f"Reference table: {tbl}")
        st.write("_(asset_id refers to trading ticker)_")
        self.edited_tables[tbl] = st.data_editor(self.tables[tbl])

        return button_clicked

    def commit_edited_tables_to_db(self):
        for k, df in self.edited_tables.items():
            df.to_sql(k, self.conn, index=False, if_exists='replace')

        # Ingestion of new ticker data is always the first thing to do
        ingest_ticker_data(self.edited_tables['asset_allocation']['asset_id'].values)

        # Update all table based on changes made mainly to asset_allocation
        update_portfolio_and_weights()

        # Refresh page
        st.rerun()

    def show_portfolio_visualization(self):
        st.subheader('Portfolio overview')

        df = self.tables['asset_allocation']
        df_dict = {k: v for k, v in df.groupby('portfolio_id')}

        for k, v in df_dict.items():
            fig = px.pie(
                v, values='asset_weight', names='asset_id',
                title=k
            )

            st.plotly_chart(fig)

        st.write("_(market trends and macro variables in the next section)_")


DashboardAssetAlloc()