# -*- coding: utf-8 -*-
"""
03 防坑三件套（散户量化工具箱 ②）
实测结论：参数网格是高原（✓）、样本外原形毕露（训练 20.4% → 测试 -1.4%，✗）、成本不敏感（✓）
三个谎言：换个参数还行吗？没见过的数据还行吗？扣完成本还行吗？
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_PATH = os.path.join('data', 'hs300_raw.csv')
SPLIT = '2018-01-01'          # 训练段 2005-2017 / 测试段 2018-2026
COST = 0.001

df = pd.read_csv(DATA_PATH, parse_dates=['date'], index_col='date')
df = df[df.index >= '2005-01-01'].copy()
df['pct'] = df['close'].pct_change().fillna(0)

def strat_nav(data, fast, slow, cost=COST):
    ma_f, ma_s = data['close'].rolling(fast).mean(), data['close'].rolling(slow).mean()
    raw = (ma_f > ma_s).astype(int)
    pos = raw.shift(1).fillna(0)                 # T+1 执行
    trades = pos.diff().abs().fillna(0)
    return (1 + pos * data['pct'] - trades * cost).cumprod()

def ann(nav):
    return nav.iloc[-1] ** (250 / len(nav)) - 1

def mdd(nav):
    return (nav / nav.cummax() - 1).min()

# ---------- 防坑一：参数网格 ----------
FASTS, SLOWS = [5, 10, 15, 20, 30], [20, 40, 60, 80, 120]
grid = np.full((len(FASTS), len(SLOWS)), np.nan)
for i, f in enumerate(FASTS):
    for j, s in enumerate(SLOWS):
        if f < s:
            grid[i, j] = ann(strat_nav(df, f, s)) * 100
print('=== 参数网格（年化%，含千1成本）===')
print(pd.DataFrame(grid, index=FASTS, columns=SLOWS).round(1).to_string())

# ---------- 防坑二：样本外检验 ----------
train = df[df.index < SPLIT]
test = df[df.index >= SPLIT]
best, best_a = None, -99
for f in FASTS + [40]:
    for s in SLOWS + [180]:
        if f < s:
            a = ann(strat_nav(train, f, s))
            if a > best_a:
                best_a, best = a, (f, s)
fb, sb = best
print(f'\n训练段最优: 快{fb}/慢{sb}，训练段年化 {best_a*100:.2f}%')

def seg_ann(nav):
    nav = nav / nav.iloc[0]          # ★ 分段起点归一化（否则年化失真）
    return ann(nav) * 100

full = strat_nav(df, fb, sb)
bench = (1 + df['pct']).cumprod()
for name, nav_s, bn_s in [
        ('训练段', full[full.index < SPLIT], bench[bench.index < SPLIT]),
        ('测试段', full[full.index >= SPLIT], bench[bench.index >= SPLIT])]:
    print(f'{name}: 策略 {seg_ann(nav_s):.2f}% vs 基准 {seg_ann(bn_s):.2f}%')

# ---------- 防坑三：成本压测 ----------
print('\n=== 成本压测（快5/慢20）===')
for c_bp in [0, 5, 10, 20, 30]:
    print(f'成本 {c_bp}bp: 年化 {ann(strat_nav(df, 5, 20, c_bp/10000))*100:.2f}%')

# ---------- 出图：网格热力图 ----------
fig, ax = plt.subplots(figsize=(10.8, 5.2), dpi=130)
im = ax.imshow(grid, cmap='RdYlGn', aspect='auto')
ax.set_xticks(range(len(SLOWS)), [f'慢{s}' for s in SLOWS])
ax.set_yticks(range(len(FASTS)), [f'快{f}' for f in FASTS])
for i in range(len(FASTS)):
    for j in range(len(SLOWS)):
        if not np.isnan(grid[i, j]):
            ax.text(j, i, f'{grid[i,j]:.1f}', ha='center', va='center', fontsize=10)
ax.set_title('参数网格：年化 %（含千1成本）')
fig.colorbar(im, ax=ax, shrink=0.85)
fig.tight_layout()
fig.savefig('param_grid.png', bbox_inches='tight')
print('\n图已保存: param_grid.png')
