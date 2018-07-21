'''
make an exchange class that will run a strategy on a given amount of symbols
'''

import logging

import ccxt

from PyTrade import PyTrade
from default_strategy import Strategy
from csv_utils import write_csv


class Coin:
    def __init__(self, symbol, strategy, filter_func):
        self.symbol = symbol

        self.StrategyClass = strategy
        self.strategy = self.StrategyClass.check_strategy

        self.filter_func = filter_func


def setup_logger():
    fmt_str = '[%(asctime)s] - [%(levelname)s] - %(funcName)s - %(message)s'
    formatter = logging.Formatter(fmt_str)

    # get the logger
    logger = logging.getLogger('py_trade')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('py_trade.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)


def last_candle(candle_list):
    return candle_list[0]


def make_coin_class(symbols, strategy):
    coins = [Coin(s, strategy, last_candle) for s in symbols]

    return coins


def main():
    ''' the start function '''

    setup_logger()

    exchange = ccxt.cex({'enableRateLimit': None})

    exchange.load_markets()

    symbols = ['BTC/USD', 'ETH/USD',
               'BCH/USD', 'BTG/USD',
               'DASH/USD', 'XRP/USD',
               'XLM/USD', 'ZEC/USD']

    coins = make_coin_class(symbols, Strategy())

    bot = PyTrade(exchange, coins, [write_csv])

    bot.start_bot()


if __name__ == '__main__':
    main()
