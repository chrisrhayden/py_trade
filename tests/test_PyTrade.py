import pytest

from context import PyTrade

from concurrent.futures import ThreadPoolExecutor

a_candle = [1504541580000, 4235.4, 4240.6, 4230.0, 4230.7, 37.72941911]
two_candls = [a_candle, a_candle]


class FakeExchange:
    def fetch_ohlcv(self, pair, time):
        return [[1504541580000,
                 4235.4,
                 4240.6,
                 4230.0,
                 4230.7,
                 37.72941911
                 ],
                [1504541580000,
                 4235.4,
                 4240.6,
                 4230.0,
                 4230.7,
                 37.72941911
                 ]]


class FakeStrategy:
    def __init__(self):
        self.pair = 'BTC/USD'

    def filter_data(self, raw_data):
        return raw_data[0]

    def check_strategy(self, data):
        return {'buy': None, 'sell': None}


@pytest.fixture
def py_trade_class():
    ''''''
    return PyTrade.PyTrade(FakeExchange(), [FakeStrategy()])


def test_get_data(py_trade_class):
    '''
    test that we get data back (if all goes well on the server side)

    test if it will add to the wait_data_stack
    if api_hit_this_second is over limit
    '''
    # TODO: test error handling

    strat = py_trade_class.strategys[0]

    data = py_trade_class.get_data(strat)

    assert len(data) == 2

    py_trade_class.api_hit_this_second = 3

    data = py_trade_class.get_data(strat)

    assert data is None

    assert len(py_trade_class.wait_data_stack) == 1


def test_on_data(py_trade_class):
    strat = py_trade_class.strategys[0]

    obj_to_cmp_none = {
            'candle': a_candle,
            'coin': 'BTC',
            'buy': None,
            'sell': None
            }

    obj_to_cmp_buy = {
            'candle': a_candle,
            'coin': 'BTC',
            'buy': True,
            'sell': None
            }

    obj_to_cmp_sell = {
            'candle': a_candle,
            'coin': 'BTC',
            'buy': None,
            'sell': True
            }

    action_obj = py_trade_class.on_data(strat, two_candls)

    assert action_obj == obj_to_cmp_none

    strat.check_strategy = lambda data: {'buy': True, 'sell': None}

    action_obj_buy = py_trade_class.on_data(strat, two_candls)

    assert action_obj_buy == obj_to_cmp_buy

    strat.check_strategy = lambda data: {'buy': None, 'sell': True}

    action_obj_sell = py_trade_class.on_data(strat, two_candls)

    assert action_obj_sell == obj_to_cmp_sell


def test_loop_logic(py_trade_class):
    ''''''

    with ThreadPoolExecutor(max_workers=4) as ex:
        py_trade_class.loop_logic(ex, py_trade_class.strategys)

        assert len(py_trade_class.plugin_data_stack) == 1
