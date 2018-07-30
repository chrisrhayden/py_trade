import pytest

from context import main


class FakeStrategy:
    def __init__(self, pair):
        self.pair = pair


class FakeExchange:
    def __init__(self):
        self.markets = {'BTC': 'fake btc market', 'ETH': 'fake eth market'}

    def load_markets(self):
        pass


class ccxt(FakeExchange):
    def __init__(self):
        super()


def test_process_args():
    ''' TODO: find a way to intercept the ccxt module '''


def test_make_strategys():
    pairs = ['BTC/USD', 'ETH/USD']

    strat_name = 'default_strategy'

    strats = main.make_strategies(pairs, strat_name)

    assert len(strats) == 2
