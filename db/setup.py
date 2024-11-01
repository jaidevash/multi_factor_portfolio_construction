import duckdb
import pandas as pd

# Table and schema:

def create_table_init_cmd(table_name, **kwargs):
    """

    :param table_name:
    :param kwargs:
    :return:
    """

    if not len(kwargs):
        msg = f"No columns defined for table {table_name}"
        raise Exception(msg)

    text = (f)



def setup_db():

    create_table_init_cmd = (
        f"CREATE TABLE {table_name} ("
        f"{col1} {dtype1},"
        f"{col2} {dtype1},"
        f"{col1} {dtype1},"