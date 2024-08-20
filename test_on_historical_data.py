import csv
import os
from datetime import datetime

from stock_indicators import indicators
from stock_indicators.indicators.common.enums import Match
from stock_indicators.indicators.common.quote import Quote

from utils import get_value

"""
This script allows you to test your strategy on historical data
Historical data is in data_1m and data_5m folders
Replace put condition and call condition
Replace [-1] with [-i] and [-2] with [-i-1]
"""

TIMEFRAME = 1  # minutes
EXPIRATION = 1  # candles


def get_csv_files():
    filenames = []
    for filename in os.listdir(f'data_{TIMEFRAME}m'):
        if 'csv' not in filename:
            continue
        filenames.append(filename)
    return sorted(filenames)


def get_quotes(filename):
    # get quotes from csv file
    quotes = []
    with open(f'data_{TIMEFRAME}m/{filename}') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            try:
                timestamp = datetime.fromtimestamp(float(row[1]))
            except ValueError:  # pass header
                continue
            try:
                quotes.append(Quote(
                    date=timestamp,
                    open=row[2],
                    high=row[4],
                    low=row[5],
                    close=row[3],
                    volume=None))
            except ValueError:  # on Windows and non-en_US locale
                quotes.append(Quote(
                    date=timestamp,
                    open=str(row[2]).replace('.', ','),
                    high=str(row[4]).replace('.', ','),
                    low=str(row[5]).replace('.', ','),
                    close=str(row[3]).replace('.', ','),
                    volume=None))
            except Exception as e:
                print(e)
    return quotes


def check_indicators(quotes):
    sma_short = indicators.get_sma(quotes, lookback_periods=3)
    sma_long = indicators.get_sma(quotes, lookback_periods=8)

    orders = 0
    wins = 0
    draws = 0
    loses = 0

    for i in range(1, len(quotes) - 40, 1):
        try:

            # put condition
            if sma_short[-i-1].sma > sma_long[-i-1].sma and sma_short[-i].sma < sma_long[-i].sma:
                if get_value(quotes[-i]) < get_value(quotes[-i-1]) < get_value(quotes[-i-2]):

                        if get_value(quotes[-i]) < get_value(quotes[-i + EXPIRATION]):
                            orders += 1
                            wins += 1
                        elif get_value(quotes[-i]) == get_value(quotes[-i + EXPIRATION]):
                            orders += 1
                            draws += 1
                        else:
                            orders += 1
                            loses += 1

            # call condition
            if sma_short[-i-1].sma < sma_long[-i-1].sma and sma_short[-i].sma > sma_long[-i].sma:
                if get_value(quotes[-i]) > get_value(quotes[-i-1]) > get_value(quotes[-i-2]):

                        if get_value(quotes[-i]) > get_value(quotes[-i + EXPIRATION]):
                            orders += 1
                            wins += 1
                        elif get_value(quotes[-i]) == get_value(quotes[-i + EXPIRATION]):
                            orders += 1
                            draws += 1
                        else:
                            orders += 1
                            loses += 1

        except:
            pass

    return orders, wins, draws, loses


def main():
    csv_files = get_csv_files()

    all_orders = 0
    all_wins = 0
    all_draws = 0
    all_loses = 0

    for csv_file in csv_files:
        quotes = get_quotes(csv_file)
        orders, wins, draws, loses = check_indicators(quotes)
        print(csv_file, 'Orders:', orders, 'Wins:', wins, 'Loses:', loses, 'Win percent:', round(wins * 100 / orders, 2), '%')

        all_orders += orders
        all_wins += wins
        all_draws += draws
        all_loses += loses

    print('---')
    print('All Orders:', all_orders, 'All Wins:', all_wins, 'All Draws:', all_draws, 'All Loses:', all_loses, 'Win percent:', round(all_wins * 100 / all_orders, 2), '%')


if __name__ == '__main__':
    main()
