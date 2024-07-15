import os
import pathlib
import duckdb
import pandas as pd
import numpy as np

class CreateDB:
    """
    A class to create and manage a DuckDB database from CSV files in a specified folder.

    Attributes:
    -----------
    data_folder : str
        Path to the folder containing CSV files.
    db_path : str
        Path to the DuckDB database file.
    conn : duckdb.DuckDBPyConnection
        DuckDB connection object.
    table_name : str
        Name of the table to be created in the database.

    Methods:
    --------
    create_table():
        Creates the table in the database if it does not already exist.
    insert_data():
        Inserts data from CSV files into the table.
    run():
        Runs the process of creating the table and inserting the data.
    """

    def __init__(self, data_folder, db_path):
        """
        Initializes the CreateDB class with the specified data folder and database path.

        Parameters:
        -----------
        data_folder : str
            Path to the folder containing CSV files.
        db_path : str
            Path to the DuckDB database file.
        """
        self.data_folder = pathlib.Path(data_folder)
        self.db_path = db_path
        print(self.db_path)
        self.conn = duckdb.connect(database=str(self.db_path))
        self.table_name = 'data'

    def create_table(self):
        """
        Creates the table in the DuckDB database if it does not already exist.
        """
        query = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                DateTime TIMESTAMP,
                Open FLOAT,
                High FLOAT,
                Low FLOAT,
                Close FLOAT,
                Volume INT,
                OI INT,
                Underlying VARCHAR,
                Ticker VARCHAR,
                Expiry TIMESTAMP,
                Strike FLOAT,
                Type VARCHAR,
                Date TIMESTAMP,
                Weekday INT
            )
        """
        self.conn.execute(query)

    def insert_data(self):
        """
        Inserts data from CSV files in the specified data folder into the database table.
        """
        csv_files = list(self.data_folder.glob('*.csv'))
        if not csv_files:
            print(f"No CSV files found in {self.data_folder}")
            return

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
                df['Expiry'] = pd.to_datetime(df['Expiry'], errors='coerce')
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df[['Open', 'High', 'Low', 'Close', 'Strike']] = df[['Open', 'High', 'Low', 'Close', 'Strike']].astype(float)
                df[['Volume', 'OI', 'Weekday']] = df[['Volume', 'OI', 'Weekday']].astype(int)
                df[['Type', 'Ticker', 'Underlying']] = df[['Type', 'Ticker', 'Underlying']].astype(str)

                query = f"INSERT INTO {self.table_name} SELECT * FROM df"
                self.conn.execute(query)
                print(f"Data from {file_path} inserted successfully")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    def run(self):
        """
        Runs the process of creating the table and inserting the data into the DuckDB database.
        """
        self.create_table()
        self.insert_data()
        print("Database setup and data insertion complete")


if __name__ == '__main__':
    data_folder = 'OP_BackTest/DataDB/data_folder'
    db_path = 'OP_BackTest/DataDB/data.db'
    db = CreateDB(data_folder, db_path)
    db.run()
