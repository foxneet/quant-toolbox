# -*- coding: utf-8 -*-
"""
05 RSRS 择时实测（中秋前系列 / 公众号实测文）
结论：训练段(2005-2017)年化 26.7% 吊打市场；测试段(2017.6 后)年化 1.7% 跑输持有。
方法：滚动 18 日 OLS(最高价~最低价) 斜率 → 600 日 Z-Score 标准分
     标准分 >0.7 持有，<-0.7 空仓；信号 T+1 执行
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_PATH = os.path.join('data', 'hs300_raw.csv')
N, M = 18, 600
COST = 0.001

df = pd.read_csv(DATA_PATH, parse_dates=['date'], index_col='date')
df['pct'] = df['close'].pct_change().fillna(0)

# 滑窗 OLS（向量化闭式解）
def rolling_rsrs(high, low, n):
    h, l = high.values, low.values
    hw = np.lib.stride_tricks.sliding_window_view(h, n)
    lw = np.lib.stride_tricks.sliding_window_view(l, n)
    lc, hc = lw - lw.mean(1, keepdims=True), hw - hw.mean(1, keepdims=True)
    beta = (lc * hc).sum(1) / (lc ** 2).sum(1)
    out = np.full(len(high), np.nan)
    out[n-1:] = beta
    return pd.Series(out, index=high.index)

df['beta'] = rolling_rsrs(df['high'], df['low'], N)
df['std_score'] = (df['beta'] - df['beta'].rolling(M, min_periods=120).mean()) \
                  / df['beta'].rolling(M, min_periods=120).std()
df = df.dropna(subset=['std_score']).copy()

# 策略：T 日信号 T+1 执行
raw = (df['std_score'] > 0.7).astype(int)
pos = raw.shift(1).fillna(0)
turn = pos.diff().abs().fillna(0)
nav = (1 + pos * df['pct'] - turn * COST).cumprod()
bench = (1 + df['pct']).cumprod()

SPLIT = pd.Timestamp('2017-06-30')   # 研报发布于 2017 上半年，此后=样本外

def seg(nav):
    nav = nav / nav.iloc[0]
    return nav.iloc[-1] ** (250/len(nav)) - 1, (nav/nav.cummax()-1).min()

for name, a, bnd in [('全样本', nav, bench),
                     ('样本内(05→17.6)', nav[nav.index < SPLIT], bench[bench.index < SPLIT]),
                     ('样本外(17.6→今)', nav[nav.index >= SPLIT], bench[bench.index >= SPLIT])]:
    sa, sm = seg(a)
    ba, bm = seg(bnd)
    print(f'{name}: 策略 {sa*100:.2f}%/{sm*100:.1f}% vs 基准 {ba*100:.2f}%/{bm*100:.1f}%')

fig, ax = plt.subplots(figsize=(10.8, 5.2), dpi=130)
ax.plot(nav.index, nav, color='#1f3a5f', lw=1.5, label='RSRS 标准分策略（单边千1）')
ax.plot(bench.index, bench, color='#c0392b', lw=1.1, alpha=0.9, label='沪深300')
ax.axvline(SPLIT, color='#7f8c8d', ls=':', lw=1.3)
ax.text(SPLIT, bench.max()*0.95, ' 2017.6 研报发布 → 此后为样本外', fontsize=9.5, color='#7f8c8d')
ax.set_title('RSRS 实测：超额收益止步于研报发布日')
ax.legend(fontsize=10, frameon=False)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig('rsrs_nav.png', bbox_inches='tight')
print('图已保存: rsrs_nav.png')
