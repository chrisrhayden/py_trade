'''
make an exchange class that will run a strategy on a given amount of symbols
'''

import ccxt

from PyTrade import PyTrade


def main():
    ''' the start function '''

    exchange = ccxt.poloniex()

    exchange.load_markets()

    bot = PyTrade(
            exchange,
            ['BCH/BTC', 'BCH/USD', 'BTC/EUR', 'BTC/GBP', 'BTC/USD',
             'ETH/BTC', 'ETH/EUR', 'ETH/USD', 'LTC/BTC', 'LTC/EUR',
             'LTC/USD', 'BCH/EUR'])

    bot.start_bot()


if __name__ == '__main__':
    main()
