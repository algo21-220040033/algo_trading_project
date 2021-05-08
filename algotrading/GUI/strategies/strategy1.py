from howtrader.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager
)

from howtrader.trader.constant import Interval
from datetime import datetime
from howtrader.app.cta_strategy.engine import CtaEngine, EngineType
import pandas_ta as ta
import pandas as pd


class Strategy1(CtaTemplate):
    """
    做市
    """
    fixed_trade_money = 1000  # 每次定投的资金比例.
    buy_signal=0.9995
    sell_signal=1.0005

    parameters = ['fixed_trade_money', 'buy_signal','sell_signal']

    def __init__(self, cta_engine: CtaEngine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg_1hour = BarGenerator(self.on_bar, 1, self.on_1hour_bar, Interval.HOUR)
        self.am = ArrayManager(size=100)  # 时间序列，类似我们用的pandas, 值保留最近的N个K线的数据.

    def on_init(self):
        """
        Callback when strategies is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(1)  # 具体加载多少天的数据, 1表示1天的数据，如果是2表示过去2天的数据

    def on_start(self):
        """
        Callback when strategies is started.
        """
        self.write_log(f"我的策略启动")
        self.put_event()


    def on_stop(self):
        """
        Callback when strategies is stopped.
        """
        self.write_log("策略停止")
        self.put_event()


    def on_tick(self, tick: TickData):
        pass

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_1hour.update_bar(bar)  # 合成1小时的数据.
        self.put_event()

    def on_1hour_bar(self, bar: BarData):
        """
        四小时的K线数据.
        """
        # self.cancel_all()  # 撤销所有订单.
        self.am.update_bar(bar)  # 把最新的K线放进时间序列里面.
        # 下面可以计算基数指标等等....
        # 以及下单的事情.

        if not self.am.inited:
            return

        # [0,1,2,3,4,5,6]
        last_close_price = self.am.close_array[-2]  # 上一根K线
        current_close_price = bar.close_price # self.am.close_array[-1] #  当前的收盘价

        # 如果四小时价格下跌5%就买入.
        if  current_close_price <= self.buy_signal:
            price = bar.close_price
            self.buy(price, self.fixed_trade_money/price)

        self.put_event()

        if  current_close_price >= self.sell_signal:
            price = bar.close_price
            self.sell(price, self.fixed_trade_money/price)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        订单的回调方法: 订单状态更新的时候，会调用这个方法。
        """
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        """
        self.put_event()  # 更新UI界面方法。


    def on_stop_order(self, stop_order: StopOrder):
        """
        这个是一个停止单的方法，用来监听你止损单的方法。
        """
        pass

