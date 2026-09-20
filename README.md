# 量化工具箱 / Quant Toolbox

> 配套公众号「晋盈投资」《散户量化工具箱》《AI 投研手搓实录》系列的全套可运行代码。
> 全部代码在真实 A 股数据上跑过，结果在公众号文章中如实公开（包括不赚钱的）。

## ⚠️ 免责声明

本仓库仅用于量化交易方法学习与研究，不构成任何投资建议，不涉及任何具体标的推荐，亦不承诺任何收益。历史回测不代表未来表现。市场有风险，决策需谨慎。

## 目录

| 脚本 | 对应文章 | 内容 |
|---|---|---|
| `code/01_data_fetch_baostock.py` | 工具箱 ① | baostock 数据获取（5265 个交易日实测 3.3s） |
| `code/02_double_ma_backtest.py` | 工具箱 ① | 双均线策略回测（T+1 执行 + 成本），跑不赢持有的诚实结果 |
| `code/03_anti_pitfall_tests.py` | 工具箱 ② | 防坑三件套：参数网格 / 样本外检验 / 成本压测 |
| `code/04_position_kelly.py` | 工具箱 ③ | 凯利公式实测（f*=0.75）+ 仓位扫描 + 回撤响应实验 |
| `code/05_rsrs_timing.py` | 中秋特供 | RSRS 择时实测：发布前年化 27%，发布后 2.5% |
| `code/06_api_benchmark.py` | 数据接口横评 | baostock / akshare / TQ / xtquant 六组接口速度实测（xtquant 段为历史实测，miniQMT 已停用） |
| `code/07_data_pipeline.py` | AI 投研 ② | 适配器 + parquet 落库 + 增量更新 + 四项质检 |
| `code/08_moon_phase.py` | 中秋彩蛋 | 计算任意日期的月相（含月相对收益的趣味检验） |

## 环境要求

```bash
pip install pandas numpy matplotlib baostock akshare pyarrow
# 06 号脚本需要：本地运行通达信/QMT 客户端（可选）
```

## 快速开始

```bash
python code/01_data_fetch_baostock.py   # 先拉数据到 data/
python code/02_double_ma_backtest.py    # 跑第一个回测
```

数据默认存放在 `data/` 目录（自动创建）。

## 系列文章索引（公众号「晋盈投资」）

- 《散户量化工具箱 ①：用 Python 跑通你的第一个双均线回测》
- 《散户量化工具箱 ②：训练段年化 20%，测试段 −1.4%——防坑三件套实测》
- 《散户量化工具箱 ③：凯利公式实测——最优仓位是 75%，不是满仓》
- 《中秋特供 | 我们用 21 年 A 股数据，实测了「月亮会影响股市」》
- 《免费A股数据接口怎么选？akshare、baostock、通达信TQ、miniQMT 全部实测了一遍》
- 《AI 投研手搓实录》系列（连载中）

## License

MIT
