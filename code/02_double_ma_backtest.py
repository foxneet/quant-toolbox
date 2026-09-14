# -*- coding: utf-8 -*-
"""
02 双均线策略回测（散户量化工具箱 ①）
实测结论（沪深300, 2015→2026, 单边千1成本）：年化 -0.07%，跑不赢买入持有
关键纪律：信号 shift(1)——T 日收盘出信号，T+1 才执行（防未来函数）
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============ 配置 ============
DATA_PATH = os.path.join('data', 'hs300_raw.csv')
START = '2015-01-01'
FAST, SLOW = 5, 20
COST = 0.001          # 单边成本（佣金+滑点保守估计）

# ============ 数据 ============
df = pd.read_csv(DATA_PATH, parse_dates=['date'], index_col='date')
df = df[df.index >= START].copy()
df['pct'] = df['close'].pct_change().fillna(0)

# ============ 策略 ============
df['ma_f'] = df['close'].rolling(FAST).mean()
df['ma_s'] = df['close'].rolling(SLOW).mean()
df = df.dropna(subset=['ma_s']).copy()
raw = (df['ma_f'] > df['ma_s']).astype(int)   # 1=多头 0=空仓
pos = raw.shift(1).fillna(0)                  # ★ 信号次日才执行
trades = pos.diff().abs().fillna(0)           # 每次调仓记一笔换手

nav_cost = (1 + pos * df['pct'] - trades * COST).cumprod()
nav_free = (1 + pos * df['pct']).cumprod()
bench = (1 + df['pct']).cumprod()

# ============ 统计 ============
def stats(nav):
    ret = nav.pct_change().dropna()
    ann = nav.iloc[-1] ** (250 / len(nav)) - 1
    mdd = (nav / nav.cummax() - 1).min()
    sharpe = ret.mean() / ret.std() * np.sqrt(250) if ret.std() > 0 else 0
    return ann * 100, mdd * 100, sharpe

for name, nav in [('双均线(零成本)', nav_free), ('双均线(单边千1)', nav_cost), ('买入持有', bench)]:
    a, m, s = stats(nav)
    print(f'{name}: 年化 {a:.2f}% | 回撤 {m:.1f}% | 夏普 {s:.2f}')
print(f'交易次数(单边): {int((trades > 0).sum())}')

# ============ 出图 ============
fig, ax = plt.subplots(figsize=(10.8, 5.0), dpi=130)
ax.plot(nav_cost.index, nav_cost, color='#1f3a5f', lw=1.4, label='双均线（单边千1）')
ax.plot(bench.index, bench, color='#c0392b', lw=1.1, alpha=0.9, label='买入持有')
ax.set_title('双均线 vs 买入持有（信号 T+1 执行）')
ax.legend(fontsize=10, frameon=False)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig('backtest_nav.png', bbox_inches='tight')
print('图已保存: backtest_nav.png')
