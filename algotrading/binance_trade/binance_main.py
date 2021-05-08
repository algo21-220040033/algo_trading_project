"""
    声明：
    以下的视频和代码内容，只作为学习和研究使用，如果需要进行实盘交易，
    请您本人进行仔细测试和研究，如果使用该代码进行交易，造成的损失由个人承担全部责任
    51bitquant本人不保证所以的代码和交易思路的正确性. 谨慎使用.

    交易所链接:
    币安交易所链接：https://www.binance.com/en/register?ref=22795115
    bybit交易所链接：https://www.bybit.com/app/register?ref=yXjOz

    1.注意事项：
    1. 生成的API-key 要保管好，防止泄露，因为是期货交易，如果高杠杆的情况下，很容易爆仓
    2. 切记开仓的仓位数量过大, 开仓做好止损.
    3. 建议小资金测试，确认交易的策略能够盈利，且代码逻辑没有问题.

"""
from binance_trade.gateway.binance_ws import BinanceDataWebsocket
from binance_trade.gateway.binance_http import BinanceFutureHttp
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime
from binance_trade.strategies.DoubleEMAStrategy import DoubelEMAStrategy

import logging
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=format, filename='ema_strategy.txt')
logging.getLogger('apscheduler').setLevel(logging.WARNING)  # 设置apscheduler日记类型.

if __name__ == '__main__':

    key = "你的币安apikey"
    secret = '你的币安secret'
    binance = BinanceFutureHttp(key=key, secret=secret)

    symbol = 'BUSDUSDT'
    double_ema_strategy = DoubelEMAStrategy(http_client=binance, symbol=symbol)
    scheduler = BackgroundScheduler()


    # 子线程执行。
    binance_ws = BinanceDataWebsocket(on_tick_callback=double_ema_strategy.on_tick)
    binance_ws.subscribe("busdusdt")

    # scheduler在子线程里面执行.
    # 获取K线数据.
    scheduler.add_job(double_ema_strategy.on_1hour_kline_data, trigger='cron', args=(symbol,), hour='*/1')

    # 获取当前的挂单没有成交的订单.  30 秒请求一次.
    scheduler.add_job(double_ema_strategy.on_open_orders, trigger='cron', args=(symbol,), second='*/30')

    # 获取当前的仓位信息.
    scheduler.add_job(double_ema_strategy.on_position, trigger='cron', args=(symbol,), second='*/15')

    scheduler.start()

    #
    double_ema_strategy.on_1hour_kline_data(symbol)

    while True:
        double_ema_strategy.check_position()
        time.sleep(60)  # 2min.
        # 每两分钟需要检查下仓位信息, 检查订单有没有成交，
        # 是否符合自己的要求.


