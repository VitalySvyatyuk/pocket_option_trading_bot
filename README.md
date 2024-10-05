# Pocket Option Trading Bot
Bot for autotrade in [Pocket Option](https://pocketoption.com/). Only for Demo mode!

### Installation
Install .NET6.0 or later: https://dotnet.microsoft.com/en-us/download/dotnet/6.0

For Windows users: download and install last Python version from here: https://www.python.org/downloads/

Download a project from Github by clicking `Code` -> `Download zip`, unzip the project.

Open a terminal (Mac and Linux users) or cmd terminal on Windows. Inside of terminal, go to the folder with a project you unzipped.

Type `pip3 install -r requirements.txt` to install dependencies.

### Run
by staying in the terminal with the project folder opened, type:

`python3 po_bot.py`
or

`python3 po_bot_indicators.py`
or

`python3 po_bot_ml.py`

### After authorization:
- switch account to `DEMO`
- set timeframe as `1 min`
- set time as `1 min`

### Information
Bot connects to websocket and receives signals every half a second from PO.
To make it more convenient, I simplify data to 1 second so that to use seconds
everywhere. After each change of currency, the screen reloads. It is to cut
unwanted signals from previous currencies.

### Pocket Option trading bot Martingale
`po_bot.py` - Martingale trading. The strategy is pretty simple. If the previous candle is red, the bot makes 'put' order. And 'call' otherwise. You can see a current Martingale stack in the console (Martingale stack). For example, Martingale stack [1, 3, 7, 15, 31, 62, 124, 249, 499, 999] means that if you order $1 and lose, the next order will be $3, then $7, and so on. You can change `MARTINGALE_COEFFICIENT`, but take it in mind that there is almost no difference between 2.0 and 2.1, but there is a HUGE difference between 1.9 and 2.0.

### Pocket Option trading bot with indicators
`po_bot_indicators.py` - script allows you to try different indicators and their combinations. See how an example in `check_indicators()` works and make your updates. Currently, the PSAR strategy is used. Despite using default parameters `acceleration_step=0.02`, `max_acceleration_factor=0.2`, bot's sensitivity is higher, so additional orders appear. Works for 1m and higher timeframes.

### Pocket Option trading bot with machine learning
`po_bot_ml.py` - script makes orders based on prediction. Random Forest Classifier approach is used. The prediction is based on the indicators: `awesome_oscillator`, `PSAR`, `CCI` and `MACD` from the last 200 candles. Bot makes an order when the probability is > 0.60. You can set even higher values (0.70, 0.80, 0.90) in the `check_data()` method. !important! You have to set an order time = TIME param. For example, your `po_bot_ml.py/TIME`=5, then set your order time to 5 minutes. Works for 1m and higher timeframes.

### Backtest

`test_on_historical_data.py` - here you can backtest strategies on historical data of 1m and 5m timeframes. To create your own history files, set `SAVE_CSV` to `True` in `po_bot_indicators.py`.



### FAQ
`Is it free?`
Yes, the bot is fully free and you can use it without any payments.

`Is it profitable?`
No, my greedy friend. Sometimes, you can have profitable days, but you will lose all your money in the long run.

`What's the purpose of the Bot then?`
The goal of the bot is to strengthen your Python programming skills, motivating you with the illusory opportunity to get rich.

### Telegram
https://t.me/pocketoption_trading_bot

### Donations
If you want to thank the author for his amazing work:

buy me a coffee:
https://buymeacoffee.com/vitaliisviatiuk

or

Patreon: https://www.patreon.com/pocket_option_trading_bot

or

send your BTC here: `bc1qemxzzy6rq6ycxjn0f00yqgptjqldkms8g2ucu0`
