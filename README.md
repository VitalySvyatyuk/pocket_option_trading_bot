# Pocket Option Trading Bot with Machine Learning
Bot for autotrade in [Pocket Option](https://pocketoption.com/). Only for Demo mode!

### Installation
`pip3 install -r requirements.txt`

### Run
`python3 po_bot.py`

### After authorization:
- switch account to `DEMO`
- set timeframe as `15 sec`
- set time as `1:00 min`

### Information
Bot is for learning purposes only! And only for Demo mode!
The current version uses machine learning for price prediction.
Each row in dataframe includes the price from the previous 20 minutes.
Plus current price. 21 params in total. From the beginning, we have 3000 seconds
with prices from the history. This is pretty enough for teaching the model and
testing it. As you may see, I'm not using any indicators now, only price movement
is enough for the model. Also, I'm not using normalization/scale for the params,
as they all have similar values

What happens each second? 
- Each second bot teaches a model with the last data from the stack.
- Each second bot makes a prediction for the last price.
- Each second you may see a record 'Accuracy' 0.4-0.8 in the console.
- Each second bot calls or puts based on prediction. This activity is regulated by `MAX_ACTIONS` and  `ACTIONS_SECONDS` params, see below.

Too many things happen each second, that's why your processor will be loaded at 100%.
I'll fix that in one of the next versions.
I suggest choosing a currency with the highest accuracy value. In fact, the currency
with an accuracy of 0.7 will give you 55% of profitable results. If you see an accuracy
around 0.5-0.6, feel free to switch to another currency.

Bot connects to websocket and receives signals every half a second from PO.
To make it more convenient, I simplify data to 1 second so that to use seconds
everywhere. After each change of currency, the screen reloads. It is to cut
unwanted signals from previous currencies.

By default, Bot makes no more than 1 order in 15 seconds if conditions are met.
`MAX_ACTIONS` - amount of orders in `ACTIONS_SECONDS`. For example, if 
`MAX_ACTIONS` is set to 1 and `ACTIONS_SECONDS` is 15, bot will not open
more than 1 order in the next 15 seconds.

If you want to donate to me, please send USDT (TRC20) to `TN4pGa8q6r7wJBDVLvAzmRKrMvTrftwi8a`