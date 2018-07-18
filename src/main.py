'''
make an exchange class that will run a strategy on a given amount of coins
'''

from concurrent.futures import (ThreadPoolExecutor, as_completed)

import ccxt


class Exchange:
    def __init__(self, exchange, coins):
        self.max_workers = 4

        self.coins = coins.split(',')
        self.exchange = exchange

    def get_data(self, coin):

        candle = self.exchange.fetch_ohlcv(coin)

        return candle

    def start_bot(self):

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            self.loop(ex)

    def loop(self, executor):
        print(self.coins)
        futures = {executor.submit(self.get_data, c): c for c in self.coins}

        for candle in as_completed(futures):
            print(candle.result())


def main():
    ''' the start function '''

    gdax = ccxt.gdax()

    gdax

    e = Exchange(gdax, 'BTC/USD,ETH/USD,BTC/USD,ETH/USD')

    e.start_bot()


if __name__ == '__main__':
    main()
