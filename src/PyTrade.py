import time
import logging
from concurrent.futures import (ThreadPoolExecutor, as_completed)

from ccxt import (RequestTimeout, DDoSProtection, ExchangeError)


def future_wraper(fn, *args, **kwargs):
    '''
    id like all plugins / functions to at least return something

    since the inner function is not getting called by the executor we need to
    pass it something it can call so we use the lambdas
    '''
    try:
        ret = fn(*args, **kwargs)
    except Exception as e:
        # i think i need to move this out of the iner fun t to catch prperly
        # after
        raise e

    if ret:
        return lambda: ret
    else:
        return lambda: False


class PyTrade:
    def __init__(self, exchange, strategys, functions):
        self.log = logging.getLogger('py_trade')

        # cpu dependent I think, make this a variable some how
        self.max_workers = 4
        # TODO: this needs to be exchange dependent
        # the amount of time we can call the api in a second
        self.max_api_calls = 3

        # needs to be 
        # self.max_timeout_retries = 10
        # the timeout_retries needs to be unique for every strategy
        # self.timeout_retries = 0

        self.exchange = exchange
        self.strategys = strategys
        self.plugin_functions = functions

        self.api_hit_this_second = 0
        self.wait_data_stack = []

        self.plugin_data_stack = []

    def reset_bot(self):
        self.api_hit_this_second = 0
        self.wait_data_stack = []

    def start_bot(self):
        ''' TODO '''

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            # TODO: consider adding the condition to state
            while True:
                self.log.debug('start loop')

                self.reset_bot()

                begin_loop = time.time()
                # run the logic / strategy
                self.loop_logic(ex, self.strategys)

                for fn in self.plugin_functions:
                    self.run_plugin(ex, fn)

                self.log.debug(f'loop delta: {time.time() - begin_loop}')

                # make sure to fall out of the current minute
                time.sleep(1)
                # TODO: make the 60 correspond to the amount of strategys that
                # will be in wait_stack
                next_min = 60 - int(time.strftime('%S'))
                self.log.debug(f'sleep for {next_min}')
                time.sleep(next_min)

    def get_data(self, strategy):
        if self.api_hit_this_second == self.max_api_calls:
            self.wait_data_stack.append(strategy)
            return None

        self.api_hit_this_second += 1

        try:
            # TODO: make the amount of time adjustable
            candles = self.exchange.fetch_ohlcv(strategy.pair, '1m')
        except RequestTimeout:
            self.log.error('request timeout')
            # TODO: set a limit on retries
            if self.max_timeout_retries:
            return self.get_data(strategy)

        if candles is None or candles[0] is None:
            raise Exception(f'candles is none: {candles}')

        self.log.info(f'retrieved candles for {strategy.pair}')
        return candles

    def sell_function(self):
        print('\n\nbuying >>>>>\n')

    def buy_function(self):
        print('\n\nsellling >>>>>\n')

    def on_data(self, strategy, raw_data):
        '''
        this will spawn the buying and selling funcs,
        TODO: should make concurrent eventually

        strategy - a strategy class
        raw_data - what ever get_data() returns
        '''
        candle = strategy.filter_data(raw_data)

        self.log.debug(
                f'running strategy for {strategy.pair}\n- candle: {candle}')

        action_obj = strategy.check_strategy(candle)

        # naive buy / sell logic
        if action_obj['buy'] is True:
            self.buy_function()

        elif action_obj['sell'] is True:
            self.sell_function()

        action_obj['coin'] = strategy.pair.split('/')[0]
        action_obj['candle'] = candle

        return action_obj

    def unwrap_exception(self, exception_to_unwrap, source, stack):
        '''
        handle errors so to keep other coins going
        or not let a plugin kill a trade

        TODO: make this real
        '''

        try:
            exception_to_unwrap.result()

        except DDoSProtection:
            print('\nddos exception\n will add to the wait_data_stack\n')
            stack.append(source)

        except ExchangeError as e:
            print('ExchangeError >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', e)

    def loop_logic(self, executor, strategys):
        '''
        receive an executor instance and a list of strategy's to get data for

        when a get data func resolves run the given strategy,
        when the api limit has been hit add the strategy to the wait_data_stack

        if there is anything in the wait_data_stack reset the class then
        rerun loop_logic() with the leftovers

        executor - an executor instance from ThreadPoolExecutor handler

        strategys - a list of strategy class's to get data for
        '''

        futures = {executor.submit(self.get_data, s): s for s in strategys}

        for exchange_data in as_completed(futures):
            if exchange_data.exception():
                self.unwrap_exception(
                        exchange_data,
                        futures[exchange_data],
                        self.wait_data_stack)

            elif exchange_data.result():
                strategys = futures[exchange_data]

                completed_candle = self.on_data(strategys,
                                                exchange_data.result())

                self.plugin_data_stack.append(completed_candle)

        if len(self.wait_data_stack) > 0:
            # wait a full second
            time.sleep(1)
            wait_stack = self.wait_data_stack

            self.reset_bot()
            return self.loop_logic(executor, wait_stack)

    def run_plugin(self, executor, fn):
        '''
        run all the candles with a given plugin,
        the same more or less as loop_logic
        '''

        self.log.debug('running plugins')

        futures = [executor.submit(future_wraper(fn, obj))
                   for obj in self.plugin_data_stack]

        for complete_plugin in as_completed(futures):
            if complete_plugin.exception() and complete_plugin.result:
                # TODO: take things like function name and what not
                self.unwrap_exception(
                        complete_plugin,
                        futures[complete_plugin],
                        self.plugin_data_stack)

            elif complete_plugin.result():
                ret = complete_plugin.result()
                print(ret)
