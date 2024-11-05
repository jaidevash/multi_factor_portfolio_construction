import os
import sys
import numpy as np
import pandas as pd
import streamlit as st
import sqlite3
import plotly.express as px
from datetime import datetime as dt

from common.constants import *
from calculations.calc_portfolio import calc_portfolio_price, calc_portfolio_returns
from calculations.calc_correlations import calc_primary_coefficients

class DashboardAnalysis:

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

        st.title("Analysis")
        st.write('#### Select a portfolio, then flip through the tabs for analyses. ')

        with sqlite3.connect(self.db_path) as conn:
            self.conn = conn
            self.add_portfolio_dropdown()

            # Spit dashboard page into tabs
            tabs = st.tabs(['Market Trends', 'Macro-economic Indicators', 'Return attribution'])

            with tabs[0]:
                self.show_market_trends()

            with tabs[1]:
                self.show_macro_indicators()

            with tabs[2]:
                self.show_return_attribution()

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
        self.assets_tbl = calc_portfolio_price(assets_tbl)
        self.pf_tbl = calc_portfolio_returns(self.assets_tbl)

        # Chart 2
        # fig = px.line(
        #     pf_tbl, x='date', y='price',
        #     title='Portfolio Price Trends (log scale)',
        #     # color_discrete_sequence='yellow',
        #     log_y=True,
        # )
        # st.plotly_chart(fig)

        # Chart 3
        fig = px.line(
            self.pf_tbl, x='date', y='log_return',
            title='Portfolio Log Returns (period-over-period)',
            # color_discrete_sequence='yellow',
            # log_y=True,
        )
        st.plotly_chart(fig)
        st.caption('Asset returns are weight-averaged at each time period based on weights provided (see below)')

        # Table to support charts 2 and 3
        st.dataframe(self.assets_tbl)
        st.dataframe(self.pf_tbl)

    def show_macro_indicators(self):

        conn = self.conn

        factor_names = pd.read_sql_query("SELECT DISTINCT factor_name FROM factors", conn).iloc[:, 0].values
        region_names = pd.read_sql_query("SELECT DISTINCT region_name FROM regions", conn).iloc[:, 0].values

        cols = st.columns(2) 
        with cols[0]:
            self.factor_selected = st.selectbox("Pick the macroeconomic indicator against which correlations are to be computed", factor_names)
        with cols[1]:
            self.region_selected = st.selectbox("Select a region corresponding to the macroeconomic indicator", region_names)

        macro_data = pd.read_sql_query((
            f"SELECT factor_data.factor_id, factors.factor_name, factor_data.region_id, regions.region_name, factor_data.date, factor_data.value "
            f"FROM factor_data "
            f"INNER JOIN factors ON factor_data.factor_id = factors.factor_id "
            f"INNER JOIN regions ON factor_data.region_id = regions.region_id "
            f"WHERE factors.factor_name = '{self.factor_selected}'; "
        ), conn)

        c = macro_data['region_name'] == self.region_selected
        macro_data = macro_data[c].reset_index(drop=True)

        with st.expander('Preview of macroeconomic data'):
            st.dataframe(macro_data.head(10))

        cols = st.columns(2)
        with cols[0]:
            window = st.slider('Select rolling window (number of months)', min_value=1, max_value=60, value=6)

        data1 = self.pf_tbl['pct_return'].rolling(window)
        data2 = macro_data['value'].pct_change()
        # data2 = np.log(macro_data['value'] / macro_data['value'].shift(1))

        corr = data1.corr(data2)
        corr.index = self.pf_tbl['date']

        st.write(f"#### Rolling window correlation between portfolio returns and selected macroeconomic indicator")
        fig = px.line(corr)
        fig.update_layout(yaxis_range = [-1,1])
        st.plotly_chart(fig)
        st.write(f"**Average correlation:** {corr.mean().round(2)}")
        st.write(f"**Variability (stdev) of correlation:** {corr.std().round(2)}")
        st.caption('A pct change correlation is used instead of log to reduce instances of division by zero errors')

    def show_return_attribution(self):

        conn = self.conn

        st.write('Return attributions are computationally expensive to compute all together for all possible time windows. ')
        st.write('We use an L2 regularization approach to identify most contributing factors in a given window, using specific start and end date inputs at a time. ')

        cols = st.columns(2)
        with cols[0]:
            start = st.date_input('Start Date', min_value=DEFAULT_START_DATE_DT, max_value=DEFAULT_END_DATE_DT,
                value=DEFAULT_RET_ATTR_START_DATE_DT)
        with cols[1]:
            end = st.date_input('End Date', min_value=DEFAULT_START_DATE_DT, max_value=DEFAULT_END_DATE_DT,
                value=DEFAULT_RET_ATTR_END_DATE_DT)

        macro_data = pd.read_sql_query((
            f"SELECT factors.factor_name, regions.region_name, factor_data.date, factor_data.value "
            f"FROM factor_data "
            f"INNER JOIN factors ON factor_data.factor_id = factors.factor_id "
            f"INNER JOIN regions ON factor_data.region_id = regions.region_id "
        ), conn)

        macro_data['key'] = macro_data['factor_name'] + '|' + macro_data['region_name']
        macro_dt = pd.to_datetime(macro_data['date'], format=DATE_FORMAT).dt.date
        c1 = macro_dt >= start
        c2 = macro_dt <= end
        macro_data = macro_data[c1 & c2].reset_index(drop=True)

        pf_dt = pd.to_datetime(self.pf_tbl['date'], format=DATE_FORMAT).dt.date
        c1 = pf_dt >= start
        c2 = pf_dt <= end

        # Preprocess the predictor and target variables
        y = self.pf_tbl[c1 & c2]['pct_return'].reset_index(drop=True)
        X = macro_data.pivot(index='date', columns='key', values='value').reset_index(drop=True).pct_change()
        X = X.dropna(how='all', axis=1)
        Xy = pd.concat([X, y], axis=1)
        Xy = Xy.dropna(subset='pct_return').reset_index(drop=True)
        Xy = Xy.bfill(axis=0).ffill(axis=0)
        Xy = Xy.replace({np.inf: 999, -np.inf:-999})

        y = Xy.iloc[:,-1]
        X = Xy.iloc[:,:-1]

        st.write('Predictor variables sample input: ')
        st.write(X.iloc[:5, 50:55])
        st.write('Target variable sample input: ')
        st.write(y.iloc[:5])

        coefficients = calc_primary_coefficients(X, y)

        st.divider()

        pos = coefficients[coefficients['Coefficient'].ge(0)].sort_values(by='Coefficient', ascending=False).reset_index(drop=True)
        neg = coefficients[coefficients['Coefficient'].lt(0)].sort_values(by='Coefficient', ascending=True).reset_index(drop=True)

        st.write(f"#### Outcome: Key contributing factors (in order from highest to lowest influence on portfolio return) ")

        cols = st.columns(2)

        with cols[0]:
            st.write('Positively influencing factors: ')
            st.dataframe(pos)

        with cols[1]:
            st.write('Negatively influencing factors: ')
            st.dataframe(neg)





DashboardAnalysis()