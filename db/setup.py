import os
import sqlite3
import json
import logging
from typing import Dict, Any
logging.basicConfig(
    # filename='app.log', # Log to this file
    level=logging.INFO, # Set the logging level format
    format='%(asctime)s %(name)s [%(levelname)s]: %(message)s'
)

from common.constants import *

class DataBase:

    def __init__(self, db_name: str = None) -> None:
        """
        Creates a new database (file name: db_name) using the schema provided in
        ./config/database_schema.json

        In case this file name is already present, deletes the file
        and re-creates it from scratch.

        :param db_name: File name of the database to initialize
        """
        self.db_name = DB_NAME if db_name is None else db_name
        self.db_schema_path = 'config/database_schema.json'
        self.db_schema = None

        if os.path.isfile(f"db/{self.db_name}"):
            os.remove(f"db/{self.db_name}")
        sqlite3.connect(f"db/{self.db_name}").close()

        self.set_up_tables()

    def load_schema(self) -> None:
        """

        :return:
        """

        with open(self.db_schema_path, 'r') as file:
            self.db_schema = json.load(file)

    def set_up_tables(self) -> None:
        """

        :return:
        """

        self.load_schema()

        with sqlite3.connect(f"db/{self.db_name}") as conn:

            cursor = conn.cursor()

            for table, schema in self.db_schema.items():
                sql_cmd = self.create_sql_cmd(table, schema)
                logging.info(sql_cmd)
                cursor.execute(sql_cmd)

            conn.commit()

    @staticmethod
    def create_sql_cmd(table, schema):
        """
        Creates a

        :param table:
        :param schema:
        :return: String representation of SQL command
        """

        result = f"CREATE TABLE {table}"

        primary_key = schema.get('primary_key', None)
        if primary_key is not None and len(primary_key) == 0: primary_key = None

        n = len(schema['columns'])
        if n:
            result = f"{result} ("

            for i, (column, column_info) in enumerate(schema['columns'].items()):
                dtype = column_info.get('datatype', 'BLOB')
                nullable = column_info.get('nullable', True)
                unique = column_info.get('unique', False)

                col_cmd = (
                    f"{column} {dtype}"
                    f"{' NOT NULL' if not nullable else ''}"
                    f"{' UNIQUE' if unique else ''}"
                )

                result = f"{result}{col_cmd}"

                if i < n-1:
                    result = f"{result}, "

            if primary_key is not None:
                result = f"{result}, PRIMARY KEY ({', '.join(primary_key)})"

            result = f"{result})"

        return result

if __name__ == '__main__':

    os.chdir("..")
    # db_name = input(f'Initializing a database from scratch. Provide a name (if left blank: {DB_NAME}): ')
    # if db_name == '': db_name = DB_NAME
    test_db = DataBase(db_name=DB_NAME)
