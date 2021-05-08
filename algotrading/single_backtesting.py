'''
用于howtrader内部策略的回测以及可视化
'''


from howtrader.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from examples.strategies.atr_rsi_strategy import AtrRsiStrategy
from examples.strategies.boll_channel_strategy import BollChannelStrategy
from datetime import datetime


def run_backtesting(strategy_class, setting, vt_symbol, interval, start, end, rate, slippage, size, pricetick, capital):
    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        end=end,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital
    )
    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    return df

def show_portafolio(df):
    engine = BacktestingEngine()
    engine.calculate_statistics(df)
    engine.show_chart(df)


df = run_backtesting(
    strategy_class=AtrRsiStrategy,
    setting={},
    vt_symbol="btcusdt.BINANCE",
    interval="1m",
    start=datetime(2020, 1, 1),
    end=datetime(2020, 2, 28),
    rate=0.3/10000,
    slippage=0.2,
    size=300,
    pricetick=0.2,
    capital=1_000_000,
    )


show_portafolio(df)