from pandas_datareader import data
import datetime
import pandas as pd
import numpy as np
import sqlite3 as sql
import os
from itertools import zip_longest
import time
from pandas.tseries.offsets import BDay
import matplotlib.pyplot as plt
import re
import math

#class BackTester(object):

#    def __init__(self, ticker, strategy, expiry, open_position, exit_position):
#        self.ticker = ticker
#        self.strategy = strategy
#        self.expiry = expiry
#        self.open_position = open_position
#        self.exit_position = exit_position

def iron_condor(ticker, expiry, open_date, close_date, aver_days, dis_bc = 2, center_strike=0):

    optionschain =[]
    mon_dict = {'Jan':'1','Feb':'2','Mar':'3','Apr':'4','May':'5','Jun':'6',
                'Jul':'7','Aug':'8','Sep':'9','Oct':'10','Nov':'11','Dec':'12'}

    conn = sql.connect('/home/youliang/computing/investing/OptionBackTester/OptionsChain.db')
    c = conn.cursor()

    #print('Back test Iron Condor','expiry',expiry,'open_date:',open_date,'close_date:',close_date)

    stock_price = data.DataReader(ticker, 'yahoo', open_date-datetime.timedelta(days=aver_days), open_date)
    if center_strike != 0:
        pass
    else:
        center_strike =  int(stock_price["Adj Close"][-1]) #int(stock_price["Adj Close"].mean()) # 20 day average as the strike price
    delta_strike= int((stock_price["Adj Close"].mad()))
    if delta_strike==0: delta_strike=1

    strike_a = int(center_strike)-dis_bc*delta_strike
    strike_b = int(center_strike)-0.5*dis_bc*delta_strike
    strike_c = int(center_strike)+0.5*dis_bc*delta_strike
    strike_d = int(center_strike)+dis_bc*delta_strike

    #print('center_strike:', center_strike, 'strikes:',(strike_a,strike_b,strike_c,strike_d))

    for row in c.execute('''select ticker, expiry_date, close_date, strike_price, call_mark, put_mark
                        from OptionsChain join Symbol join Expiry join Dates join Strike
                        on OptionsChain.symbol_id = Symbol.id and OptionsChain.expiry_id = Expiry.id and OptionsChain.date_id = Dates.id and OptionsChain.strike_id = Strike.id
                        order by OptionsChain.symbol_id, OptionsChain.date_id, OptionsChain.expiry_id, Strike.strike_price '''):

        a = re.split('; |, | ',row[1])
        date_tmp = datetime.date(int(a[2]), int(mon_dict[a[0]]), int(a[1]))
        if row[0] == ticker and date_tmp ==expiry and row[3] in range(int(center_strike*0.8),int(center_strike*1.2),1): # covering -20% to +20% of the current strike price
            optionschain.append(row)
            #print(row)

    open_price = 0
    close_price = 0

    for item in optionschain:
        if item[2]==str(open_date) and item[3]== strike_a:
            open_price = open_price + item[5]
            #print('open','at strike',item[3], item[5])
        if item[2]==str(open_date) and item[3]== strike_b:
            open_price = open_price - item[5]
            #print('open','at strike',item[3], item[5])
        if item[2]==str(open_date) and item[3]== strike_c:
            open_price = open_price - item[4]
            #print('open','at strike',item[3], item[4])
        if item[2]==str(open_date) and item[3]== strike_d:
            open_price = open_price + item[4]
            #print('open','at strike',item[3], item[4])

        if item[2]==str(close_date) and item[3]== strike_a:
            close_price = close_price + item[5]
            #print('close','at strike',item[3], item[5])
        if item[2]==str(close_date) and item[3]== strike_b:
            close_price = close_price - item[5]
            #print('close','at strike',item[3], item[5])
        if item[2]==str(close_date) and item[3]== strike_c:
            close_price = close_price - item[4]
            #print('close','at strike',item[3], item[4])
        if item[2]==str(close_date) and item[3]== strike_d:
            close_price = close_price + item[4]
            #print('close','at strike',item[3], item[4])

    print('Iron Condor','strikes:',(strike_a,strike_b,strike_c,strike_d), 'open:',open_price*100, 'close:',close_price*100, 'return:',(close_price-open_price)/math.fabs(open_price)*100,'%', '\n')

    return (close_price-open_price)/math.fabs(open_price)


def short_straddle(ticker, expiry, open_date, close_date, aver_days, center_strike=0):

    #print('Short Straddle','expiry',expiry,'open_date:',open_date,'close_date:',close_date)

    optionschain =[]
    mon_dict = {'Jan':'1','Feb':'2','Mar':'3','Apr':'4','May':'5','Jun':'6',
                'Jul':'7','Aug':'8','Sep':'9','Oct':'10','Nov':'11','Dec':'12'}

    conn = sql.connect('/home/youliang/computing/investing/OptionBackTester/OptionsChain.db')
    c = conn.cursor()

    stock_price = data.DataReader(ticker, 'yahoo', open_date-datetime.timedelta(days=aver_days), open_date)

    if center_strike != 0:
        pass
    else:
        center_strike = int(stock_price["Adj Close"][-1]) #int(stock_price["Adj Close"].mean()) # 20 day average as the strike price

    for row in c.execute('''select ticker, expiry_date, close_date, strike_price, call_mark, put_mark
                        from OptionsChain join Symbol join Expiry join Dates join Strike
                        on OptionsChain.symbol_id = Symbol.id and OptionsChain.expiry_id = Expiry.id and OptionsChain.date_id = Dates.id and OptionsChain.strike_id = Strike.id
                        order by OptionsChain.symbol_id, OptionsChain.date_id, OptionsChain.expiry_id, Strike.strike_price '''):

        a = re.split('; |, | ',row[1])
        date_tmp = datetime.date(int(a[2]), int(mon_dict[a[0]]), int(a[1]))
        if row[0] == ticker and date_tmp ==expiry and row[3] in range(int(center_strike*0.5),int(center_strike*1.5),1): # covering -50% to +50% of the current strike price
            optionschain.append(row)
            #print(row)

    open_price = 0
    close_price = 0

    for item in optionschain:
        if item[2]==str(open_date) and item[3]== center_strike:
            open_price = open_price -item[4] - item[5]
            #print('open','at strike',item[3], item[4], item[5])
        if item[2]==str(close_date) and item[3]== center_strike:
            close_price = close_price - item[4] - item[5]
            #print('close', item[4], item[5])

    print('Short Straddle','center_strike:', center_strike, 'open: $',open_price*100,'close: $',close_price*100,'return:',(close_price-open_price)/math.fabs(open_price)*100,'%', '\n')
    #print('return:',(close_price-open_price)/math.fabs(open_price)*100,'%', '\n')

    return (close_price-open_price)/math.fabs(open_price)



def short_strangle(ticker, expiry, open_date, close_date, aver_days, center_strike=0):

    #print('Short Strangle','expiry',expiry,'open_date:',open_date,'close_date:',close_date)

    optionschain =[]
    mon_dict = {'Jan':'1','Feb':'2','Mar':'3','Apr':'4','May':'5','Jun':'6',
                'Jul':'7','Aug':'8','Sep':'9','Oct':'10','Nov':'11','Dec':'12'}

    conn = sql.connect('/home/youliang/computing/investing/OptionBackTester/OptionsChain.db')
    c = conn.cursor()

    stock_price = data.DataReader(ticker, 'yahoo', open_date-datetime.timedelta(days=aver_days), open_date)
    if center_strike != 0:
        pass
    else:
        center_strike = int(stock_price["Adj Close"][-1]) #int(stock_price["Adj Close"].mean()) # 20 day average as the strike price

    delta_strike= int((stock_price["Adj Close"].mad()))
    if delta_strike==0: delta_strike=1

    #print('center_strike:', center_strike, 'delta_strike:',delta_strike)
#    print(stock_price["Adj Close"])
    for row in c.execute('''select ticker, expiry_date, close_date, strike_price, call_mark, put_mark
                        from OptionsChain join Symbol join Expiry join Dates join Strike
                        on OptionsChain.symbol_id = Symbol.id and OptionsChain.expiry_id = Expiry.id and OptionsChain.date_id = Dates.id and OptionsChain.strike_id = Strike.id
                        order by OptionsChain.symbol_id, OptionsChain.date_id, OptionsChain.expiry_id, Strike.strike_price '''):

        a = re.split('; |, | ',row[1])
        date_tmp = datetime.date(int(a[2]), int(mon_dict[a[0]]), int(a[1]))
        if row[0] == ticker and date_tmp ==expiry and row[3] in range(int(center_strike*0.8),int(center_strike*1.2),1): # covering -20% to +20% of the current strike price
            optionschain.append(row)
#            print(row)

    open_price = 0
    close_price = 0

    strike_a = int(center_strike)-delta_strike
    strike_b = int(center_strike)+delta_strike

    for item in optionschain:
        if item[2]==str(open_date) and item[3]== strike_a:
            open_price = open_price - item[5]
            #print('open','at strike',item[3], -item[5])
        if item[2]==str(open_date) and item[3]== strike_b:
            open_price = open_price - item[4]
            #print('open','at strike',item[3], -item[4])

        if item[2]==str(close_date) and item[3]== strike_a:
            close_price = close_price - item[5]
            #print('close','at strike',item[3],-item[5])
        if item[2]==str(close_date) and item[3]== strike_b:
            close_price = close_price - item[4]
            #print('close','at strike',item[3],-item[4])

    print('Short Strangle','strikes:',(strike_a,strike_b), 'open: $',open_price*100,'close: $',close_price*100,'return:',(close_price-open_price)/math.fabs(open_price)*100,'%', '\n')

    return (close_price-open_price)/math.fabs(open_price)


def spread(ticker, expiry, open_date, close_date, aver_days, center_strike=0, type='Call'):

    #print(type,'spread','expiry',expiry,'open_date:',open_date,'close_date:',close_date)

    optionschain =[]
    mon_dict = {'Jan':'1','Feb':'2','Mar':'3','Apr':'4','May':'5','Jun':'6',
                'Jul':'7','Aug':'8','Sep':'9','Oct':'10','Nov':'11','Dec':'12'}

    conn = sql.connect('/home/youliang/computing/investing/OptionBackTester/OptionsChain.db')
    c = conn.cursor()

    stock_price = data.DataReader(ticker, 'yahoo', open_date-datetime.timedelta(days=aver_days), open_date)
    if center_strike != 0:
        pass
    else:
        center_strike = int(stock_price["Adj Close"][-1]) #int(stock_price["Adj Close"].mean()) # 20 day average as the strike price

    delta_strike= int(stock_price["Adj Close"].mad())
    if delta_strike==0: delta_strike=1

    for row in c.execute('''select ticker, expiry_date, close_date, strike_price, call_mark, put_mark
                        from OptionsChain join Symbol join Expiry join Dates join Strike
                        on OptionsChain.symbol_id = Symbol.id and OptionsChain.expiry_id = Expiry.id and OptionsChain.date_id = Dates.id and OptionsChain.strike_id = Strike.id
                        order by OptionsChain.symbol_id, OptionsChain.date_id, OptionsChain.expiry_id, Strike.strike_price '''):

        a = re.split('; |, | ',row[1])
        date_tmp = datetime.date(int(a[2]), int(mon_dict[a[0]]), int(a[1]))
        if row[0] == ticker and date_tmp ==expiry and row[3] in range(int(center_strike*0.8),int(center_strike*1.2),1): # covering -20% to +20% of the current strike price
            optionschain.append(row)
#            print(row)

    open_price = 0
    close_price = 0

    strike_a = int(center_strike)-delta_strike
    strike_b = int(center_strike)+delta_strike

    for item in optionschain:
        if type=='Call':
            if item[2]==str(open_date) and item[3]== strike_a:
                open_price = open_price + item[4]
            if item[2]==str(open_date) and item[3]== strike_b:
                open_price = open_price - item[4]
            if item[2]==str(close_date) and item[3]== strike_a:
                close_price = close_price + item[4]
            if item[2]==str(close_date) and item[3]== strike_b:
                close_price = close_price - item[4]
        elif type=='Put':
            if item[2]==str(open_date) and item[3]== strike_a:
                open_price = open_price + item[5]
            if item[2]==str(open_date) and item[3]== strike_b:
                open_price = open_price - item[5]
            if item[2]==str(close_date) and item[3]== strike_a:
                close_price = close_price + item[5]
            if item[2]==str(close_date) and item[3]== strike_b:
                close_price = close_price - item[5]

    print(type,'spread','strikes:',(strike_a,strike_b), 'open: $',open_price*100,'close: $',close_price*100,'return:',(close_price-open_price)/math.fabs(open_price)*100,'%', '\n')

    return (close_price-open_price)/math.fabs(open_price)


if __name__ == '__main__':

    conn = sql.connect('/home/youliang/computing/investing/OptionBackTester/OptionsChain.db')
    c = conn.cursor()
    dates = []
    for row in c.execute('''select ticker, expiry_date, close_date, strike_price, call_mark, put_mark
                        from OptionsChain join Symbol join Expiry join Dates join Strike
                        on OptionsChain.symbol_id = Symbol.id and OptionsChain.expiry_id = Expiry.id and OptionsChain.date_id = Dates.id and OptionsChain.strike_id = Strike.id
                        order by OptionsChain.symbol_id, OptionsChain.date_id, OptionsChain.expiry_id, Strike.strike_price '''):
        if row[2] not in dates:
            dates.append(row[2])

    aver_days = 20
    expiry_date = datetime.date(2017,2,17)
    print(dates)
    for symbol in ['NVDA','BABA','FB','AAPL']:#,'TSLA','FB','BABA','AAPL']:#['INTC','AMD','NVDA','TSLA','FB','BABA','AAPL','AMZN','IBM','GLD','SPY','QQQ']
        print(symbol)
        center_strike = 0
        ssg = []
        ssd = []
        ic = []
        sp = []
        type = 'Put'
        for i in range(len(dates)-10,len(dates)-1):
            print(dates[i])
            open_date = datetime.date(int(dates[i][0:4]),int(dates[i][5:7]),int(dates[i][8:10]))
            close_date = datetime.date(int(dates[i+1][0:4]),int(dates[i+1][5:7]),int(dates[i+1][8:10])) # datetime.date(2017,1,idx[i+1])
            file = '/home/youliang/computing/investing/OptionBackTester/Data/'+symbol+'_all_money_'+str(open_date)+'_2.csv'
            if not os.path.isfile(file):
                print('equity '+symbol+': options chain at_'+str(open_date)+' not in database, please check!')
                break

            ssg.append(short_strangle(ticker = symbol, expiry=expiry_date, open_date = open_date, close_date = close_date,
                             aver_days=aver_days, center_strike=center_strike))
            ssd.append(short_straddle(ticker = symbol, expiry=expiry_date, open_date = open_date, close_date = close_date,
                             aver_days=aver_days, center_strike=center_strike))
            sp.append(spread(ticker = symbol, expiry=expiry_date, open_date = open_date, close_date = close_date,
                             aver_days=aver_days, center_strike=center_strike,type=type))
#            ic.append(iron_condor(ticker = symbol, expiry=expiry_date, open_date = open_date, close_date = close_date,
#                    aver_days=aver_days, dis_bc = 2, center_strike=center_strike))

#        open_date = datetime.date(2017,1,idx[0])
#        close_date = datetime.date(2017,1,idx[-1])
#        print('\n')
#        ssg_total = short_strangle(ticker = symbol, expiry=expiry_date, open_date = open_date, close_date = close_date,
#                             aver_days=aver_days, center_strike=center_strike)
#        ssd_total = short_straddle(ticker = symbol, expiry=expiry_date, open_date = open_date, close_date = close_date,
#                             aver_days=aver_days, center_strike=center_strike)
#        ic_total = iron_condor(ticker = symbol, expiry=expiry_date, open_date = open_date, close_date = close_date,
#                    aver_days=aver_days, dis_bc = 2, center_strike=center_strike)

        ssg = np.copy(ssg)
        ssd = np.copy(ssd)
        sp = np.copy(sp)
        ssg_total = (1+ssg.mean())**(len(ssg)-1)-1
        ssd_total = (1+ssd.mean())**(len(ssd)-1)-1
        sp_total = (1+sp.mean())**(len(sp)-1)-1
        print(symbol+' Summary')
        print('short strangle:',ssg,ssg_total,ssg.mean(),ssg.std(),ssg_total/ssg.std(),'\n')
        print('short straddle:',ssd,ssd_total,ssd.mean(),ssd.std(),ssd_total/ssd.std(),'\n')
        print('credit '+type+' spread:',sp,sp_total,sp.mean(),sp.std(),sp_total/sp.std(),'\n')
#        print((ssg_total,ssd_total,ic_total),(ssg.std(),ssd.std(),ic.std()))

        #get sharpo ratio for these three strategies
        open_date = datetime.date.today()
        stock_price = data.DataReader(symbol, 'yahoo', open_date-datetime.timedelta(days=aver_days), open_date)
        center_strike = stock_price["Adj Close"].mean()
        delta_strike= stock_price["Adj Close"].mad()
        print('Market Price', stock_price["Adj Close"][-1],'Average & S.T.D in last 30 days:',center_strike, delta_strike,'\n')

        plt.plot(ssg.tolist(), label=symbol+'ssg')
        plt.plot(ssd.tolist(), label=symbol+'ssd')
        plt.plot(sp.tolist(), label=symbol+'sp')
        plt.ylabel('return')
        plt.legend(bbox_to_anchor=(1.05, 1), loc=0)

    #plt.show()

#    ('NVDA', 'Feb 03, 2017', '2017-01-13', 100, 5.550000000000001, 2.1449999999999996)


