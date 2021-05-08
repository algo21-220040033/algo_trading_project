import os
import csv
from datetime import datetime, time

from howtrader.trader.constant import (Exchange,Interval)
from howtrader.trader.database import database_manager
from howtrader.trader.object import BarData

def csv_load(file):
    """
    读取csv文件内容，并写入到数据库中
    """
    with open(file, "r") as f:
        reader = csv.DictReader(f) # DictReader会将第一行的内容（类标题）作为key值，第二行开始才是数据内容; 一行一行的进行读取

        bar = []
        start = None
        count = 0

        for item in reader:

            # generate datetime
            date = item["datetime"]

            dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

            bars = BarData(
                symbol="btcusdt",
                datetime=dt,
                exchange=Exchange.BINANCE,
                interval=Interval.MINUTE,
                open_price=float(item['open']),
                high_price=float(item['high']),
                low_price=float(item['low']),
                close_price=float(item['close']),
                volume=float(item["volume"]),
                gateway_name="BINANCE",
            )
            bar.append(bars)

            # do some statistics
            count += 1
            if not start:
                start = bars.datetime

        end = bars.datetime
        database_manager.save_bar_data(bar)

        print("插入数据", start, "-", end, "总数量：", count)

file = "D:/MFE/project/AIgo Trading/howtrader/data.csv"
csv_load(file)