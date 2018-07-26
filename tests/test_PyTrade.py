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


def test_get_data_good(py_trade_class):
    '''
    test that we get data back (if all goes well on the server side)

    test if it will add to the wait_data_stack
    if api_hit_this_second is over limit
    '''
    # TODO: test error handling

    strat = py_trade_class.strategys[0]

    data = py_trade_class.get_data(strat)

    assert len(data) == 2


def test_get_data_max_api_calls(py_trade_class):
    py_trade_class.api_hit_this_second = py_trade_class.max_api_calls

    strat = py_trade_class.strategys[0]

    data = py_trade_class.get_data(strat)

    assert data is None

    assert len(py_trade_class.wait_data_stack) == 1


def test_on_data_no_action(py_trade_class):
    strat = py_trade_class.strategys[0]

    obj_to_cmp_none = {
            'candle': a_candle,
            'coin': 'BTC',
            'buy': None,
            'sell': None
            }

    action_obj = py_trade_class.on_data(strat, two_candls)

    assert action_obj == obj_to_cmp_none


def test_on_data_buy(py_trade_class):
    obj_to_cmp_buy = {
            'candle': a_candle,
            'coin': 'BTC',
            'buy': True,
            'sell': None
            }

    strat = py_trade_class.strategys[0]

    strat.check_strategy = lambda data: {'buy': True, 'sell': None}

    action_obj_buy = py_trade_class.on_data(strat, two_candls)

    assert action_obj_buy == obj_to_cmp_buy


def test_on_data_sell(py_trade_class):
    strat = py_trade_class.strategys[0]
    obj_to_cmp_sell = {
            'candle': a_candle,
            'coin': 'BTC',
            'buy': None,
            'sell': True
            }

    strat.check_strategy = lambda data: {'buy': None, 'sell': True}

    action_obj_sell = py_trade_class.on_data(strat, two_candls)

    assert action_obj_sell == obj_to_cmp_sell


# TODO: test exception handling
def test_loop_logic(py_trade_class):
    ''''''

    with ThreadPoolExecutor(max_workers=4) as ex:

        # idk why it didn't like just a variable
        get_data_calls = {'calls': 0}

        data_func = py_trade_class.get_data

        def get_data_wrapper_fun(data):
            get_data_calls['calls'] = get_data_calls['calls'] + 1
            return data_func(data)

        py_trade_class.get_data = get_data_wrapper_fun

        py_trade_class.loop_logic(ex, py_trade_class.strategys)

        assert len(py_trade_class.plugin_data_stack) == 1

        assert get_data_calls['calls'] == 1

        get_data_calls['calls'] = 0

        py_trade_class.wait_data_stack = [py_trade_class.strategys[0],
                                          py_trade_class.strategys[0]]

        py_trade_class.api_hit_this_second = py_trade_class.max_api_calls

        assert len(py_trade_class.wait_data_stack) == 2

        py_trade_class.loop_logic(ex, [])

        assert get_data_calls['calls'] == 2

        assert len(py_trade_class.wait_data_stack) == 0


plugin_calls = {'one_calls': 0, 'two_calls': 0}


def fake_plugin_one(data_obj):
    plugin_calls['one_calls'] = plugin_calls['one_calls'] + 1

    # just to return something
    return plugin_calls


def fake_plugin_two(data_obj):
    plugin_calls['two_calls'] = plugin_calls['two_calls'] + 1


def test_plugins(py_trade_class):
    ''' im unsure what to test here '''

    with ThreadPoolExecutor(max_workers=4) as ex:
        py_trade_class.plugin_data_stack = py_trade_class.strategys

        py_trade_class.run_plugin(ex, fake_plugin_one)

        assert plugin_calls['one_calls'] == 1

        py_trade_class.run_plugin(ex, fake_plugin_two)

        assert plugin_calls['two_calls'] == 1
