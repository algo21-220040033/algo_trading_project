"""

"""
import json
from datetime import datetime

from binance_trade.gateway.base_websocket import BaseWebsocket
from binance_trade_event.event import EventEngine, Event


class BinanceDataWebsocket(BaseWebsocket):
    def __init__(self, ping_interval=20,on_tick_callback=None):
        # self.event_engine = event_engine  # 事件引擎.

        host = "wss://stream.binance.com:9443/stream?streams="
        super(BinanceDataWebsocket, self).__init__(host=host, ping_interval=ping_interval)
        self.on_tick_callback=on_tick_callback

        self.symbols = set()
        self.symbols.add('busdusdt')

    def on_open(self):
        print(f"websocket open at:{datetime.now()}")

    def on_close(self):
        print(f"websocket close at:{datetime.now()}")

    def on_msg(self, data: str):
        json_msg = json.loads(data)

        stream = json_msg["stream"]
        # print(stream)
        data = json_msg["data"]
        # print(data)
        symbol, channel = stream.split("@")

        # print(symbol)
        # print(channel)

        if channel == 'ticker':
            ticker = {"volume": float(data['v']),
                        "open_price":float(data['o']),
                        "high_price": float(data['h']),
                        "low_price": float(data['l']),
                        "last_price": float(data['c']),
                        "datetime": datetime.fromtimestamp(float(data['E']) / 1000),
                        "symbol": symbol.upper()
                        }

            # event = Event('tick', ticker)  # 初始化一个事件.
            # self.event_engine.put(event)  # 把它放进队列中，或者说把这个事件放进事件驱动(循环)系统中

            if self.on_tick_callback:
                self.on_tick_callback(ticker)  # event_egine.put(event)

    # def on_error(self, exception_type: type, exception_value: Exception, tb):
    #     print(f"websocket触发异常，状态码：{exception_type}，信息：{exception_value}")

    def subscribe(self, symbol):

        self.symbols.add(symbol)
        if self._active:
            self.stop()
            self.join()

        channels = []

        for symbol in self.symbols:
            channels.append(symbol.lower()+"@ticker")
            # channels.append(symbol.lower()+"@depth5")
            # <symbol>@depth<levels

        self.host += '/'.join(channels)
        print(self.host)
        self.start()

def test(data):
    print(data)

if __name__ == '__main__':
    ws = BinanceDataWebsocket(on_tick_callback=test)
    ws.subscribe('busdusdt')

