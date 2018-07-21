import logging
import time
from concurrent.futures import (ThreadPoolExecutor, as_completed)

from ccxt import RequestTimeout


def future_wraper(fn, *args, **kwargs):
    ret = fn(*args, **kwargs)

    if ret:
        return ret
    else:
        return None


class PyTrade:
    def __init__(self, exchange, coins, functions):
        self.max_workers = 4
        # TODO: this needs to be exchange dependent
        # the amount of time we can call the api in a second
        self.max_api_calls = 3

        self.coins = coins
        self.exchange = exchange

        self.api_hit_this_second = 0
        self.wait_data_stack = []

        self.functions = functions
        self.plugin_data_stack = []

        self.log = logging.getLogger('py_trade')

    def start_bot(self):
        ''' TODO '''

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            # lets only loop twice for now
            # TODO: consider adding the condition to state
            while True:
                self.log.debug('start loop')
                # reset the bot
                self.api_hit_this_second = 0
                self.wait_data_stack = []

                begin_loop = time.time()
                # run the logic / strategy
                self.loop_logic(ex, self.coins)

                for fn in self.functions:
                    self.run_plugin(ex, fn)

                self.log.debug(f'loop delta: {time.time() - begin_loop}')

                # make sure to fall out of the current minute
                time.sleep(1)
                # TODO: make the 60 correspond to the amount of coins that
                # will be in wait_stack
                next_min = 60 - int(time.strftime('%S'))
                self.log.debug(f'sleep for {next_min}')
                time.sleep(next_min)

    def get_data(self, coin):
        if self.api_hit_this_second == self.max_api_calls:
            self.wait_data_stack.append(coin)
            return None

        self.api_hit_this_second += 1

        try:
            candles = self.exchange.fetch_ohlcv(coin.symbol, '1m')
        except RequestTimeout:
            self.log.error('request timeout')
            # TODO: set a limit on retries
            return self.get_data(coin)

        if candles is None or candles[0] is None:
            raise Exception(f'candles is none {candles}')

        candle = coin.filter_func(candles)

        self.log.info(f'retrieved candle for {coin.symbol}')
        return candle

    def sell_function(self):
        print('\n\nbuying >>>>>\n')

    def buy_function(self):
        print('\n\nsellling >>>>>\n')

    def on_data(self, coin, candle):
        ''''''
        action_obj = coin.strategy(candle)

        if action_obj['buy'] is True:
            self.buy_function()

        elif action_obj['sell'] is True:
            self.sell_function()

        action_obj['coin'] = coin.symbol.split('/')[0]
        action_obj['candle'] = candle

        return action_obj

    def loop_logic(self, executor, coins):
        '''
        receive an executor instance and a list of coins to retrieve data to
        then pass to a strategy

        TODO add strategy
        the strategy will return a string that will tell the bot what to do if
        anything at all

        executor - an executor instance from ThreadPoolExecutor handler

        coins - a list of coins to get data for
        '''

        futures = {executor.submit(self.get_data, c): c for c in coins}

        for exchange_data in as_completed(futures):
            data = exchange_data.result()

            if data is None:
                continue
            elif exchange_data.exception():
                # TODO i dont this thie will exicut becas i think the result()
                # will panic the main progra when call and it has an error
                print('\n\nexchange exception >>>>>>>>>>>>>')
            else:
                # TODO: make a way to adjust the size i guess
                coin = futures[exchange_data]

                self.log.debug(
                    f'running strategy for {coin.symbol}\n   - data: {data}')

                action_obj = self.on_data(coin, data)
                self.plugin_data_stack.append(action_obj)

        if len(self.wait_data_stack) > 0:
            # wait a full second
            time.sleep(1)
            wait_stack = self.wait_data_stack

            self.api_hit_this_second = 0
            self.wait_data_stack = []
            return self.loop_logic(executor, wait_stack)

    def run_plugin(self, executor, fn):
        self.log.debug('running plugins')

        futures = [executor.submit(future_wraper(fn, obj))
                   for obj in self.plugin_data_stack]

        for complete_plugin in as_completed(futures):
            if not complete_plugin.exception():
                print(complete_plugin.result())
