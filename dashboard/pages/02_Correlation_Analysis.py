import os
import sys
import numpy as np
import pandas as pd
import streamlit as st
import sqlite3
import plotly.express as px

from common.constants import *
from calculations.calc_portfolio import calc_portfolio_price, calc_portfolio_returns

class DashboardCorrelation:

    def __init__(self) -> None:
        self.db_path = f"db/{DB_NAME}"
        self.tables = {}
        self.pf_id_selected = None

        self.set_page_config()
        self.show_all()

    @staticmethod
    def set_page_config() -> None:
        st.set_page_config(
            layout="wide",
            page_title="Dashboard - by Jaidev Ashok",
            page_icon=":chart_with_upwards_trend:"
        )

    def show_all(self):

        st.title("Correlation Analysis")
        st.write('#### Select a portfolio, then flip through the tabs for analyses. ')

        with sqlite3.connect(self.db_path) as conn:
            self.conn = conn
            self.add_portfolio_dropdown()

            # Spit dashboard page into tabs
            tabs = st.tabs(['Market Trends', 'Macro-economic Indicators'])

            with tabs[0]:
                self.show_market_trends()



    def add_portfolio_dropdown(self):

        conn = self.conn
        pf_ids = pd.read_sql_query("SELECT DISTINCT portfolio_id FROM portfolios", conn)
        pf_ids = pf_ids.iloc[:, 0].values

        cols = st.columns(4)  # This is only to control dropdown size
        with cols[0]:
            self.pf_id_selected = st.selectbox("Pick the portfolio whose returns are to be analyzed", pf_ids)

    def show_market_trends(self):

        conn = self.conn

        assets_tbl = pd.read_sql_query((
            f"SELECT asset_allocation.portfolio_id, asset_allocation.asset_id, asset_allocation.asset_weight, asset_prices.date, asset_prices.asset_price "
            f"FROM asset_allocation JOIN asset_prices ON asset_allocation.asset_id = asset_prices.asset_id "
            f"WHERE asset_allocation.portfolio_id = '{self.pf_id_selected}'"
        ), conn)

        # Chart 1
        fig = px.line(
            assets_tbl, x='date', y='asset_price',
            color='asset_id',
            title='Individual Index Price Trends (log scale; non-homogeneous currencies)',
            # color_discrete_sequence='yellow',
            log_y=True,
        )
        st.plotly_chart(fig)

        # Table to support chart 1
        assets_tbl_pivot = assets_tbl.pivot(index='date', columns='asset_id', values='asset_price').reset_index()
        st.dataframe(assets_tbl_pivot)

        # Calcs to support chart 2
        assets_tbl = calc_portfolio_price(assets_tbl)
        pf_tbl = calc_portfolio_returns(assets_tbl)

        # Chart 2
        fig = px.line(
            pf_tbl, x='date', y='price',
            title='Portfolio Price Trends (log scale)',
            # color_discrete_sequence='yellow',
            log_y=True,
        )
        st.plotly_chart(fig)
        st.caption('Price is weight-averaged based on weights provided')

        # Chart 3
        fig = px.line(
            pf_tbl, x='date', y='log_return',
            title='Portfolio Log Returns (period-over-period)',
            # color_discrete_sequence='yellow',
            # log_y=True,
        )
        st.plotly_chart(fig)

        # Table to support charts 2 and 3
        st.dataframe(pf_tbl)



DashboardCorrelation()