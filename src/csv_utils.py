import os
import time


def file_writer(path, write_string):
    ''''''
    with open(path, 'a+') as f:
        f.write(write_string)
    return True


def write_csv(action_obj):
    '''
    [
        1504541580000, // 0 UTC timestamp in milliseconds, integer
        4235.4,        // 1 (O)pen price, float
        4240.6,        // 2 (H)ighest price, float
        4230.0,        // 3 (L)owest price, float
        4230.7,        // 4 (C)losing price, float
        37.72941911    // 5 (V)olume (in terms of the base currency), float
    ]
    '''
    write_string = ','.join([
        str(action_obj['candle'][0]),
        str(action_obj['candle'][4]),
        'sell' if action_obj['sell'] else 'NA',
        'buy' if action_obj['buy'] else 'NA'
        ]) + '\n'

    date = time.strftime('%F')

    name_str = action_obj['coin'] + '_' + date + '.csv'

    path = os.path.join('csv_data', name_str)
    file_writer(path, write_string)
