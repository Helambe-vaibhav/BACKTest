import os
import pandas as pd
import numpy as np
import duckdb
from abc import ABCMeta, abstractmethod
import pandas as pd
import re
import numpy as np
import datetime as dt
import warnings
warnings.filterwarnings("ignore")
from OP_BackTest.core import DataFetcher
from threading import Thread
from queue import Queue
from OP_BackTest.utlis import log_handler

class Engine:
    def __init__(self, Strategy_parameters,db_path=None,log_path=None):
        self.Strategy_parameters = Strategy_parameters
        self.db_path = '../DataDB/data.db' if db_path is None else db_path

        log_path = "Engine.log" if log_path is None else log_path + "Engine.log"
        loggerC = log_handler.ThreadSafeLogger("Engine", log_path)
        self.logger = loggerC.get_logger()

        self.unpack_parameters()
        self.unpack_legs()
        self.max_window_cal()


    def unpack_parameters(self):
        for key, default_value in {
            'TimeFrame': 1,
            'EntryTime': '09:15:00',
            'ExitTime': '15:29:00',
            'EntryType': 'Close',
            'ExpiryEntryDate': 6,
            'ExpiryExitDate': 0,
            'FromDate': '2024-02-02',
            'ToDate': '2024-02-14',
            'ExpiryType': 'WEEKLY',
            'Indicator_data': {},
            'Legs': []
        }.items():
            setattr(self, key, self.Strategy_parameters.get(key, default_value))
        self.logger.info('Parameters Unlocked')

    def unpack_legs(self):
        self.legs = []
        for leg in self.Legs:
            leg_parameters = {
                'LegName': leg.get('LegName', 'Leg'),
                'Index': leg.get('Index', 'NIFTY'),
                'Segment': leg.get('Segment', 'OPT'),
                'Spot': leg.get('Spot', 'Index'),
                'OptionType': leg.get('OptionType', 'CE'),
                'StrikePrice': leg.get('StrikePrice', {'ClosestPremium': {'closet': 100}}),
                'ActionType': leg.get('ActionType', 'BUY'),
                'TotalLot': leg.get('TotalLot', 1),
                'Target': leg.get('Target', {'Points': 10}),
                'Stoploss': leg.get('Stoploss', {'Points': 10}),
                'EntryConditions': leg.get('EntryConditions', []),
                'ExitConditions': leg.get('ExitConditions', []),
            }
            self.legs.append(leg_parameters)
        self.logger.info('Legs Unlocked')

    def include_indicators(self, data):
        for indicator_name, indicator_params in self.Indicator_data.items():
            indicator_function = indicator_params[0]
            indicator_columns = indicator_params[1]
            indicator_params_list = indicator_params[2]
            methods = indicator_params[3]

            for params in indicator_params_list:
                # print(indicator_name,indicator_function)
                indicator_instance = indicator_function(*[data[col] for col in indicator_columns], **params)
                for method_name in methods:
                    data[f'{indicator_name}'] = round(getattr(indicator_instance, method_name)(), 3)
        return data

    def data_fetch_para(self):
        self.logger.info('Data Fetch Parameters Created')
        return {
            'EveryDayStartTime': self.EntryTime,
            'EveryDayEndTime': self.ExitTime,
            'FromDate': self.FromDate,
            'ToDate': str(pd.to_datetime(self.ToDate) + pd.Timedelta(days=1)),
            'StartDaysBeforeExpiry': self.ExpiryEntryDate,
            'EndDaysBeforeExpiry': self.ExpiryExitDate,
        }



    def leg_excution(self, leg):
        Data = DataFetcher(db_path=self.db_path)
        legTradeBook = pd.DataFrame(columns=['EntryTime', 'Action', 'Ticker', 'EntryPrice', 'Target', 'Stoploss', 'ExitTime', 'ExitPrice', 'ExitReason', 'TotalLot'])

        data_fetch_para_par = self.data_fetch_para()
        data_fetch_para_par['Type'] = leg['OptionType']

        current_trade_entry_date = pd.to_datetime(f'{self.FromDate} {self.EntryTime}')
        last_trade_exit_date = pd.to_datetime(f'{self.ToDate} {self.ExitTime}')

        while current_trade_entry_date < last_trade_exit_date:
            current_trade_entry_date = self.adjust_for_next_trade(Data, current_trade_entry_date)
            print(current_trade_entry_date)
            data_fetch_para = data_fetch_para_par.copy()
            data_fetch_para['DateTime'] = current_trade_entry_date
            option_data = Data.fetch_options_data(data_fetch_para)
            if option_data.empty:
                continue

            strike_price = self.get_strkePrice(leg['StrikePrice'], option_data)
            start_time, end_time = self.calculate_time(end_time=current_trade_entry_date)
            strike_data = self.fetch_and_prepare_strike_data(Data, start_time, strike_price['Ticker'])

            if strike_data.empty or strike_data.shape[0] < self.max_window:
                continue

            strike_data_pre = strike_data[strike_data['DateTime'] <= current_trade_entry_date]
            strike_data_post = strike_data[strike_data['DateTime'] > current_trade_entry_date]

            if strike_data_post.empty or not self.check_conditions(strike_data_pre, leg['EntryConditions'], entry=True):
                continue

            trade_entry = self.prepare_trade_entry(leg, strike_data_pre, current_trade_entry_date)
            trade_exit = self.determine_trade_exit(leg, trade_entry, strike_data_post)
            legTradeBook.loc[len(legTradeBook)] = {**trade_entry, **trade_exit}

            current_trade_entry_date = trade_exit['ExitTime']

        legTradeBook['LegName'] = leg['LegName']
        legTradeBook['Action'] = leg['ActionType']
        return legTradeBook

    def fetch_and_prepare_strike_data(self, Data, start_time, ticker):
        data_fetch_para = {
            'FromDate': start_time,
            'Ticker': ticker,
        }
        strike_data = Data.fetch_options_data(data_fetch_para, resample_period=f'{self.TimeFrame}min')
        return self.include_indicators(strike_data)

    def prepare_trade_entry(self, leg, strike_data_pre, current_trade_entry_date):
        entry_price = strike_data_pre['Close'].iloc[-1]
        target = entry_price + leg['Target']['Points'] if leg['ActionType'] == 'BUY' else entry_price - leg['Target']['Points']
        stoploss = entry_price - leg['Stoploss']['Points'] if leg['ActionType'] == 'BUY' else entry_price + leg['Stoploss']['Points']
        return {
            'Ticker': strike_data_pre['Ticker'].iloc[-1],
            'EntryTime': current_trade_entry_date,
            'EntryPrice': entry_price,
            'Target': target,
            'Stoploss': stoploss,
            'TotalLot': leg['TotalLot']
        }

    def determine_trade_exit(self, leg, trade_entry, strike_data_post):
        strike_data_post['Signal'] = self.check_conditions(strike_data_post, leg['ExitConditions'])
        if leg['ActionType'] == 'BUY':
            strike_data_post['TargetSignal'] = strike_data_post['High'] >= trade_entry['Target']
            strike_data_post['StoplossSignal'] = strike_data_post['Low'] <= trade_entry['Stoploss']
        else:
            strike_data_post['TargetSignal'] = strike_data_post['Low'] <= trade_entry['Target']
            strike_data_post['StoplossSignal'] = strike_data_post['High'] >= trade_entry['Stoploss']

        strike_data_post['DayEnd'] = strike_data_post['DateTime'].dt.time == pd.to_datetime(self.ExitTime).time()

        strike_data_post['ExitReason'] = np.where(strike_data_post['StoplossSignal'], 'Stoploss',
                                                  np.where(strike_data_post['TargetSignal'], 'Target',
                                                           np.where(strike_data_post['Signal'], 'ExitCondition',
                                                                    np.where(strike_data_post['DayEnd'], 'DayEnd', None))))

        exit_row = strike_data_post.dropna(subset=['ExitReason']).iloc[0]
        exit_price = self.get_exit_price(exit_row, trade_entry)
        return {'ExitTime': exit_row['DateTime'], 'ExitPrice': exit_price, 'ExitReason': exit_row['ExitReason']}

    def get_exit_price(self, exit_row, trade_entry):
        if exit_row['ExitReason'] == 'ExitCondition':
            return exit_row['Close']
        elif exit_row['ExitReason'] == 'Target':
            return trade_entry['Target']
        elif exit_row['ExitReason'] == 'Stoploss':
            return trade_entry['Stoploss']
        elif exit_row['ExitReason'] == 'DayEnd':
            return exit_row['Close']

    def calculate_time(self, end_time=None):
        end_time = pd.to_datetime(end_time)
        days = self.max_window // (375 // self.TimeFrame)
        start_time = end_time - pd.Timedelta(days=days + 1)
        return start_time,end_time


    def adjust_for_next_trade(self, Data, exit_time):
        next_entry_time = exit_time + pd.Timedelta(minutes=self.TimeFrame)
        if next_entry_time.time() >= pd.to_datetime(self.ExitTime).time():
            while True:
                next_entry_time = next_entry_time + pd.Timedelta(days=1)
                if Data.is_trading_date(next_entry_time.date()):
                    break
            next_entry_time = pd.to_datetime(f'{next_entry_time.date()} {self.EntryTime}')
        return next_entry_time

    def check_conditions(self, df, conditions,entry = False):

        # Transform each condition using transform_condition
        transformed_conditions = [self.transform_condition(cond, df) for cond in conditions]
        # Evaluate all transformed conditions using pandas.eval with local_dict
        evaluated_conditions = [pd.eval(cond, local_dict={'df': df}, engine='python') for cond in transformed_conditions]

        # Combine all conditions using '&' operator to get the final signal
        final_signal = evaluated_conditions[0]
        for cond in evaluated_conditions[1:]:
            final_signal |= cond

        if entry:
            # Return the signal for the last row
            return final_signal.iloc[-1]
        else:
            return final_signal

    def transform_condition(self, condition, df):
        # Mapping logical operators to pandas equivalents
        logical_operators = {
            ' and ': ' & ',
            ' or ': ' | ',
            ' not ': ' ~'
        }

        transformed_condition = condition
        # Replace logical operators in the condition
        for operator, replacement in logical_operators.items():
            transformed_condition = transformed_condition.replace(operator, replacement)

        # Create a regex pattern to match column names and optional suffixes
        pattern = re.compile(r'\b(' + '|'.join(df.columns) + r')(_\d+)?\b')

        # Function to replace matched column names with df references
        def replace_column(match):
            col = match.group(1)
            suffix = match.group(2)
            if suffix:
                period = int(suffix[1:])
                return f"df['{col}'].shift({period})"
            else:
                return f"df['{col}']"

        # Replace column names in the condition with their corresponding df references
        transformed_condition = pattern.sub(replace_column, transformed_condition)

        return transformed_condition


    def calculate_time(self, end_time=None):
        end_time = pd.to_datetime(end_time)
        days = self.max_window // (375 // self.TimeFrame)
        start_time = end_time - pd.Timedelta(days=days + 1)
        return start_time,end_time

    def max_window_cal(self):
        self.max_window = 0
        for indicator_params in self.Indicator_data.values():
            indicator_params_list = indicator_params[2]
            for params in indicator_params_list:
                if 'window' in params:
                    self.max_window = max(self.max_window, params['window'])

    def get_strkePrice(self,condition,df):
        if 'lessthan' in condition:
            return df[df[self.EntryType] < condition['lessthan']].iloc[-1]
        elif 'greaterthan' in condition:
            return df[df[self.EntryType] > condition['greaterthan']].iloc[0]

    def calculate_profit(self,TradeBook):
        if TradeBook.empty:
            return TradeBook
        TradeBook.sort_values(by='ExitTime',inplace=True)
        TradeBook['Profit'] = np.where(TradeBook['Action'] == 'BUY', (TradeBook['ExitPrice'] - TradeBook['EntryPrice']) * TradeBook['TotalLot'], (TradeBook['EntryPrice'] - TradeBook['ExitPrice']) * TradeBook['TotalLot'])
        TradeBook['CumulativeProfit'] = TradeBook['Profit'].cumsum()
        TradeBook['Drawdown'] = TradeBook['CumulativeProfit'] - TradeBook['CumulativeProfit'].cummax()
        return TradeBook

    def run(self):
        self.logger.info('Engine Run Started')
        # Queue for collecting results from threads
        result_queue = Queue()

        # Function to execute leg execution and collect result
        def execute_leg_and_collect_result(leg):
            legTradeBook = self.leg_excution(leg)
            result_queue.put(legTradeBook)

        # List to keep track of threads
        threads = []

        # Start a thread for each leg
        for leg in self.legs:
            # execute_leg_and_collect_result(leg)
            thread = Thread(target=execute_leg_and_collect_result, args=(leg,))
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results from queue
        AllTradeBook = pd.DataFrame()
        while not result_queue.empty():
            legTradeBook = result_queue.get()
            AllTradeBook = pd.concat([AllTradeBook, legTradeBook])

        # Calculate profit
        AllTradeBook = self.calculate_profit(AllTradeBook)
        self.logger.info('Engine Run Completed')
        return AllTradeBook