# pocket_option_trading_bot
Bot for autotrade in [Pocket Option](https://pocketoption.com/). Only for Demo mode!

### Installation
Install packages from requirements.txt file. For using stock_indicators package,
.NET6 must be in the system: https://dotnet.microsoft.com/en-us/download/dotnet/6.0

### Run
`python3 po_bot.py`

### After authorization:
- switch account to `DEMO`
- set timeframe as `15 sec`
- set time as `1:30 seconds`
- switch `Trades` to `Closed`

![setup](https://raw.githubusercontent.com/VitalySvyatyuk/pocket_option_trading_bot/main/setup.jpg)

### Information
Bot is for learning purposes only! Use it only in Demo mode!
Bot always trades on OTC pairs which profit is 92%. If profit becomes less in some time, the currency will be changed
automatically. Also, if you have last 2 losses in a row, currency will be changed.
Bot makes no more than 1 order in 20 seconds if conditions are met.

I'm using 3 indicators with default params:
- Parabolic SAR. Signalizes reversal moment.
- MACD. > 0 for puts and < 0 for calls.
- ADX for trend detection. Should be > 18

Bot connects to websocket and receive signals every half a second from PO.
To make it more strict, I simplify data to 1 second so that to use seconds 
everywhere. After each changing of currency the screen reloads. It is to
cut unwanted signals from previous currencies.

You can play with `PERIOD` param to try different timeframes (candles).
But be careful with timeframes 30sec and more, because for such big timeframes
you have to wait 10-30 minutes for data to be cached. Do I don't recommend
to use timeframes 30sec+. At the other hand, all data for timeframes
less than 15sec is cached from the beginning and instantly ready for 
processing.

`MAX_ACTIONS` - amount of orders in `ACTIONS_SECONDS`. For example, if 
`MAX_ACTIONS` is set to 1 and `ACTIONS_SECONDS` is 20, bot will not open
more than 1 order in the next 20 seconds.

If you want to donate to me, please send USDT (TRC20) to `TN4pGa8q6r7wJBDVLvAzmRKrMvTrftwi8a`