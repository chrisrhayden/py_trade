'''
Usage:
    py_trade -e EXCHANGE -p PAIRS


Options:
    -e --exchange EXCHANGE  an exchange to use

    -p --pairs PAIRS        a comma separated string of symbol and currency pairs

Examples:
    trade both btc and eth on cex exchange
        py_trade -e 'cex' -s 'BTC/USD,ETH/USD'
''' # noqa: 501
# E501: lines over 80 chars

import logging

import ccxt

from docopt import docopt

from PyTrade import PyTrade
from default_strategy import Strategy
from csv_utils import write_csv


def setup_logger():
    ''' make the log handlers and set the format_str '''

    fmt_str = '[%(asctime)s] - [%(levelname)s] - %(funcName)s - %(message)s'
    formatter = logging.Formatter(fmt_str)

    logger = logging.getLogger('py_trade')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('py_trade.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)


def process_args(args):
    ''' return a instantiated ccxt exchange class '''

    exchange_name = args['--exchange']

    try:
        ex_attr = getattr(ccxt, exchange_name)
    except AttributeError:
        print(f'{exchange_name} is not a ccxt supported exchange')
        return False, False

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


def make_strategies(pairs):
    # TODO: make dynamic
    return [Strategy(p) for p in pairs]


def main(args):
    ''' the start function '''
    # symbols = ['BTC/USD', 'ETH/USD',
    #            'BCH/USD', 'BTG/USD',
    #            'DASH/USD', 'XRP/USD',
    #            'XLM/USD', 'ZEC/USD']
    setup_logger()

    exchange, pairs = process_args(args)

    if exchange is False:
        return

    strategys = make_strategies(pairs)

    plugins = [write_csv]

    bot = PyTrade(exchange, strategys, plugins)

    bot.start_bot()


if __name__ == '__main__':
    args = docopt(__doc__)
    print(args)
    main(args)
