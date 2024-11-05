import os
import sys
import pandas as pd
import streamlit as st
import sqlite3
import plotly.express as px

from common.constants import *

class DashboardCorrelation:

    def __init__(self) -> None:
        self.db_path = f"db/{DB_NAME}"
        self.tables = {}

        self.set_page_config()
        self.show_rolling_correlations()

    @staticmethod
    def set_page_config() -> None:
        st.set_page_config(
            layout="wide",
            page_title="Dashboard - by Jaidev Ashok",
            page_icon=":chart_with_upwards_trend:"
        )

    def show_rolling_correlations(self):

        st.title("Correlation Analysis")

        with sqlite3.connect(self.db_path) as conn:

            pf_ids = pd.read_sql_query("SELECT DISTINCT portfolio_id FROM portfolios", conn)
            pf_ids = pf_ids.iloc[:, 0].values

            cols = st.columns(4)

            with cols[0]:
                pf_id = st.selectbox("Select portfolio whose returns you wish to analyze", pf_ids)

            cols = st.columns(2)

            with cols[0]:
                assets_tbl =  pd.read_sql_query((
                    f"SELECT asset_allocation.asset_id, asset_allocation.asset_weight, asset_prices.date, asset_prices.asset_price "
                    f"FROM asset_allocation JOIN asset_prices ON asset_allocation.asset_id = asset_prices.asset_id "
                    f"WHERE asset_allocation.portfolio_id = '{pf_id}'"
                ), conn)

                # st.dataframe(assets_tbl)
                #
                fig = px.line(assets_tbl, x='date', y='asset_price', color='asset_id', title='Index Price Trends',
                    # color_discrete_sequence='yellow'
                )
                fig.show()

            # asset_prices =

DashboardCorrelation()