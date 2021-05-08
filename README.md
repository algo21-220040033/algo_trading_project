# algo_trading_project
binance_trade
## 回测框架和策略

+ 框架内有四份文件：Code文件夹、data文件夹、main.py
+ Code文件夹：Backtest.py
+ data文件夹：data.csv，为比特币的K线数据【由于上传限制，无法上传2018.1.1-2021.5.1全部数据，上传2021.1.1-2021.1.15数据为例】
+ main.py：回测框架运行文件

### 回测框架说明

+ 点开main.py，修改对应参数（年化天数、交易费率、无风险利率、输入文件夹和文件名以及布林带策略的对应参数），运行得到结果
+ 输出结果为该策略下的：整体收益率、年化收益率、年化波动率、最大回撤以及起止时间、夏普比率和信息比率
+ 绘制出策略和基准的净值曲线图

### Howtrader回测框架修改说明

single_backtesting.py用于howtrader内部的策略回测；同样也用于检验我们自己的回测系统

### 策略说明

+ 采用的是布林带策略，回测区间以2021.1.1-2021.1.15为例
+ 当收盘价小于等于下轨时且持仓为0，买入1单位比特币
+ 当收盘价大于等于上轨时且持仓为1，卖出1单位比特币
+ 其他时候不做任何操作

![image](https://user-images.githubusercontent.com/80995891/117527872-bac72000-b001-11eb-93b0-0d81b0297367.png)

## GUI说明

+ 基于vnpy框架的UI界面进行了修改
+ 添加了币安交易所的API
+ 下载GUI所有文件后，运行main_window.py后，点击链接binance，输入币安apikey和apisecret，使用其功能。

### 策略部署

+ 添加策略，命名策略名称，选择交易对代码，初始化，调整策略参数后，运行
+ 添加自己新写的策略可在strategies中增加文件

### 数据导入直接版本

+ 点击数据管理，导入数据，选择本地已调整好格式的csv文件
+ 也可从系统直接下载数据，速度较慢，大批量数据不推荐使用


### 数据导入code版本

data_imp.py 用于将本地csv格式数据导入到VN trader的数据管理器中: 呈现格式为```.db (SQLite)```

(1) howtrader.trader.object里的BarData: record Candlestick bar data of a certain trading period.

(2) howtrader.trader.database里的database_manager.save_bar_data: 存储Sequence of "BarData"

(3) howtrader.trader.constant里的(Exchange,Interval)：主要用于标准化语句：Exchange.BINANCE="BINANCE"; Interval.MINUTE: csv数据为分钟数据


## binance_trade(实盘交易无界面版）

+ 运行binance_main.py进行运行
+ 主要展示UI界面中各个功能api的运行情况


## Howtrader中重要的基础设置类

trader -> howtrader.trader: 对VN Trader中的变量做基础设置

(1) .constant: General constant string used in VN Trader -> *Direction、Offset、Status、Product、OrderType、OptionType、Currency、Exchange、Interval*
       
(2) .object: ```Basic data structure``` used for general trading function in VN Trader -> *父类：BaseData; 子类: TickData、BarData、OrderData、TradeData...*

...
