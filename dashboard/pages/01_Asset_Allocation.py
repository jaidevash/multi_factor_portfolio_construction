import os
import sys
import streamlit as st
import pandas as pd
import sqlite3

from common.constants import *

# Dashboard elements begin here
st.set_page_config(
    layout="wide",
    page_title="Dashboard - by Jaidev Ashok",
    page_icon=":chart_with_upwards_trend:"
)

# Retrieve and show current state of the portfolio and assets
# Make this an editable so it reads/writes from/to DB dynamically


if False:
    st.header('sys')
    for p in sys.path:
        st.text(p)
    st.divider()

    st.header('os')
    st.text(os.getcwd())
    st.divider()