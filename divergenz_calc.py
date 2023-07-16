import requests
import time


class DivergenzCalc:

    div_message = None

    def __init__(self, timeframes_to_watch=30, rsi_length=14):
        self.historical_prices, \
        self.high_list,\
        self.low_list,\
        self.rsi_ma_list,\
        self.rsi_ema_list,\
        self.rsi_rma_list,\
        self.avg_gain_ma,\
        self.avg_loss_ma,\
        self.avg_gain_ema,\
        self.avg_loss_ema,\
        self.avg_gain_rma,\
        self.avg_loss_rma = self.initial_data(timeframes_to_watch, rsi_length)

    ''' 
        different methods to compute rsi
        return rsi depending on data values length and corresponding avg_gain, avg_loss
        
        calc_rsi_ma is actually used
    '''
    def calc_rsi_ma(self, change, avg_gain, avg_loss):
        if change > 0:
            avg_gain = (avg_gain * 13 + change) / 14
            avg_loss = (avg_loss * 13) / 14
        elif change < 0:
            avg_gain = (avg_gain * 13) / 14
            avg_loss = (avg_loss * 13 - change) / 14
        rsi = 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
        return rsi, avg_gain, avg_loss

    def calc_rsi_ema(self, change, avg_gain, avg_loss):
        sf = 2 / (14 + 1)
        if change > 0:
            avg_gain = (1 - sf) * avg_gain + sf * change
            avg_loss = (1 - sf) * avg_loss
        elif change < 0:
            avg_gain = (1 - sf) * avg_gain
            avg_loss = (1 - sf) * avg_loss - sf * change
        rsi = 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
        return rsi, avg_gain, avg_loss

    def calc_rsi_rma(self, change, avg_gain, avg_loss):
        sf = 1 / 14
        if change > 0:
            avg_gain = (1 - sf) * avg_gain + sf * change
            avg_loss = (1 - sf) * avg_loss
        elif change < 0:
            avg_gain = (1 - sf) * avg_gain
            avg_loss = (1 - sf) * avg_loss - sf * change
        rsi = 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
        return rsi, avg_gain, avg_loss

    ''' 
        high and lows computing of data
        returns lists of indices of local maxima and minima
    '''
    def check_high_low(self, data, old_pos_lst, old_neg_lst, initial=False):

        pos_lst = old_pos_lst.copy()
        neg_lst = old_neg_lst.copy()

        if initial:
            for i in range(1, len(data) - 1):
                # pos case
                if data[i] > data[i + 1] and data[i] > data[i - 1]:
                    if len(pos_lst) > 0:
                        if data[pos_lst[-1]] < data[i]:
                            pos_lst.append(i)
                    else:
                        pos_lst.append(i)
                # neg case
                elif data[i] < data[i + 1] and data[i] < data[i - 1]:
                    if len(neg_lst) > 0:
                        if data[neg_lst[-1]] > data[i]:
                            neg_lst.append(i)
                    else:
                        neg_lst.append(i)
        else:
            # pos case
            if data[-2] > data[-1] and data[-2] > data[-3]:
                if len(pos_lst) > 0:
                    if data[pos_lst[-1]] < data[-2]:
                        pos_lst.append(len(data) - 2)
                        self.div_message = self.pos_div_check()
                else:
                    pos_lst.append(len(data) - 2)
            # neg case
            elif data[-2] < data[-1] and data[-2] < data[-3]:
                if len(neg_lst) > 0:
                    if data[neg_lst[-1]] > data[-2]:
                        neg_lst.append(len(data) - 2)
                        self.div_message = self.neg_div_check()
                else:
                    neg_lst.append(len(data) - 2)

        return pos_lst, neg_lst

    ''' 
        method to get price information of currency
        returns an array of 'close' prices
    '''
    def hourly_price_historical(self, symbol, comparison_symbol, limit, aggregate, exchange=''):
        url = 'https://min-api.cryptocompare.com/data/histohour?fsym={}&tsym={}&limit={}&aggregate={}' \
            .format(symbol.upper(), comparison_symbol.upper(), limit, aggregate)
        if exchange:
            url += '&e={}'.format(exchange)
        page = requests.get(url)
        data = page.json()['Data']

        #api retrievs one element more than limit, so delete the first and the oldest element
        return [i["close"] for i in data[1:]], data[-1]['time']

    ''' 
        initial method to get price data set and first rsi values
        returns parameters for future computation and actual data length set in 'timeframes_to_watch' parameter
    '''
    def initial_data(self, timeframes_to_watch, rsi_length):
        data_global, self.last_timestamp = self.hourly_price_historical('BTC', 'USD', timeframes_to_watch + rsi_length, 1)


        avg_gain, avg_loss = self.avg_gain_loss_init(data_global[:rsi_length + 1])

        # initial values
        avg_gain_ma, avg_loss_ma = avg_gain, avg_loss
        avg_gain_ema, avg_loss_ema = avg_gain, avg_loss
        avg_gain_rma, avg_loss_rma = avg_gain, avg_loss

        rsi_ma_list = []
        rsi_ema_list = []
        rsi_rma_list = []
        for i in range(1, timeframes_to_watch + 1):
            # change in procent from one value to another
            change = (data_global[i] / data_global[i - 1] - 1.0) * 100

            # different methods to compute rsi
            rsi_ma, avg_gain_ma, avg_loss_ma = self.calc_rsi_ma(change, avg_gain_ma, avg_loss_ma)
            rsi_ema, avg_gain_ema, avg_loss_ema = self.calc_rsi_ema(change, avg_gain_ema, avg_loss_ema)
            rsi_rma, avg_gain_rma, avg_loss_rma = self.calc_rsi_rma(change, avg_gain_rma, avg_loss_rma)

            rsi_ma_list.append(rsi_ma)
            rsi_ema_list.append(rsi_ema)
            rsi_rma_list.append(rsi_rma)

        high, low = self.check_high_low(data_global[-timeframes_to_watch:], [], [], initial=True)

        return data_global[
               -timeframes_to_watch:], high, low, rsi_ma_list, rsi_ema_list, rsi_rma_list, avg_gain_ma, avg_loss_ma, avg_gain_ema, avg_loss_ema, avg_gain_rma, avg_loss_rma

    ''' 
        method to compute initial average gain and loss
        returns average gain and loss
    '''
    def avg_gain_loss_init(self, data, rsi_length=14):
        gain = 0.0
        loss = 0.0

        for i in range(1, rsi_length + 1):
            change_procent = (data[i] / data[i - 1] - 1.0) * 100
            if change_procent > 0:
                gain += change_procent
            elif change_procent < 0:
                loss -= change_procent

        return gain / rsi_length, loss / rsi_length
    '''
        method to get data of the new hour, compute parameters and check divergence
    '''
    def get_new_hour(self, new_timestamp, new_data):
        if new_timestamp > self.last_timestamp:
            self.last_timestamp = new_timestamp
            self.historical_prices.append(new_data)

            # shift view window to the right (delete last elem and add new elem)
            self.historical_prices = self.historical_prices[1:]
            self.rsi_ma_list = self.rsi_ma_list[1:]
            self.rsi_ema_list = self.rsi_ema_list[1:]
            self.rsi_rma_list = self.rsi_rma_list[1:]

            # reduce high and low indices by one, delete negativ indices
            self.high_list = [i - 1 for i in self.high_list]
            if len(self.high_list) > 0 and self.high_list[0] < 0:
                self.high_list = self.high_list[1:]
            self.low_list = [i - 1 for i in self.low_list]
            if len(self.low_list) > 0 and self.low_list[0] < 0:
                self.low_list = self.low_list[1:]

            # compute price change and rsi's
            change = (self.historical_prices[-1] / self.historical_prices[-2] - 1.0) * 100
            rsi_ma, self.avg_gain_ma, self.avg_loss_ma = self.calc_rsi_ma(change, self.avg_gain_ma,
                                                                          self.avg_loss_ma)
            rsi_ema, self.avg_gain_ema, self.avg_loss_ema = self.calc_rsi_ema(change, self.avg_gain_ema,
                                                                              self.avg_loss_ema)
            rsi_rma, self.avg_gain_rma, self.avg_loss_rma = self.calc_rsi_rma(change, self.avg_gain_rma,
                                                                              self.avg_loss_rma)
            self.rsi_ma_list.append(rsi_ma)
            self.rsi_ema_list.append(rsi_ema)
            self.rsi_rma_list.append(rsi_rma)

            self.high_list, self.low_list = self.check_high_low(self.historical_prices, self.high_list,
                                                                self.low_list)

    def run(self):
        while (True):
            new_data, new_timestamp = self.hourly_price_historical('BTC', 'USD', 1, 1)
            if new_timestamp > self.last_timestamp:
                self.get_new_hour(new_timestamp, new_data[0])
            time.sleep(60)


    '''
        method checks if difference between 2 values of rsi_list corresponding a pair of
        - high_list indices is negative
        - low_list indices is positive
        
        returns divergence notification or None 
    '''
    def pos_div_check(self):
        print('in pos check')
        for i in range(len(self.high_list) - 1):
            if self.rsi_ma_list[self.high_list[-1]] < self.rsi_ma_list[self.high_list[-i - 2]]:
                return f"FOUND POSITIVE RSI PRICE DIVERGENCE {len(self.historical_prices) - self.high_list[-i - 2] - 1} HOURS AGO!!!"

    def neg_div_check(self):
        print('in neg check')
        for i in range(len(self.low_list) - 1):
            if self.rsi_ma_list[self.low_list[-1]] > self.rsi_ma_list[self.low_list[-i - 2]]:
                return f"FOUND NEGATIVE RSI PRICE DIVERGENCE {len(self.historical_prices) - self.low_list[-i - 2] - 1} HOURS AGO!!!"



# dc = DivergenzCalc()
# dc.run()













