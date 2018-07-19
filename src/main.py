'''
make an exchange class that will run a strategy on a given amount of symbols
'''

import time
from concurrent.futures import (ThreadPoolExecutor, as_completed)

import ccxt
from ccxt import RequestTimeout


class PyTrade:
    def __init__(self, exchange, symbols):
        self.max_workers = 4
        # TODO: this needs to be exchange dependent
        # the amount of time we can call the api in a second
        self.max_api_calls = 3

        self.symbols = symbols
        self.exchange = exchange

        self.api_hit_this_second = 0
        self.wait_stack = []

    def start_bot(self):

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            # lets only loop twice for now
            c = 0
            while c < 2:
                # reset the bot
                self.api_hit_this_second = 0
                self.wait_stack = []

                begin_loop = time.time()
                print(f'loop {c + 1} time: {begin_loop}')

                # run the logic / strategy
                self.loop_logic(ex, self.symbols)
                print(f'after loop {c + 1} dleta: {time.time() - begin_loop}')

                c += 1

                print('now we sleep')
                # make sure to fall out of the current minute
                time.sleep(1)
                # TODO: make the 60 correspond to the amount of symbols that
                # will be in wait_stack
                next_min = 60 - int(time.strftime('%S'))
                time.sleep(next_min)

    def get_data(self, coin):
        if self.api_hit_this_second == self.max_api_calls:
            self.wait_stack.append(coin)
            return None

        self.api_hit_this_second += 1

        try:
            candle = self.exchange.fetch_ohlcv(coin)
        except RequestTimeout:
            # TODO: set a limit on retries
            return self.get_data(coin)

        return candle

    def loop_logic(self, executor, symbols):
        '''
        receive an executor instance and a list of symbols to retrieve data to
        then pass to a strategy

        TODO add strategy
        the strategy will return a string that will tell the bot what to do if
        anything at all

        executor - an executor instance from ThreadPoolExecutor handler

        symbols - a list of symbols to get data for
        '''

        futures = {executor.submit(self.get_data, s): s for s in symbols}

        for exchange_data in as_completed(futures):
            candles = exchange_data.result()

            if candles is None:
                continue
            elif exchange_data.exception():
                # print(result)
                print('fuck')
            else:
                print(candles[-1])

        if len(self.wait_stack) > 0:
            # wait a full second
            time.sleep(1)
            wait_stack = self.wait_stack

            self.api_hit_this_second = 0
            self.wait_stack = []
            return self.loop_logic(executor, wait_stack)


def main():
    ''' the start function '''

    gdax = ccxt.gdax()

    gdax.load_markets()

    e = PyTrade(
            gdax,
            ['BCH/BTC', 'BCH/USD', 'BTC/EUR', 'BTC/GBP', 'BTC/USD',
             'ETH/BTC', 'ETH/EUR', 'ETH/USD', 'LTC/BTC', 'LTC/EUR',
             'LTC/USD', 'BCH/EUR'])

    e.start_bot()


if __name__ == '__main__':
    main()
