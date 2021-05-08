# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import pandas_ta as ta
warnings.filterwarnings('ignore')

class Portfolio:
    def __init__(self, ann, fee_rate, rf, input_path, file, n, window):
        self.ann = ann
        self.fee_rate = fee_rate
        self.rf = rf
        self.input_path = input_path
        self.file = file
        self.n = n
        self.window = window
    #get the bitcoin data
    def data_read(self):
    	data = pd.read_csv(self.input_path+self.file, index_col = 0)
    	return data

    def trade_fee(self, volume):
    	fee = volume * self.fee_rate
    	return fee

    def strategy(self, data):
                
        data = data.reset_index()
        
        close = data.close
        standard_deviation = ta.stdev(close=close, length=self.window).fillna(0)
        mid = ta.sma(close=close, length=self.window).fillna(0) 

        data['boll_mid'] = mid
        data['boll_up'] = (mid + self.n * standard_deviation).shift(1).fillna(0)
        data['boll_down'] = (mid - self.n * standard_deviation).shift(1).fillna(0)
        
        data['flag'] = 0
        data['position'] = 0
        data['cash'] = 15000
        data['weight'] = 0
        position = 0
        
        for i in range(self.window+1,data.shape[0]-1):
            if data.loc[i,'close']<=data.loc[i,'boll_down'] and position == 0:
                data.loc[i,'flag'] = 1
                data.loc[i+1,'position'] = 1
                position = 1
                data.loc[i,'cash'] = data.loc[i-1,'cash'] - data.loc[i,'close']*1
                data.loc[i,'weight'] =  data.loc[i,'close']/(data.loc[i,'cash'] + data.loc[i,'close'])
            elif data.loc[i,'close']>=data.loc[i,'boll_up'] and position == 1:
                data.loc[i,'flag'] = -1
                data.loc[i+1,'position'] = 0
                position = 0
                data.loc[i,'cash'] = data.loc[i-1,'cash'] + data.loc[i,'close']*1
                data.loc[i,'weight'] =  0
            else:
                data.loc[i+1,'position'] = data.loc[i,'position']
                data.loc[i,'cash'] = data.loc[i-1,'cash'] 
                data.loc[i,'weight'] = (data.loc[i+1,'position'] * data.loc[i,'close'])/(data.loc[i,'cash'] + data.loc[i,'close'])
        
        data['net'] =(1+data.close.pct_change(1).fillna(0) * data.weight.shift(1)).cumprod()
        data.index = data.datetime
        net = data['net']
        net = net.fillna(1)
        return net

    def data_clean(self, data, net):
        networth = net
        data.index = pd.to_datetime(data.index)
        data['daily'] = networth.diff()/networth.shift(1)
        data['net_worth'] = networth
        data['m_daily'] = data['close'].diff()/data['close'].shift(1)
        return data

    def wholeR(self, data):
        p = data['net_worth']
        wr = (p.iloc[-1]-p.iloc[0])/p.iloc[0]
        return wr

    def annualR(self, data):
        r = self.wholeR(data)
        r_p = ((1+r)**(self.ann/data['daily'].count())-1)
        return r_p

    def annualV(self, data):
        s = np.nansum((data['daily']-np.mean(data['daily']))**2)
        V = np.sqrt(self.ann*s/(data['daily'].count()-1))
        return V
    
    def max_dd(self, returns):
        #计算每天的累计收益
        r = (returns+1).cumprod()
        #r.cummax()计算出累计收益的最大值，再用每天的累计收益除以这个最大值，算出收益率
        dd = r.div(r.cummax()).sub(1)
        #取最小
        mdd = dd.min()
        end = dd.idxmin()
        #end = end.date()
        start = r.loc[:end].idxmax()
        #start = start.date()
        return -mdd, start, end

    #计算夏普比率
    def sharpe(self, data):
        r_p = self.annualR(data)
        V = self.annualV(data)
        sharpe =(r_p - self.rf)/V
        return sharpe

    def info_ratio(self, data):
        r =(data['close'].iloc[-1]-data['close'].iloc[0])/data['close'].iloc[0]
        r_p = self.annualR(data)
        s = np.nansum((data['daily']-np.mean(data['daily']))**2)
        r_m = ((1+r)**(self.ann/data['m_daily'].count())-1)
        Vt = np.sqrt(self.ann*s/(data['daily'].count()-1))
        IR = (r_p - r_m)/Vt
        return IR

    def output(self, data, net):
        networth = net
        networth.name = 'strategy'
        price = data['close']
        price = price/price.iloc[0]
        price.name = 'benchmark'
        price = pd.concat([price, networth], axis =1)
    	
        plt.clf()
        plt.rcParams['font.sans-serif']=['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        #fig, ax = plt.subplots()
        price.plot(figsize=(12,6),color = ['tab:red','tab:blue'],rot = 0,
                linewidth=1.0)
        plt.title('net-worth',size=15)
        plt.legend(loc='upper left')
        ax = plt.axes()
        x_axis = ax.axes.get_xaxis()
        x_axis.set_label_text('time')
        y_axis = ax.axes.get_yaxis()
        y_axis.set_label_text('net-worth')
        return True
        
    def backtest(self):
        data = self.data_read()
        net = self.strategy(data)
        data = self.data_clean(data, net)
        
        wholeR = self.wholeR(data)
        wholeR = "%.2f%%" % (wholeR * 100)
        annualR = self.annualR(data)
        annualR = "%.2f%%" % (annualR * 100)
        annualV = self.annualV(data)
        annualV = "%.2f%%" % (annualV * 100)
        mdd, start, end = self.max_dd(data['daily'])
        mdd = "%.2f%%" % (mdd * 100)
        sharpe = round(self.sharpe(data),2)
        IR = round(self.info_ratio(data),2)
        
        print('The overall return is: ', wholeR)
        print('The annual return is: ', annualR)
        print('The annual volatility is:',annualV)
        print('The max drawdown is:', mdd)
        print('The start time of mdd is:', start)
        print('The end time of mdd is:', end)
        print('The sharpe is:', sharpe)
        print('The Information-Ratio is:', IR)
        
        self.output(data, net)
        return True
        
        
        
        
        