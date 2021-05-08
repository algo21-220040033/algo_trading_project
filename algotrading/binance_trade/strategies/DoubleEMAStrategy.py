"""

    Double EMA Strategy.
"""

from binance_trade.gateway.binance_http import BinanceFutureHttp, Interval, OrderType, OrderSide
import pandas as pd
pd.set_option("expand_frame_repr", False)
import talib
from datetime import datetime
from binance_trade.util.utility import round_to, load_json, save_json
import time
import logging

class DoubelEMAStrategy(object):

    variables = ["strategy_pos"]  #

    def __init__(self, http_client: BinanceFutureHttp, symbol='BTCUSDT',  file_name=None):

        self.http_client = http_client
        self.symbol = symbol

        self.file_name = file_name if file_name else self.__class__.__name__
        self.json_data = load_json(self.file_name)

        self.strategy_pos = 0  # 给个默认的值
        for key in self.variables:
            self.__setattr__(key, float(self.json_data.get(key, 0)))

        print(f"self.strategy_pos: {self.strategy_pos}")
        self.open_orders = []
        self.pos_dict = {}  # 默认的仓位信息.

        # 策略的参数.
        self.fast_ema_window = 15
        self.slow_ema_window = 50
        self.trade_money = 1  # 10USDT.
        self.min_volume = 0.001  # 最小的交易数量.
        self.trade_size = 0
        self.trend_status = 0
        self.last_price = 0

        self.logger = logging.getLogger(__name__)

    def on_1hour_kline_data(self, symbol, interval=Interval.HOUR_1):
        """
        拿到k线的方法.
        :param df:
        :return:
        """
        # print(symbol)

        data = self.http_client.get_kline(symbol, interval=interval)

        df = pd.DataFrame(data, columns={"open_time":0, 'open': 1, 'high': 2, 'low': 3, 'close': 4,
                                         'volume': 5, 'close_time': 6, 'trade_money': 7, 'trade_count': 8,
                                         'buy_volume': 9, 'sell_volume': 10, 'other': 11
                                         })

        df = df[['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time']]
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms') + pd.Timedelta(hours=8)
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms') + pd.Timedelta(hours=8)
        # print(df)

        self.calculate_signal(df)

    def calculate_signal(self, df):

        # print(df)
        current_bar = df.iloc[-1]  # 最后一行.
        now = datetime.now()
        if current_bar['close_time'] > now:  # 防止时间提前了, 收盘价的时候还没有到整点.
            df.drop(len(df)-1, inplace=True)  # 删除最后一行.

        df['fast_ema'] = talib.EMA(df['close'], timeperiod=self.fast_ema_window)
        df['slow_ema'] = talib.EMA(df['close'], timeperiod=self.slow_ema_window)
        # print(df)
        # 获得最后两个Bar, 看看他们的数据, 比较金叉和死叉.
        current_bar = df.iloc[-1]
        last_bar = df.iloc[-2]

        # 计算开仓的数量
        self.trade_size = round_to(self.trade_money / float(current_bar['close']), self.min_volume)
        if self.trade_size < self.min_volume:
            self.trade_size = self.min_volume

        # 金叉的时候.
        if current_bar['fast_ema'] > current_bar['slow_ema'] and last_bar['fast_ema'] <= last_bar['slow_ema']:
            self.trend_status = 1
        # 死叉的时候.
        elif current_bar['fast_ema'] < current_bar['slow_ema'] and last_bar['fast_ema'] >= last_bar['slow_ema']:
            self.trend_status = -1
        else:
            self.trend_status = 0

        # self.trend_status = 1  # 测试使用.

    def on_tick(self, tick_data):
        """
        250ms
        拿到tick数据的方法.
        {'volume': 144748.226, 'open_price': 7397.99, 'high_price': 7409.85, 'low_price': 7137.74,
        'last_price': 7329.97, 'datetime': datetime.datetime(2019, 12, 3, 10, 48, 50, 285000),
        'symbol': 'BTCUSDT'}, 2019-12-03 10:48:50.511381
        :return:
        """
        self.last_price = float(tick_data['last_price'])

        now = datetime.now()
        self.logger.info(f"strategy tick_data{now}")
        self.logger.info(f"{tick_data}, {now}")

        if self.trend_status == 1:  # 金叉的时候.
            if self.strategy_pos <= 0:  # 空仓，我就开多仓， 你有空头仓位，我就空头，然后开多头.

                pos = self.strategy_pos  # 获取未平仓的仓位. -0.2BTC + 0.2 + 0.2
                self.strategy_pos = self.trade_size  # 获取
                self.sync_data()
                volume = abs(pos) + abs(self.strategy_pos)
                # 下单的数量.
                if self.last_price > 0:
                    self.http_client.place_order(self.symbol,
                                                 side=OrderSide.BUY,
                                                 order_type=OrderType.LIMIT,
                                                 quantity=abs(volume),
                                                 price=self.last_price
                                                 )

        elif self.trend_status == -1:  # 死叉的时候.
            if self.strategy_pos >= 0:
                pos = self.strategy_pos
                self.strategy_pos = -self.trade_size  # 应该下单的仓位, 因为是死叉，所以需要的是做空，做空用负数表示.
                volume = abs(pos) + abs(self.strategy_pos)
                self.sync_data()
                if self.last_price > 0:
                    self.http_client.place_order(self.symbol,
                                                 side=OrderSide.SELL,
                                                 order_type=OrderType.LIMIT,
                                                 quantity=abs(volume),
                                                 price=self.last_price
                                                 )
    def on_open_orders(self, symbol):
        """
        获取到当前挂单没有成交的订单，用于撤单使用.
        :param symbol:
        :return:
        """
        open_orders = self.http_client.get_open_orders(symbol)
        if isinstance(open_orders, list):
            self.open_orders = open_orders  # 获取前的订单
            print(open_orders)

    def on_position(self, symbol):
        """
        获取到指定的symbol的仓位..
        :param symbol:
        :return:
        """
        pos_list = self.http_client.get_position_info()
        if isinstance(pos_list, list):
            for item in pos_list:
                if item['symbol'] == symbol:
                    self.pos_dict = item
                    self.logger.info(item)

    def check_position(self):

        if not self.pos_dict.get('positionAmt'):
            self.logger.info(f"没有获取到交易所仓位的信息: {self.pos_dict}")
            return

        exchange_pos = float(self.pos_dict['positionAmt'])  # 也是正负数的.
        strategy_pos = self.strategy_pos

        if strategy_pos != exchange_pos:  # 买1BTC,  0.5BTC
            amount = abs(strategy_pos-exchange_pos)
            if amount < self.min_volume or self.last_price <= 0:
                return

            if len(self.open_orders) > 0:  # 下单没有成交的订单撤销.
                for order in self.open_orders:
                    self.http_client.cancel_order(self.symbol, order_id=order['orderId'])

            amount = strategy_pos - exchange_pos
            # 策略， 1BTC ,  0.5BTC
            # 策略： 0.5BTC, 1BTC

            if amount >= self.min_volume:
                # 交易所的订单少，应该买.
                order = self.http_client.place_order(self.symbol,
                                                     side=OrderSide.BUY,
                                                     order_type=OrderType.LIMIT,
                                                     quantity=abs(amount),
                                                     price=self.last_price)

            elif amount <= -self.min_volume:
                order = self.http_client.place_order(self.symbol,
                                                     side=OrderSide.SELL,
                                                     order_type=OrderType.LIMIT,
                                                     quantity=abs(amount),
                                                     price=self.last_price)

    def sync_data(self):
        """
        同步策略的变量.
        :return:
        """
        for key in self.variables:
            self.json_data[key] = self.__getattribute__(key)

        save_json(self.file_name, self.json_data)

