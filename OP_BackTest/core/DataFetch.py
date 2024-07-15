import duckdb
import pandas as pd
import datetime as dt
import os

# show all columns
pd.set_option('display.max_columns', None)

class DataFetcher:
    def __init__(self,db_path=None):
        if db_path is None:
            db_path = 'data.db'
            # raise ValueError("Database path not found")
        #     print path
        # print("Database Path : ", db_path)
        self.conn = duckdb.connect(database=db_path, read_only=True)

    def _execute_query(self, query, params=[]):
        # print(query, params)
        return self.conn.execute(query, params).fetch_df()

    def get_columns(self):
        query = "SELECT * FROM data LIMIT 1"
        return self._execute_query(query).columns.tolist()

    def fetch_expirys(self, from_date='2021-01-01', to_date='2025-12-31'):
        """
        Fetch all unique expiry dates between from_date and to_date
        Args:
            from_date:
            to_date:

        Returns:

        """
        query = """
                SELECT DISTINCT Expiry
                FROM data
                WHERE CAST(Expiry AS DATE) >= ? AND CAST(Expiry AS DATE) <= ? AND Expiry IS NOT NULL
                ORDER BY Expiry
            """
        return self._execute_query(query, [from_date, to_date])

    def get_conditions(self):
        print("Data Details : Table Name : data, Column Names : ",['DateTime', 'Expiry', 'Type', 'Strike', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI', 'Underlying'])
        print("Valid keys for conditions are: ",['Expiry', 'DateTime', 'DateTime_M', 'Date', 'Date_M', 'Time', 'Time_M', 'Weekday', 'Weekday_M', 'Strike', 'Strike_M', 'Ticker', 'Ticker_M', 'FromDate', 'ToDate', 'DaysBeforeExpiry',
               'StartDaysBeforeExpiry', 'EndDaysBeforeExpiry', 'EveryDayStartTime', 'EveryDayEndTime', 'Type',
                'CloseLessThan', 'CloseGreaterThan'])

    def _validate_conditions(self, conditions):
        valid_keys = ['Expiry', 'DateTime', 'DateTime_M', 'Date', 'Date_M', 'Time', 'Time_M', 'Weekday', 'Weekday_M', 'Strike', 'Strike_M', 'Ticker', 'Ticker_M', 'FromDate', 'ToDate', 'DaysBeforeExpiry',
                      'StartDaysBeforeExpiry', 'EndDaysBeforeExpiry', 'EveryDayStartTime', 'EveryDayEndTime', 'Type', 'ClosestPrimium', 'CloseLessThan', 'CloseGreaterThan']
        if not isinstance(conditions, dict):
            raise TypeError("Input conditions must be a dictionary. Valid keys are: " + str(valid_keys))
        for key, value in conditions.items():
            if key not in valid_keys:
                raise ValueError(f"Invalid condition key: {key}. Allowed keys are: {valid_keys}")
            if key in ['DateTime', 'Expiry', 'FromDate', 'ToDate', 'Date'] and not isinstance(value, (str, dt.datetime)):
                raise TypeError(f"Invalid data type for {key}. Expected string or datetime object.")

    def fetch_options_data(self, conditions=None, resample_period='1min', order_by=None):
        if order_by is None:
            order_by = ['DateTime', 'Type', 'Open']
        self._validate_conditions(conditions)
        conditions = conditions or {'StartDaysBeforeExpiry': 6, 'EndDaysBeforeExpiry': 0, 'EveryDayStartTime': '09:15:00', 'EveryDayEndTime': '15:30:00'}

        ## Delete in next version
        if conditions.get('Ticker') == 'NIFTY':
            conditions['Ticker'] = 'NIFTY'
            conditions.pop('Expiry', None)
            conditions.pop('Type', None)
            conditions.pop('Strike', None)

        common_keys = ['DateTime', 'Expiry', 'Type', 'Strike', 'Ticker', 'FromDate', 'ToDate', 'Date', 'Time', 'Weekday', 'DaysBeforeExpiry',
                       'StartDaysBeforeExpiry', 'EndDaysBeforeExpiry', 'EveryDayStartTime', 'EveryDayEndTime', 'CloseLessThan', 'CloseGreaterThan']

        where_conditions = []
        params = []

        for key, value in conditions.items():
            if key in common_keys:
                if key in ['DateTime', 'Expiry', 'Type', 'Strike', 'Ticker']:
                    where_conditions.append(f"{key} = ?")
                elif key in ['FromDate', 'ToDate']:
                    where_conditions.append(f"DateTime {'>=' if key == 'FromDate' else '<='} ?")
                elif key in ['Date', 'Time']:
                    where_conditions.append(f"CAST(DateTime AS {key.upper()}) = ?")
                elif key == 'Weekday':
                    where_conditions.append("DATE_PART('dow', DateTime) = ?")
                elif key in ['DaysBeforeExpiry', 'StartDaysBeforeExpiry', 'EndDaysBeforeExpiry']:
                    where_conditions.append(f"DATEDIFF('day', DateTime, Expiry) {'=' if key == 'DaysBeforeExpiry' else '<=' if key == 'StartDaysBeforeExpiry' else '>='} ?")
                elif key in ['EveryDayStartTime', 'EveryDayEndTime']:
                    where_conditions.append(f"CAST(DateTime AS TIME) {'>=' if key == 'EveryDayStartTime' else '<='} ?")
                elif key in ['CloseLessThan', 'CloseGreaterThan']:
                    where_conditions.append(f"Close {'<' if key == 'CloseLessThan' else '>'} ?")
                params.append(value)

            elif key.endswith('_M'):
                if key in ['DateTime_M', 'Strike_M', 'Ticker_M']:
                    where_conditions.append(f"{key[:-2]} IN ({','.join(['?'] * len(value))})")
                    params.extend(value)
                elif key in ['Date_M', 'Time_M']:
                    where_conditions.append(f"CAST(DateTime AS {key[:-2].upper()}) IN ({','.join(['?'] * len(value))})")
                    params.extend(value)
                elif key == 'Weekday_M':
                    where_conditions.append("DATE_PART('dow', DateTime) IN ({})".format(",".join("?" * len(value))))
                    params.extend(value)

        where_clause = " AND ".join(where_conditions)

        query = f"""
                SELECT *,
                       CAST(DateTime AS DATE) AS Date, DATE_PART('dow', DateTime) AS Weekday
                FROM data
                WHERE {where_clause}
                ORDER BY {', '.join(order_by)}
            """
        options_data_results = self._execute_query(query, params)

        conditions['FromDate'] = conditions['FromDate'] if 'FromDate' in conditions else options_data_results['DateTime'].min()
        conditions['ToDate'] = conditions['ToDate'] if 'ToDate' in conditions else options_data_results['DateTime'].max()

        if not options_data_results.empty and resample_period != '1min':
            options_data_results = self.fetch_and_resample_data(options_data_results, resample_period, conditions['FromDate'], conditions['ToDate'])

        return options_data_results

    def fetch_closest_strike_premium(self, closest_premium, conditions=None):
        if conditions is None:
            conditions = {}

        where_conditions = []
        params = []

        for key, value in conditions.items():
            if key in ['DateTime', 'Expiry', 'Type', 'Strike']:
                where_conditions.append(f"{key} = ?")
                params.append(value)

        where_conditions = " AND ".join(where_conditions)
        inner_query_params = params[:]  # Copy params for the inner query
        query = f"""
            SELECT *
            FROM data
            WHERE {where_conditions} 
                AND ABS(Close - ?) = (
                    SELECT MIN(ABS(Close - ?))
                    FROM data
                    WHERE {where_conditions}
                )
            ORDER BY DateTime, Type, Open
        """
        params.extend([closest_premium, closest_premium])  # Extend with closest_premium for the outer query
        params += inner_query_params  # Add inner query params after closest_premium
        return self._execute_query(query, params)

    def fetch_and_resample_data(self, df, resample_period, FromDate=None, ToDate=None):
        # print(f"Resampling {resample_period} on data size {df.shape[0]}")
        if FromDate is None:
            FromDate = df['DateTime'].min().date()
        if ToDate is None:
            ToDate = df['DateTime'].max().date()
        query = """
                    SELECT DISTINCT DateTime
                    FROM data
                    WHERE DateTime >= ? AND DateTime <= ? AND Ticker = 'NIFTY'
                    ORDER BY DateTime
                """
        nifty_datetime = self.conn.execute(query, [FromDate, ToDate]).fetch_df()
        # print(f"Resampling {resample_period} on data size {nifty_datetime.shape[0]}")
        grouped = df.groupby('Ticker')
        processed_data = []

        for ticker, data_group in grouped:
            data_merged = nifty_datetime.merge(data_group, how='left', on='DateTime').ffill()
            resampled_data = data_merged.set_index('DateTime').resample(resample_period).agg({
                'Expiry': 'first',
                'Strike': 'first',
                'Type': 'first',
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum',
                'OI': 'last',
                'Date' : 'first',
                'Weekday' : 'first',
                'Underlying' : 'last'
            }).reset_index()
            resampled_data['Ticker'] = ticker
            processed_data.append(resampled_data)

        combined_df = pd.concat(processed_data, ignore_index=True)
        return combined_df.dropna(subset=['Close'], axis=0).reset_index(drop=True)

    def fetch_custom_data(self, query, params=[]):
        return self._execute_query(query, params)

    def is_trading_date(self, date):
    #   check wheatherr data in db Datetime.Date
        query = """
            SELECT DISTINCT CAST(DateTime AS DATE) AS Date
            FROM data
            WHERE CAST(DateTime AS DATE) = ?
        """
        return self._execute_query(query, [date]).shape[0] > 0


if __name__ == '__main__':
    db_path = 'D:\PROJECTS\ResumeProjects\BackTest\OP_BackTest\DataDB\data.db'
    data_fetcher = DataFetcher(db_path)
    conditions = {
        'EveryDayStartTime': '09:15:00',
        'EveryDayEndTime': '15:29:00',
        'FromDate': '2024-02-01 09:56:00',
        'ToDate': '2024-02-02 09:56:00',
        'StartDaysBeforeExpiry': 6,
        'EndDaysBeforeExpiry': 0,
        'Type': 'CE',
        'Ticker': 'NIFTY08FEB2422150CE'}
    # {'EveryDayStartTime': '09:15:00', 'EveryDayEndTime': '15:29:00', 'FromDate': '2024-02-01 09:56:00', 'ToDate': '2024-02-02 09:56:00', 'StartDaysBeforeExpiry': 6, 'EndDaysBeforeExpiry': 0, 'Type': 'CE', 'Ticker': 'NIFTY08FEB2422150CE'}
    print(data_fetcher.fetch_options_data(conditions, resample_period='3min'))
