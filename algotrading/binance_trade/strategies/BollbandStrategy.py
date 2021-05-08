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

class BollbandStrategy(object):
    """
    策略思路，盘中价格向上突破上轨就会做多, 在多头的情况下，价格跌破中轨轨就会平多头.
            盘中价格跌破下轨就做空，在空头持仓情况下，价格突破中轨就平掉空头.

    """

    variables = ["strategy_pos", 'boll_up', 'boll_dn', 'boll_mid']  #

    def __init__(self, http_client: BinanceFutureHttp, symbol='BTCUSDT', file_name=None):

        self.http_client = http_client
        self.symbol = symbol

        self.file_name = file_name if file_name else self.__class__.__name__
        self.json_data = load_json(self.file_name)

        self.strategy_pos = 0.0  # 给个默认的值
        self.boll_up = 0.0
        self.boll_dn = 0.0
        self.boll_mid = 0.0

        for key in self.variables:
            self.__setattr__(key, float(self.json_data.get(key, 0)))

        print(f"self.strategy_pos: {self.strategy_pos}")
        self.open_orders = []
        self.pos_dict = {}  # 默认的仓位信息.

        # 策略的参数.
        self.boll_window = 40  # 布林带的window
        self.boll_dev = 2.5  # 布林带的标准差倍数.
        self.trade_money = 1  # 10USDT.  每次交易的金额, 修改成自己下单的金额.
        self.min_volume = 0.001  # 最小的交易数量.
        self.trade_size = 0
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

        df['boll_up'], df['boll_mid'], df['boll_dn'] = talib.BBANDS(df['close'],
                                                                    timeperiod=self.boll_window,
                                                                    nbdevup=self.boll_dev,
                                                                    nbdevdn=self.boll_dev
                                                                    )

        current_bar = df.iloc[-1]  # 最新的K线 Bar.
        self.boll_up = round(float(current_bar['boll_up']), 2)
        self.boll_dn = round(float(current_bar['boll_dn']), 2)
        self.boll_mid = round(float(current_bar['boll_mid']), 2)

        # self.boll_dn = 7281.01  # 测试时候使用
        # self.boll_up = 7280  # 测试的时候使用.
        # self.boll_mid = 7000 # 测试的时候使用.

        if self.strategy_pos == 0:
            # 计算开仓的数量
            self.trade_size = round_to(self.trade_money / float(current_bar['close']), self.min_volume)
            if self.trade_size < self.min_volume:
                self.trade_size = self.min_volume

        self.sync_data()  # 保存临时变量的数据.

    def on_tick(self, tick_data):
        """
        拿到tick数据的方法.
        {'volume': 144748.226, 'open_price': 7397.99, 'high_price': 7409.85, 'low_price': 7137.74,
        'last_price': 7329.97, 'datetime': datetime.datetime(2019, 12, 3, 10, 48, 50, 285000),
        'symbol': 'BTCUSDT'}, 2019-12-03 10:48:50.511381
        :return:
        """
        now = datetime.now()
        self.logger.info(f"strategy tick_data{now}")
        self.logger.info(f"{tick_data}, {now}")

        if tick_data['symbol'] == self.symbol:  # 当前的tick数据的symbol跟策略是一致的.
            self.last_price = float(tick_data['last_price'])

            if self.boll_dn <= 0 or self.boll_mid <=0 or self.boll_up <= 0 or abs(self.trade_size) < self.min_volume or self.last_price <= 0:
                # 判断数据的正确性，策略的正确性.
                return

            if self.strategy_pos == 0:  # 没有仓位的时候
                if self.last_price > self.boll_up:  # 价格突破上轨.
                    self.strategy_pos = self.trade_size
                    self.sync_data()
                    # 做多.
                    price = self.last_price * (1+0.0003)  # 高于市场价格的万分之3,
                    price = round_to(price, 0.01)   # round(price, 2)

                    self.http_client.place_order(self.symbol,
                                                 side=OrderSide.BUY,
                                                 order_type=OrderType.LIMIT,
                                                 quantity=abs(self.strategy_pos),
                                                 price=price
                                                 )
                    # self.http_client.place_order(self.symbol,
                    #                              side=OrderSide.BUY,
                    #                              order_type=OrderType.LIMIT,
                    #                              quantity=abs(self.trade_size),
                    #                              price=price
                    #                              )

                elif self.last_price < self.boll_dn:  # 价格突破下轨.
                    self.strategy_pos = -self.trade_size  # 标记仓位的数据为空仓.
                    self.sync_data()  # 同步仓位的数据.

                    price = self.last_price * (1 - 0.0003)
                    price = round_to(price, 0.01)

                    self.http_client.place_order(self.symbol,
                                                 side=OrderSide.SELL,
                                                 order_type=OrderType.LIMIT,
                                                 quantity=abs(self.strategy_pos),
                                                 price=price
                                                 )
                    # self.http_client.place_order(self.symbol,
                    #                              side=OrderSide.SELL,
                    #                              order_type=OrderType.LIMIT,
                    #                              quantity=abs(self.trade_size),
                    #                              price=price
                    #                              )

            elif self.strategy_pos > 0:
                if self.last_price < self.boll_mid:
                    pos = self.strategy_pos
                    self.strategy_pos = 0  # 标记仓位为0
                    self.sync_data()  # 同步仓位的数据.

                    price = self.last_price * (1 - 0.0003)
                    price = round_to(price, 0.01)
                    self.http_client.place_order(self.symbol,
                                                 side=OrderSide.SELL,
                                                 order_type=OrderType.LIMIT,
                                                 quantity=abs(pos),
                                                 price=price
                                                 )

            elif self.strategy_pos < 0:
                if self.last_price > self.boll_mid:
                    pos = self.strategy_pos
                    self.strategy_pos = 0  # 设置仓位为空仓.
                    self.sync_data()  # 同步仓位数据.

                    # 下单平仓.
                    price = self.last_price * (1 + 0.0003)
                    price = round_to(price, 0.01)  # 保证价能够满足要求.
                    self.http_client.place_order(self.symbol,
                                                 side=OrderSide.BUY,
                                                 order_type=OrderType.LIMIT,
                                                 quantity=abs(pos),
                                                 price=price
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

