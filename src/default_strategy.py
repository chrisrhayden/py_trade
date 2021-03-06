class Strategy:
    ''' to show the methods and make sure the bot works '''

    def __init__(self, pair):
        self.pair = pair

    def filter_data(self, unfiltered_data):
        ''' a convenience method to keep the strategy func clean '''
        return unfiltered_data[0]

    def check_strategy(self, data):
        return {'buy': None, 'sell': None}
