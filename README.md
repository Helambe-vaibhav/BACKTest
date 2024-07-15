# Options Algo Trading Strategy Backtest Engine

This project is a backtest engine designed for options trading strategies, focusing on algorithmic backtesting. It supports various indicators and customizable trading conditions, enabling users to validate their strategies using historical data.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
    - [Step 1: Create the Database](#step-1-create-the-database)
    - [Step 2: Configure and Run the Backtest](#step-2-configure-and-run-the-backtest)
 
## Introduction

The Options Algo Trading Strategy Backtest Engine assists traders in backtesting options trading strategies. It allows for extensive customization of indicators, entry/exit conditions, and strategy parameters.

## Features

- **Custom Indicators:** Supports custom indicators such as ALMA.
- **Configurable Conditions:** Define entry and exit conditions tailored to your strategy.
- **Multi-leg Strategies:** Handles strategies with multiple legs for complex options trading.
- **Detailed Trade Book:** Provides comprehensive output of trades for analysis.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/Helambe-vaibhav/BackTest.git
    cd BackTest
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Configure the backtest engine using parameters to customize your trading environment. Below are key parameters and their descriptions:

### Time Frame

- **TimeFrame:** Time frame for the strategy in minutes (e.g., 1, 3, 5, 15, 30, 60).

### Trading Time

- **EntryTime:** Time to enter trades (e.g., 09:30:00, 10:00:00).
- **ExitTime:** Time to exit trades (e.g., 15:30:00, 16:00:00).

### Entry and Exit Types

- **EntryType:** Basis for entry (e.g., Open, Close).
- **ExpiryEntryDate:** Days before expiry to start the trade (e.g., 7, 6, 5).
- **ExpiryExitDate:** Days before expiry to end the trade (e.g., 7, 6, 5, 0).

### Date Range

- **FromDate:** Start date for backtest (e.g., 2024-02-01).
- **ToDate:** End date for backtest (e.g., 2024-02-10).

### Expiry Type

- **ExpiryType:** Type of expiry (e.g., WEEKLY).

### Indicators

- **Indicator_data:** Indicators to be used in the strategy (e.g., ALMA).
- **Indicator_parameters:**
    - **Indicator name:** Custom name for the indicator (e.g., ALMA280).
    - **Indicator Function:** Class name of the indicator (e.g., ALMAIndicator).
    - **Indicator Inputs:** Inputs to the indicator function (e.g., ['Close', 'Open', 'High', 'Low', 'Volume']).
    - **Indicator Parameters:** Parameters to the indicator function (e.g., {'window': 9, 'offset': 0.85}).
    - **Indicator Output:** Function to get the output of the indicator (e.g., alma).

### Strategy Legs
Define legs for your strategy, each with specific parameters like option type, strike price conditions, actions, targets, and conditions for entry and exit.

- `Legs`: The legs of the strategy.
    - Example: `2`
- `Leg1`:
    - `LegName`: Name of the leg.
        - Example: `LongCall`
    - `Index`: Index of the leg.
        - Example: `NIFTY`
    - `Segment`: Segment of the leg.
        - Example: `OPT`
    - `Spot`: Spot price category of the leg.
        - Example: `Index`
    - `OptionType`: Type of the option.
        - Example: `CE`, `PE`
    - `StrikePrice`: Conditions for selecting the strike price.
        - `lessthan`: Options with a strike price less than Value.
        - `greaterthan`: Options with a strike price greater than Value.
    - `ActionType`: Action to take.
        - Example: `BUY`, `SELL`
    - `TotalLot`: Number of quantities to trade.
        - Example: `50`
    - `Target`: Target profit for the leg.
        - `Points`: Points to be considered for the target.
            - Example: `10`
    - `Stoploss`: Stop loss for the leg.
        - `Points`: Points to be considered for the stop loss.
            - Example: `10`
    - `EntryConditions`: Conditions for entering the leg.
        - Example: `['ALMA280 > High']`
    - `ExitConditions`: Conditions for exiting the leg.
        - Example: `['ALMA280 < Low']`
    - `Possible Variables for Entry and Exit Conditions`:
      - `ALMA280`: Indicator name created in `Indicator_data`.
      - `High`: High price of the leg.
      - `Low`: Low price of the leg.
      - `Close`: Close price of the leg.
      - `Open`: Open price of the leg.

## Usage

To use the Options Algo Trading Strategy Backtest Engine, follow these steps to configure and run your backtest:

### Step 1: Create the Database

Before running the backtest, you need to create the database where your historical data will be stored.

1. **Import the Required Modules:**

   Begin by importing the necessary modules to create the database.

    ```python
    from OP_BackTest.core import CreateDB
    from pathlib import Path
    ```

2. **Define the Paths and Create the Database:**

   Set up the paths for the data folder and the database, and then create the database using the `CreateDB` class.

    ```python
    if __name__ == '__main__':
        root_path = Path(__file__).parent
        print(root_path)
        data_folder = 'data_folder'
        data_folder = root_path / data_folder
        db_path = 'OP_BackTest/DataDB/data.db'
        db_path = root_path / db_path
        db = CreateDB(data_folder, db_path)
        db.run()
    ```

### Step 2: Configure and Run the Backtest

1. **Import the Required Modules:**

   Begin by importing the necessary modules for the backtest engine and the custom indicators you wish to use.

    ```python
    from OP_BackTest.core.Engine import Engine
    from Indicators.Alma import ALMAIndicator
    ```

2. **Define the Parameters:**

   Set up the parameters for your backtest in a dictionary format. This includes defining the time frame, trading times, expiry dates, indicators, and the legs of your strategy.

    ```python
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
    ```

3. **Initialize the Backtest Engine:**

   Create an instance of the `Engine` class by passing the strategy parameters, the path to the database, and the log path.

    ```python
    E = Engine(Strategy_parameters=parameter, db_path='OP_BackTest/DataDB/data.db', log_path='OP_BackTest/Logs/')
    ```

4. **Run the Backtest:**

   Execute the backtest by calling the `run` method on the `Engine` instance. The results, including the detailed trade book, will be displayed and saved as specified.

    ```python
    tradeBook = E.run()
    print(tradeBook)
    ```

### Complete Example

Here's a complete example demonstrating the usage of the backtest engine:

#### Creating the Database

```python
from OP_BackTest.core import CreateDB
from pathlib import Path

if __name__ == '__main__':
    root_path = Path(__file__).parent
    print(root_path)
    data_folder = 'data_folder'
    data_folder = root_path / data_folder
    db_path = 'OP_BackTest/DataDB/data.db'
    db_path = root_path / db_path
    db = CreateDB(data_folder, db_path)
    db.run()
```

#### Running the Backtest

```python
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

E = Engine(Strategy_parameters=parameter, db_path='OP_BackTest/DataDB/data.db', log_path='OP_BackTest/Logs/')
tradeBook = E.run()
print(tradeBook)
```