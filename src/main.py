'''
Usage:
    py_trade -e EXCHANGE -p PAIRS -s STRATEGY [-l LOG_LEVEL]


Options:
    -e --exchange EXCHANGE  an exchange to use

    -p --pairs PAIRS        a comma separated string of symbol and currency pairs

    -s --strategy STRATEGY  the strategy module to use, must be in src/

    -l --log-cli LOG_LEVEL  set the cli logging level, if not set nothing will
                            be logged to the console
                                i.e. 'DEBUG' or 'INFO'

Examples:
    trade both btc and eth on cex exchange
        py_trade -e 'cex' -s 'BTC/USD,ETH/USD' -s any_strat -l 'INFO'
''' # noqa: 501
# E501: lines over 80 chars

import logging
import importlib

import ccxt

from docopt import docopt

from PyTrade import PyTrade
from csv_utils import write_csv


def setup_logger(args):
    ''' make the log handlers and set the format_str '''

    fmt_str = '[%(asctime)s] - [%(levelname)s] - %(funcName)s - %(message)s'
    formatter = logging.Formatter(fmt_str)

    logger = logging.getLogger('py_trade')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('py_trade.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    if args['--log-cli']:
        sh = logging.StreamHandler()

        log_level = args['--log-cli'].upper()
        sh.setLevel(getattr(logging, log_level))

        sh.setFormatter(formatter)

        logger.addHandler(sh)

    return logger


def process_args(args):
    ''' return a instantiated ccxt exchange class '''

    exchange_name = args['--exchange']

    ex_attr = getattr(ccxt, exchange_name)

    exchange = ex_attr({'enableRateLimit': False})

    exchange.load_markets()

    available_pairs = exchange.markets.keys()

    maybe_pairs = args['--pairs'].split(',')

    pairs = []
    bad_pairs = []

    for s in maybe_pairs:
        if s not in available_pairs:
            bad_pairs.append(s)
        else:
            pairs.append(s)

    if bad_pairs:
        print(f'\na few pairs are not present in the {exchange_name} market'
              '\nwould you like to continue with out these pairs'
              f'\n\n - included {pairs}'
              f'\n\n - not included {bad_pairs}'
              '\n\n'
              )
        user_input = input(' [y]es|[n]o -> ').lower()

        if user_input == 'no' or user_input == 'n':
            return False, False

    return exchange, pairs


def make_strategies(pairs, strategy_name):
    ''' return a list of strategy's with given pairs '''

    # TODO: make this work for any path
    strat_module = importlib.import_module(strategy_name)

    return [strat_module.Strategy(p) for p in pairs]


def main(args):
    '''
    gather the various parts and run the bot loop

    symbols = ['BTC/USD', 'ETH/USD',
               'BCH/USD', 'BTG/USD',
               'DASH/USD', 'XRP/USD',
               'XLM/USD', 'ZEC/USD']


    at the moment the setup will panic when something isn't right but hopefully
    once the strategy's are running i can kill a panicking strategy without the
    others dieing as well
    '''

    exchange, pairs = process_args(args)

    if exchange is False:
        return

    strategys = make_strategies(pairs, args['--strategy'])

    plugins = [write_csv]

    bot = PyTrade(exchange, strategys, plugins)

    bot.start_bot()


if __name__ == '__main__':
    args = docopt(__doc__)
    logger = setup_logger(args)
    logger.debug(args)
    main(args)
