# Pocket Option Simple Trading Bot
Bot for autotrade in [Pocket Option](https://pocketoption.com/). Only for Demo mode!

### Installation
`pip3 install -r requirements.txt`

Setup your chromedriver in the paths on the lines 83-85 of the script.
Chromedriver can be downloaded from here: https://googlechromelabs.github.io/chrome-for-testing/

### Run
`python3 po_bot.py`

### After authorization:
- switch account to `DEMO`
- set timeframe as `5 sec`
- set time as `5 sec`

### Information
Bot connects to websocket and receives signals every half a second from PO.
To make it more convenient, I simplify data to 1 second so that to use seconds
everywhere. After each change of currency, the screen reloads. It is to cut
unwanted signals from previous currencies.

### Strategy
The strategy is pretty simple. If the previous candle is red, the bot makes 'put' order. And 'call' otherwise. Bot makes 1 order every 10 seconds. Martingale approach is used, you can see a current Martingale stack in the console (Amounts). For example, Martingale stack [1, 3, 7, 15, 31, 62, 124, 249, 499, 999] means that if you order $1 and lose, the next order will be $3, then $7, and so on. You can change `MARTINGALE_COEFFICIENT`, but take it in mind that there is almost no difference between 2.0 and 2.1, but there is a HUGE difference between 1.9 and 2.0

### Profitability
This script will make you poor in the long run:
- there is 39% chance to increase your $100
 to $200 and 61% of losing everything
- there is 94% chance to increase your $3000 to $3100 and 6% of losing everything
- there is 0.05% chance to increase your $100 to $3100

For donations: `TN4pGa8q6r7wJBDVLvAzmRKrMvTrftwi8a`