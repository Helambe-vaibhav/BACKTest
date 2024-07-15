from OP_BackTest.core.Engine import Engine
from Indicators.Alma import ALMAIndicator

parameter = {
    'TimeFrame': 3,
    'EntryTime': '09:21:00',
    'ExitTime': '15:20:00',
    'EntryType': 'Close',
    'ExpiryEntryDate': 7,
    'ExpiryExitDate': 1,
    'FromDate': '2024-02-01',
    'ToDate': '2024-02-01',
    'ExpiryType': 'WEEKLY',
    'Indicator_data': {
        'ALMA280': [ALMAIndicator, ['Close'], [{'window': 5}], ['alma']]
    },
    'Legs': [
        {
            'LegName': 'LegCE',
            'Index': 'NIFTY',
            'Segment': 'OPT',
            'Spot': 'Index',
            'OptionType': 'CE',
            'StrikePrice': {'greaterthan': 140},
            'ActionType': 'BUY',
            'TotalLot': 50,
            'Target': {'Points': 10},
            'Stoploss': {'Points': 10},
            'EntryConditions': ['( ALMA280 > High )'],
            'ExitConditions': ['( ALMA280 < Low )'],
            'TotalTradesPerDay': 10,
        },
        {
            'LegName': 'LegPE',
            'Index': 'NIFTY',
            'Segment': 'OPT',
            'Spot': 'Index',
            'OptionType': 'PE',
            'StrikePrice': {'greaterthan': 140},
            'ActionType': 'BUY',
            'TotalLot': 50,
            'Target': {'Points': 10},
            'Stoploss': {'Points': 10},
            'EntryConditions': ['( ALMA280 > High )'],
            'ExitConditions': ['( ALMA280 < Low )'],
        }
    ]
}

E = Engine(Strategy_parameters=parameter,db_path='OP_BackTest/DataDB/data.db',log_path='OP_BackTest/Logs/')
tradeBook = E.run()
print(tradeBook)