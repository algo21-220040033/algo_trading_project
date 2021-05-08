# -*- coding: utf-8 -*-
"""
Created on Fri May  7 20:23:43 2021

@author: Liran CHEN 220040071
"""
from Code.Backtest import Portfolio

def main():
    """
    ann : 年化时考虑的天数
    fee_rate : 交易费率
    rf : 无风险利率
    input_path : 输入文件夹地址
    file : 输入数据文件名
    """
    ann = 250
    fee_rate = 0#0.0003
    rf = 0
    input_path = r'./data/'
    file = r'data.csv'
    

    n=5
    window=80
    
    pb = Portfolio(ann, fee_rate, rf, input_path, file,n,window)
    pb.backtest()
    
    

if __name__ == "__main__":
    main()
