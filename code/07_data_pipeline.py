# -*- coding: utf-8 -*-
"""
07 数据管道（AI 投研系统 ②）
四道工序：①统一适配器 → ②质检 → ③parquet 落库 → ④增量更新
工程原则：接口只是搬运工，本地 parquet 库才是资产
"""
import os
import numpy as np
import pandas as pd

DATA_DIR = 'data_parquet'
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- ① 适配器：多接口统一成标准格式 ----------
# 标准格式: DataFrame[date(DatetimeIndex), open, high, low, close, volume]

def fetch_baostock(code, start, end):
    """code 格式: sh.600519"""
    import baostock as bs
    bs.login()
    rs = bs.query_history_k_data_plus(
        code, 'date,open,high,low,close,volume',
        start_date=start, end_date=end, frequency='d', adjustflag='3')
    rows = []
    while rs.error_code == '0' and rs.next():
        rows.append(rs.get_row_data())
    bs.logout()
    df = pd.DataFrame(rows, columns=rs.fields)
    df['date'] = pd.to_datetime(df['date'])
    for c in ['open', 'high', 'low', 'close', 'volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df.set_index('date')

def fetch_akshare_em(code, start, end):
    """code 格式: 600519"""
    import akshare as ak
    df = ak.stock_zh_a_hist(symbol=code, period='daily',
                            start_date=start.replace('-', ''),
                            end_date=end.replace('-', ''), adjust='')
    df = df.rename(columns={'日期': 'date', '开盘': 'open', '最高': 'high',
                            '最低': 'low', '收盘': 'close', '成交量': 'volume'})
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date')[['open', 'high', 'low', 'close', 'volume']]

FETCHERS = {'baostock': fetch_baostock, 'akshare': fetch_akshare_em}

def get_daily(code_std, source='baostock', start='2020-01-01', end='2026-09-30'):
    """统一入口：code_std 格式 600519.SH"""
    num, mkt = code_std.split('.')
    if source == 'baostock':
        raw = f'{mkt.lower()}.{num}'
    else:
        raw = num
    return FETCHERS[source](raw, start, end)

# ---------- ② 质检：四项检查 ----------
def qc(df, code):
    problems = []
    # 1 异常涨跌幅（>±21%）
    pct = df['close'].pct_change()
    bad = pct[abs(pct) > 0.21]
    if len(bad):
        problems.append(f'异常涨跌幅 {len(bad)} 天: {list(bad.index.strftime("%Y-%m-%d"))[:5]}')
    # 2 空值
    if df[['close', 'volume']].isna().any().any():
        problems.append('存在空值')
    # 3 零成交量（非停牌标记的话是异常）
    zero_vol = (df['volume'] == 0).sum()
    if zero_vol > 0:
        problems.append(f'零成交量 {zero_vol} 天（需确认是否停牌）')
    # 4 重复日期
    if df.index.duplicated().any():
        problems.append('存在重复日期')
    return problems

# ---------- ③④ 落库 + 增量更新 ----------
def _path(code):
    return os.path.join(DATA_DIR, f'{code}.parquet')

def update(code_std, source='baostock', start='2020-01-01'):
    """增量更新：只拉本地缺的那段，绝不整段重拉"""
    path = _path(code_std)
    if os.path.exists(path):
        local = pd.read_parquet(path)
        fetch_from = (local.index.max() + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        new = get_daily(code_std, source, fetch_from, '2026-09-30')
        merged = pd.concat([local, new])
        merged = merged[~merged.index.duplicated()].sort_index()
    else:
        merged = get_daily(code_std, source, start, '2026-09-30')
    merged.to_parquet(path)

    problems = qc(merged, code_std)
    print(f'{code_std}: {len(merged)} 行 | 质检: {"通过" if not problems else problems}')
    return merged

if __name__ == '__main__':
    update('600519.SH', source='baostock')
    # 回测读本地：pd.read_parquet('data_parquet/600519.SH.parquet')
    print('\n原则：回测读本地（毫秒级），实盘连本地接口，网页接口只补数据。')
