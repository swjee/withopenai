import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from CoinInvest import DBRead

from audioplayer import AudioPlayer
from navertts import NaverTTS

import ctypes

#거래량에 대한 볼린저밴드생성.

def play(text):
    tts = NaverTTS(text)
    tts.save('alert3_gal.mp3')
    AudioPlayer('alert3_gal.mp3').play(block=True)


print ('test DBREAD')

# 1m, 3m, 5m, 10m, 30m, 1h, 6h, 12h, 24h

interval_list = ['1m', '3m', '5m', '10m', '30m', '1h', '6h', '12h', '24h' ]
delay_sec= {'1m': 60 , '3m': 180 , '5m': 300 , '10m': 600 , '30m': 1800 ,
                       '1h': 3600 , '6h': 21600 , '12h': 43200 , '24h': 86400  }
last_updated= {'1m': 0 , '3m': 0 , '5m': 0 , '10m': 0 , '30m':  0 ,
            '1h': 0 , '6h': 0 , '12h':  0 , '24h':  0}

PB_UP_TH = 0.8
PB_DW_TH = 0.2
MFI_UP_TH =70
MFI_DW_TH =20
while True:
    dbu = DBRead.DBReader()
    df = dbu.read_xrp(coin_type='XRP')
    fig = plt.figure(figsize=(24, 16) )

    df['MA20'] = df['close'].rolling(window=20).mean()
    df['stddev'] = df['close'].rolling(window=20).std()
    df['upper']  = df ['MA20'] + ( df['stddev']*2)
    df['lower']= df ['MA20'] - ( df['stddev']*2)
    df['PB'] =  ( df['close'] - df['lower']) / (df['upper'] - df['lower'])
    df['bandwidth'] = (df['upper'] - df['lower'] ) / df['MA20'] * 100
# Volume Bol
    df['V_MA20'] = df['volume'].rolling(window=20).mean()
    df['V_stddev'] = df['volume'].rolling(window=20).std()
    df['V_upper']  = df ['V_MA20'] + ( df['V_stddev']*2)
    df['V_lower']= df ['V_MA20'] - ( df['V_stddev']*2)
    df['V_PB'] =  ( df['volume'] - df['V_lower']) / (df['V_upper'] - df['V_lower'])
    df['V_bandwidth'] = (df['V_upper'] - df['V_lower'] ) / df['V_MA20'] * 100
    df['SQRT_PB_VPB'] = np.sqrt( df['PB']*df['V_PB'])
    df['SQRT_BW'] = np.sqrt( df['V_bandwidth']*df['bandwidth']) / 100
    df['SQRT_BWCHG'] = df['SQRT_BW'].pct_change(periods = 2)

 
    #MFI
    df['TP'] = ( df['high'] + df['low'] + df['close'] ) /3
    df['PMF'] = 0
    df['NMF'] = 0

    #II ( Intraday Intensity)

    df['II'] = (2*df['close'] - df['high'] - df['low']) / ( df['high'] - df['low']) * df['volume']
    df['IIP21'] = df['II'].rolling(window=21).sum()/df['volume'].rolling(window=21).sum()*100

    df = df.dropna()

    for i in range( len(df.close) -1 ):
        if df.TP.values[i] < df.TP.values[i+1]:
            df.PMF.values[i+1]=df.TP.values[i+1]*df.volume.values[i+1]
            df.NMF.values[i+1] = 0
        else:
            df.NMF.values[i+1]=df.TP.values[i+1]*df.volume.values[i+1]
            df.PMF.values[i+1] = 0

    df['MFR'] = df.PMF.rolling( window= 10).sum()/ df.NMF.rolling(window=10).sum()
    df['MFI10']= 100-100/( 1+ df['MFR'])
    df=df[19:]

    plt.subplot(4, 1, 1)
    plt.title('XRP')
    plt.plot(df.index, df['close'],  color='#0000ff',label='Close')
    plt.plot(df.index, df['upper'], 'r--', color='r',label='Upper')
    plt.plot(df.index, df['MA20'], 'k--', color='b',label='MA20')
    plt.plot(df.index, df['lower'], 'c--', color='g',label='Lower')

    for i in range(len(df.close) - 1):

        if df.PB.values[i] < 0.1 and df.IIP21.values[i]>0 :
            plt.plot(df.index.values[i], df.close.values[i], 'k^')
            if i > len(df.close) - 3:
                #ctypes.windll.user32.MessageBoxW(0, "반전 매수타이밍.!", "알림", 1)
                play("반전 매수 타이밍입니다.")
        elif df.PB.values[i] > 0.9 and df.IIP21.values[i]<0 :
            plt.plot(df.index.values[i], df.close.values[i], 'yv')
            if i > len(df.close) - 3 :
                #ctypes.windll.user32.MessageBoxW(0, "반전 매도타이밍.!", "알림", 1)
                play("반전 매도 타이밍입니다.")


        if  df.PB.values[i] > PB_UP_TH and df.MFI10.values[i] > MFI_UP_TH:
            plt.plot( df.index.values[i],df.close.values[i],'r^')
            if i > len(df.close) - 3:
                #ctypes.windll.user32.MessageBoxW(0, "매수추세!", "알림", 1)
                play("매수 추세!.")
        elif df.PB.values[i] < PB_DW_TH and df.MFI10.values[i] < MFI_DW_TH :
            plt.plot( df.index.values[i],df.close.values[i],'bv')
            if i > len(df.close) - 3:
                #ctypes.windll.user32.MessageBoxW(0, "매도추세!", "알림", 1)
                play("매도 추세!.")


        if i > len(df.close) - 3:
            if df.SQRT_BWCHG.values[i] > 0.15 and df.II.values[i] > 0:
                    play("급등 추세!.")

            elif df.SQRT_BWCHG.values[i] > 0.15 and df.II.values[i] < 0:
                    play("급락 추세!.")

    plt.legend(loc='upper left')
    plt.grid(True)


    plt.subplot(4,1,2)
    plt.title('PB&MFI')
    plt.plot(df.index, df['PB']*100,  color='b',label='%B * 100')
    plt.plot(df.index, df['MFI10'], 'g--',label='MFI 10 DAY')


    for i in range(len(df.close) - 1):
        if df.PB.values[i] > PB_UP_TH and df.MFI10.values[i] > MFI_UP_TH:
            plt.plot(df.index.values[i], 0 , 'r^')
        elif df.PB.values[i] < PB_DW_TH and df.MFI10.values[i] < MFI_DW_TH:
            plt.plot(df.index.values[i], 0 , 'bv')

    plt.legend(loc='upper left')
    plt.grid(True)


#volume BOL
    plt.subplot(4, 1, 3)
    plt.title('VOL_BOL')
    plt.plot(df.index, df['volume'],  color='k',label='volume')
    plt.plot(df.index, df['V_upper'], 'r--', color='r',label='V_Upper')
    plt.plot(df.index, df['V_MA20'], 'k--', color='b',label='V_MA20')
    plt.plot(df.index, df['V_lower'], 'c--', color='g',label='V_Lower')

    plt.legend(loc='upper left')
    plt.grid(True)

#    #  II%.. plot
#    plt.subplot(4,1,3)
#    plt.title('IIP21')
#    plt.plot(df.index, df['IIP21'],  color='g',label='II% 21day')
#
#    for i in range(len(df.close) - 1):
#        if df.PB.values[i] < 0.1 and df.IIP21.values[i] > 0:
#            plt.plot(df.index.values[i], 0 , 'r^')
#        elif df.PB.values[i] > 0.9 and df.IIP21.values[i] < 0:
#            plt.plot(df.index.values[i], 0 , 'bv')
#

    plt.legend(loc='upper left')
    plt.grid(True)

    #  volume.. plot
    plt.subplot(4,1,4)
    plt.title('V_BW*BW')
#    plt.plot(df.index, df['V_PB'],  color='k',label='V_PB')
#    plt.plot(df.index, df['PB'],  color='b',label='PB')
    plt.plot(df.index, df['SQRT_BW'],  color='k',label='SQRT BW*BBW')
    if df.SQRT_BWCHG.values[len(df.SQRT_BWCHG)-1] >=0 :
        plt.plot(df.index, df['SQRT_BWCHG'],  color='r',label='SQRT BWCHG')
    else:
        plt.plot(df.index, df['SQRT_BWCHG'],  color='b',label='SQRT BWCHG')


    plt.legend(loc='upper left')
    plt.grid(True)


    plt.pause(10)
    plt.close()
