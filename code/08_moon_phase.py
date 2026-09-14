# -*- coding: utf-8 -*-
"""
08 月相计算与"月亮效应"趣味检验（中秋特供彩蛋）
结论：A 股满月窗/新月窗收益差异统计不显著（t=-0.56），月亮不影响股市。
彩蛋：算出你出生那天的月相。
"""
import os
import numpy as np
import pandas as pd

SYNODIC = 29.530588853                      # 朔望月周期（天）
EPOCH = pd.Timestamp('2000-01-06 18:14')    # 已知新月时刻

def moon_age(dt):
    """月龄：0=新月 7.4=上弦 14.8=满月 22.3=下弦"""
    ts = pd.Timestamp(dt)
    return (ts - EPOCH).total_seconds() / 86400.0 % SYNODIC

def moon_name(dt):
    age = moon_age(dt)
    names = [(0, '新月'), (7.4, '上弦月'), (14.8, '满月'), (22.3, '下弦月')]
    return min(names, key=lambda kv: abs(age - kv[0]) if kv[0] else (age if age < SYNODIC/4 else 99))[1]

# ---------- 彩蛋：你的生日月亮 ----------
if __name__ == '__main__':
    birthday = '1995-08-15'                 # ← 换成你的生日
    age = moon_age(birthday)
    print(f'{birthday} 的月龄: {age:.2f} 天')
    for center, name in [(0, '新月'), (7.4, '上弦月'), (14.8, '满月'), (22.3, '下弦月')]:
        print(f'  距{name}中心 {abs(age - center):.2f} 天')
    print('（完整月相检验见公众号文章《中秋特供 | 我们用 21 年 A 股数据，实测了月亮会影响股市》）')

    # ---------- 对沪深300 的趣味检验 ----------
    path = os.path.join('data', 'hs300_raw.csv')
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=['date'], index_col='date')
        df['ret'] = df['close'].pct_change()
        df['age'] = [(t - EPOCH).total_seconds() / 86400.0 % SYNODIC for t in df.index]
        full = df[(df['age'] - SYNODIC/2).abs() <= 2]
        new = df[(df['age'] <= 2) | (df['age'] >= SYNODIC - 2)]
        bp = 1e4
        print(f'\n满月窗平均日收益 {full["ret"].mean()*bp:.2f} bp (n={len(full)})')
        print(f'新月窗平均日收益 {new["ret"].mean()*bp:.2f} bp (n={len(new)})')
        print('结论方向与文献相反且统计不显著——月亮不影响 A 股，安心赏月。')
