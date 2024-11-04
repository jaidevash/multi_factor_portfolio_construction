import os
import sys
import streamlit as st
from datetime import datetime as dt

# Add root project folder to sys.path if needed, and make it the working directory
PROJ_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ_PATH not in sys.path: sys.path.append(PROJ_PATH)
os.chdir(PROJ_PATH)

from common.constants import *
from db.setup import DataBase

class DashboardHome:

    def __init__(self) -> None:
        self.db_path = f"db/{DB_NAME}"
        self.set_page_config()
        self.show_header()

    # Dashboard elements begin here

    @staticmethod
    def set_page_config() -> None:
        st.set_page_config(
            layout="wide",
            page_title="Dashboard - by Jaidev Ashok",
            page_icon=":chart_with_upwards_trend:"
        )

    def if_db_exists(self) -> bool:
        return os.path.isfile(self.db_path)

    def show_header(self) -> None:
        st.title('Portfolio Evaluation Tool')
        if self.if_db_exists():
            st.write(
                f"#### You have a database available "
                f"(last updated: {dt.fromtimestamp(os.path.getmtime(self.db_path)).strftime('%Y/%m/%d at %H:%M:%S')}). "
                f"To begin, select a section from the sidebar on the left."
            )
            st.divider()
            st.write('*(alternatively, you can start creating your database again from scratch)*')
            st.button("Re-create database", type='secondary', on_click=DataBase)
        else:
            st.write("#### Seems like you don't have a database yet. Click the button below to set it up.")
            st.button("Set up database", type='primary', on_click=DataBase)
        st.divider()




DashboardHome()