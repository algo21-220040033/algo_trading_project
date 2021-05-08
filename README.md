# algo_trading_project
binance_trade
## 回测框架和策略

+ 框架内有四份文件：Code文件夹、data文件夹、main.py
+ Code文件夹：Backtest.py
+ data文件夹：data.csv，为比特币的K线数据
+ main.py：回测框架运行文件

### 回测框架说明

+ 点开main.py，修改对应参数（年化天数、交易费率、无风险利率、输入文件夹和文件名以及布林带策略的对应参数），运行得到结果
+ 输出结果为该策略下的：整体收益率、年化收益率、年化波动率、最大回撤以及起止时间、夏普比率和信息比率
+ 绘制出策略和基准的净值曲线图

### 策略说明

+ 采用的是布林带策略，回测区间为2018.1.1-2021.5.1
+ 当收盘价小于等于下轨时且持仓为0，买入1单位比特币
+ 当收盘价大于等于上轨时且持仓为1，卖出1单位比特币
+ 其他时候不做任何操作

## GUI说明

+ 基于vnpy框架的UI界面进行了修改
+ 添加了币安交易所的API
+ 下载GUI所有文件后，运行main_window.py后，点击链接binance，输入币安apikey和apisecret，使用其功能。

### 策略部署

+ 添加策略，命名策略名称，选择交易对代码，初始化，调整策略参数后，运行
+ 添加自己新写的策略可在strategies中增加文件

### 数据导入

+ 点击数据管理，导入数据，选择本地已调整好格式的csv文件
+ 也可从系统直接下载数据，速度较慢，大批量数据不推荐使用

## binance_trade(实盘交易无界面版）

+ 运行binance_main.py进行运行
+ 主要展示UI界面中各个功能api的运行情况
