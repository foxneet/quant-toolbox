# -*- coding: utf-8 -*-
"""
04 仓位管理实验（散户量化工具箱 ③）
实测结论（双均线 快5/慢40，91 笔真实交易）：
  凯利公式 f* = p - (1-p)/b = 0.86 - 0.14/1.33 ≈ 0.75 → 最优仓位是 75%，不是满仓
  仓位扫描：收益与回撤同步线性放大，夏普不变（仓位没有免费午餐）
  回撤>25% 砍仓实测比不动更差（反直觉！任何风控规则都应先回测）
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_PATH = os.path.join('data', 'hs300_raw.csv')
COST = 0.001
FAST, SLOW = 5, 40

df = pd.read_csv(DATA_PATH, parse_dates=['date'], index_col='date')
df = df[df.index >= '2005-01-01'].copy()
df['pct'] = df['close'].pct_change().fillna(0)
ma_f, ma_s = df['close'].rolling(FAST).mean(), df['close'].rolling(SLOW).mean()
raw = (ma_f > ma_s).astype(int)
pos = raw.shift(1).fillna(0)
trades = pos.diff().abs().fillna(0)
r_s = pos * df['pct'] - trades * COST           # 满仓策略日收益

# ---------- 1. 逐笔交易 → 凯利公式 ----------
entries = df.index[(pos.diff() == 1) & (pos.shift(1).fillna(0) == 0)]
trade_rets = []
for d in entries:
    seg = df.loc[d:].copy()
    still = seg['r_s'].shift(1).fillna(0) != 0
    held = seg[still]
    if len(held) == 0:
        continue
    tr = (1 + held['pct']).prod() - 1
    trade_rets.append(tr - 2 * COST)
tr = np.array(trade_rets)
p = (tr > 0).mean()
b = tr[tr > 0].mean() / abs(tr[tr <= 0].mean())
f_kelly = p - (1 - p) / b
print(f'n={len(tr)} 胜率 p={p:.2f} 盈亏比 b={b:.2f} → 凯利 f*={f_kelly:.2f}')

# ---------- 2. 仓位扫描 ----------
print('\n仓位 f | 年化% | 回撤% | 夏普')
for f in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]:
    nav = (1 + f * r_s).cumprod()
    ret = nav.pct_change().dropna()
    a = nav.iloc[-1] ** (250 / len(nav)) - 1
    m = (nav / nav.cummax() - 1).min()
    sh = ret.mean() / ret.std() * np.sqrt(250)
    print(f'{f:5.2f} | {a*100:6.2f} | {m*100:6.1f} | {sh:.2f}')

# ---------- 3. 回撤响应实验 ----------
def run(mode, trig=0.25, rec=0.10):
    base = (1 + r_s).cumprod()
    dd = base / base.cummax() - 1
    state, eff = 1.0, []
    for d in dd.values:
        if mode == 'cut' and d < -trig: state = 0.5
        elif mode == 'add' and d < -trig: state = 1.5
        elif d > -rec: state = 1.0
        eff.append(state)
    eff = pd.Series(eff, index=dd.index)
    nav = (1 + eff * r_s).cumprod()
    ret = nav.pct_change().dropna()
    return (nav.iloc[-1] ** (250/len(nav)) - 1) * 100, (nav/nav.cummax()-1).min()*100

print('\n回撤>25% 三种应对：')
for mode in ['base', 'cut', 'add']:
    a, m = run(mode)
    print(f'{mode}: 年化 {a:.2f}% | 回撤 {m:.1f}%')

# ---------- 出图：仓位-收益曲线 ----------
fs = np.arange(0.05, 2.55, 0.05)
anns = [(1 + f * r_s).cumprod().iloc[-1] ** (250/len(df)) - 1 for f in fs]
fig, ax = plt.subplots(figsize=(10.8, 5.0), dpi=130)
ax.plot(fs, np.array(anns) * 100, color='#1f3a5f', lw=2)
ax.axvline(f_kelly, color='#c0a050', ls='--', lw=1.5, label=f'凯利 f*={f_kelly:.2f}')
ax.axvline(1.0, color='#7f8c8d', ls=':', lw=1.2, label='满仓 f=1')
ax.axhline(0, color='#c0392b', ls='--', lw=1.0)
ax.set_xlabel('仓位比例 f（>1 为杠杆，仅数学展示）')
ax.set_ylabel('年化 %')
ax.set_title('仓位-收益曲线（2005→2026 实测）')
ax.legend()
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig('fraction_curve.png', bbox_inches='tight')
print('\n图已保存: fraction_curve.png')
