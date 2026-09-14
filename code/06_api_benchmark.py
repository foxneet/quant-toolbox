# -*- coding: utf-8 -*-
"""
06 免费数据接口基准实测（数据接口横评配套）
实测（600519, 2024.1→2026.9, 649 根日线）：
  akshare·东财 0.39s 最快但当天重测断连；baostock 3.3s 稳定；
  通达信TQ 二次读取 0.038s；miniQMT 增量后读取 0.08s
工程原则：网页接口负责"搬"，本地接口负责"住"——数据最终落到自己硬盘
"""
import time
import pandas as pd

CODE_BAOSTOCK = 'sh.600519'
SYMBOL = '600519'
START, END = '2024-01-01', '2026-09-05'

def timed(name, fn):
    try:
        t0 = time.time()
        df = fn()
        print(f'[OK]   {name}: {time.time()-t0:.2f}s, {len(df)} rows')
        return df
    except Exception as e:
        print(f'[FAIL] {name}: {str(e)[:100]}')

# ---------- baostock ----------
def bs_test():
    import baostock as bs
    bs.login()
    rs = bs.query_history_k_data_plus(
        CODE_BAOSTOCK, 'date,open,high,low,close,volume',
        start_date=START, end_date=END, frequency='d', adjustflag='2')
    rows = []
    while rs.error_code == '0' and rs.next():
        rows.append(rs.get_row_data())
    bs.logout()
    return pd.DataFrame(rows, columns=rs.fields)

timed('baostock 日线前复权', bs_test)

# ---------- akshare 东财源（快，但稳定性看运气——务必加重试） ----------
def ak_em_test():
    import akshare as ak
    return ak.stock_zh_a_hist(symbol=SYMBOL, period='daily',
                              start_date=START.replace('-', ''),
                              end_date=END.replace('-', ''), adjust='qfq')

timed('akshare 东财源', ak_em_test)

# ---------- akshare 新浪源（慢一点，更稳） ----------
def ak_sina_test():
    import akshare as ak
    return ak.stock_zh_a_daily(symbol='sh' + SYMBOL,
                               start_date=START.replace('-', ''),
                               end_date=END.replace('-', ''), adjust='qfq')

timed('akshare 新浪源', ak_sina_test)

# ---------- miniQMT（需 QMT 客户端运行；增量下载后本地读取毫秒级） ----------
def xt_test():
    from xtquant import xtdata
    xtdata.download_history_data('600519.SH', period='1d',
                                 start_time=START.replace('-', ''),
                                 end_time=END.replace('-', ''))
    return xtdata.get_market_data_ex([], ['600519.SH'], period='1d',
                                     start_time=START.replace('-', ''),
                                     end_time=END.replace('-'))['600519.SH']

timed('miniQMT 增量下载+读取', xt_test)

# ---------- 通达信 TQ（需客户端运行；首次入库慢，二次读取 0.04s） ----------
def tq_test():
    import sys
    sys.path.insert(0, r'E:/TDX_ZL_ALLV2026/PYPlugins/user')  # 改成你的通达信目录
    from tqcenter import tq
    tq.initialize(__file__)
    data = tq.get_market_data(field_list=['Close'], stock_list=['600519.SH'],
                              period='1d', start_time='20240101',
                              end_time='20260905', dividend_type='front')
    df = tq.price_df(data, 'Close', column_names=['600519.SH'])
    tq.close()
    return df

# timed('通达信TQ（需客户端）', tq_test)   # 按需取消注释

print('\n工程原则：回测读本地库，实盘连本地接口，网页接口只做一次性补数据。')
print('完整横评结论见公众号文章《免费A股数据接口怎么选？》')
