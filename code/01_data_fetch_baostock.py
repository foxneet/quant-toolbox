# -*- coding: utf-8 -*-
"""
01 数据获取：baostock 拉取沪深300 全量日线
实测：5265 个交易日（2005-01 → 2026-09），约 3.3 秒
"""
import os
import baostock as bs
import pandas as pd

# ============ 配置 ============
CODE = 'sh.000300'            # 沪深300 指数
START, END = '2005-01-01', '2026-09-30'
FIELDS = 'date,open,high,low,close,volume,amount,turn,pctChg'
DATA_DIR = 'data'

# ============ 拉取 ============
def fetch(code=CODE, start=START, end=END, adjustflag='3'):
    """adjustflag: 1=后复权 2=前复权 3=不复权"""
    lg = bs.login()
    rs = bs.query_history_k_data_plus(
        code, FIELDS, start_date=start, end_date=end,
        frequency='d', adjustflag=adjustflag)
    rows = []
    while rs.error_code == '0' and rs.next():
        rows.append(rs.get_row_data())
    bs.logout()
    df = pd.DataFrame(rows, columns=rs.fields)
    for c in df.columns:
        if c != 'date':
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date').sort_index()

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    for flag, name in [('3', 'raw'), ('2', 'qfq'), ('1', 'hfq')]:
        df = fetch(adjustflag=flag)
        path = os.path.join(DATA_DIR, f'hs300_{name}.csv')
        df.to_csv(path)
        print(f'{name}: {len(df)} 行 → {path}')
    print('完成。注意：当日数据一般 19:00 后才更新。')
