---
name: amtk-skill
description: A 股行情数据技能：从 Tushare 抓取数据、查询行情估值、技术分析（均线/RSI/MACD/布林带）
when_to_use: 当用户需要 A 股数据时使用 — 抓取股票数据、查询行情、搜索股票、分析估值、计算技术指标、统计收益率等
argument-hint: "[操作: fetch init | fetch daily YYYYMMDD | query 000001.SZ | query 涨幅TOP10 | analyze 000001.SZ MACD]"
user-invocable: true
allowed-tools: Bash(uv run *) Bash(uv sync) Read Grep
---

# AMtkSkill — A 股行情数据技能

根据用户意图判断执行哪类操作：**fetch**（抓取数据）、**query**（查询数据）、**analyze**（技术分析）。

如果用户意图不明确，先询问。

## 前置条件

项目根目录：`${CLAUDE_SKILL_DIR}/../..`

必须在 `.env` 中配置 `TUSHARE_TOKEN`。

检查依赖：
```!
uv sync
```

---

# 一、Fetch — 数据抓取

从 Tushare 抓取 A 股行情数据并存储为本地 Parquet/CSV 文件。

## fetch init — 首次初始化

全量抓取股票列表 + 全部行情数据（OHLCV + 估值 + 复权因子），支持中断续跑。

```bash
uv run python -c "
from fetcher.pipeline import init_fetch
init_fetch()
"
```

可选参数：
```bash
uv run python -c "
from fetcher.pipeline import init_fetch
init_fetch(
    start_date='20250418',    # 起始日期，默认一年前
    end_date='20260418',      # 结束日期，默认今天
    sleep_seconds=0.5,        # API请求间隔，默认0.5
    batch_size=100,           # 每批写入股票数，默认100
    limit=10,                 # 只抓N只（测试用），默认None=全部
)
"
```

`init_fetch` 内部自动：
1. 查找已有股票列表 CSV，没有则从 Tushare 拉取
2. 以 resume 模式抓取，跳过已完成的股票
3. 同时抓取 daily_basic（PE/PB/市值）和 adj_factor（复权因子）

抓取完成后验证数据：
```bash
uv run python -c "
from query import data_overview
print(data_overview().to_string(index=False))
"
```

## fetch daily YYYYMMDD — 每日增量更新

收盘后增量抓取当天新数据。将用户指定的日期作为 `end_date`。

```bash
uv run python -c "
from fetcher.pipeline import daily_update
daily_update(end_date='<YYYYMMDD>')
"
```

## fetch resume — 补抓取中断的数据

与 init 完全相同，`init_fetch` 本身就是 resume 模式：

```bash
uv run python -c "
from fetcher.pipeline import init_fetch
init_fetch()
"
```

## fetch stock-list — 仅拉取股票列表

```bash
uv run python -c "
from fetcher.stock_basic import fetch_and_save_stock_basic
from fetcher.common import load_dotenv_if_needed
load_dotenv_if_needed(None)
fetch_and_save_stock_basic()
"
```

---

# 二、Query — 数据查询

查询本地 Parquet/CSV 数据。所有查询通过 `uv run python -c "..."` 执行。

## query 模块函数参考

### 数据加载

| 函数 | 参数 | 说明 |
|------|------|------|
| `load_stock_basic(list_status=None)` | list_status: L/D/P/None | 加载股票列表 |
| `load_market_daily(ts_code, start_date, end_date)` | 均可选 | OHLCV + VWAP |
| `load_daily_basic(ts_code, start_date, end_date)` | 均可选 | PE/PB/市值/换手率 |
| `load_adj_factor(ts_code, start_date, end_date)` | 均可选 | 复权因子 |
| `load_full_daily(ts_code, start_date, end_date)` | ts_code 必填 | 合并三表 |

### 查询辅助

| 函数 | 参数 | 说明 |
|------|------|------|
| `data_overview()` | 无 | 各数据集行数/日期范围/股票数 |
| `search_stocks(keyword, industry, exchange)` | 均可选 | 搜索股票 |
| `latest_trading_date()` | 无 | 最近交易日 (YYYYMMDD) |
| `cross_section(trade_date, sort_by, limit)` | trade_date 必填 | 某日全市场截面 |
| `top_movers(trade_date, direction, limit)` | trade_date 必填 | 涨跌幅 TOP N |

### 参数格式

- `ts_code`: 股票代码，如 `"000001.SZ"`
- `start_date` / `end_date` / `trade_date`: YYYYMMDD 字符串
- `direction`: `"up"` 或 `"down"`

## 查询模板

### 数据总览
```bash
uv run python -c "
from query import data_overview
print(data_overview().to_string(index=False))
"
```

### 搜索股票
```bash
uv run python -c "
from query import search_stocks
result = search_stocks(keyword='银行')
print(result[['ts_code','name','industry','market','list_status']].to_string(index=False))
"
```

### 单只股票最近行情
```bash
uv run python -c "
from query import load_market_daily
df = load_market_daily('000001.SZ')
print(df.tail(20).to_string(index=False))
"
```

### 单只股票完整数据（行情+估值+复权因子）
```bash
uv run python -c "
from query import load_full_daily
df = load_full_daily('000001.SZ')
print(df.tail(20).to_string(index=False))
"
```

### 全市场截面（某日成交额 TOP 20）
```bash
uv run python -c "
from query import cross_section
df = cross_section('20260417', sort_by='amount', limit=20)
print(df.to_string(index=False))
"
```

### 涨幅 / 跌幅 TOP 10
```bash
uv run python -c "
from query import top_movers
df = top_movers('20260417', direction='up', limit=10)
print(df.to_string(index=False))
"
```

### PE 最低 TOP 10
```bash
uv run python -c "
from query import load_daily_basic, load_stock_basic, latest_trading_date
date = latest_trading_date()
db = load_daily_basic(start_date=date, end_date=date)
db = db[db['pe'] > 0].nsmallest(10, 'pe')
sb = load_stock_basic(list_status=None)
result = db.merge(sb[['ts_code','name','industry']], on='ts_code', how='left')
print(result[['ts_code','name','industry','pe','pe_ttm','pb','total_mv']].to_string(index=False))
"
```

### 行业平均估值
```bash
uv run python -c "
from query import load_daily_basic, load_stock_basic, latest_trading_date
date = latest_trading_date()
db = load_daily_basic(start_date=date, end_date=date)
sb = load_stock_basic(list_status=None)
merged = db.merge(sb[['ts_code','industry']], on='ts_code', how='left')
stats = merged.groupby('industry').agg(
    avg_pe=('pe', 'mean'), avg_pb=('pb', 'mean'),
    total_mv=('total_mv', 'sum'), count=('ts_code', 'count')
).round(2).sort_values('total_mv', ascending=False)
print(stats.head(20).to_string())
"
```

## 数据表结构

| 数据集 | 字段 |
|--------|------|
| market_daily | ts_code, trade_date, open, high, low, close, vol(手), amount(千元), vwap |
| daily_basic | ts_code, trade_date, turnover_rate(%), pe, pe_ttm, pb, total_mv(万元), circ_mv(万元) |
| adj_factor | ts_code, trade_date, adj_factor |
| stock_basic | ts_code, symbol, name, area, industry, market, exchange, list_status, list_date |

---

# 三、Analyze — 技术分析

使用 `analysis` 模块执行技术分析。所有分析通过 `uv run python -c "..."` 执行。

## analysis 模块函数参考

### 复权价格

| 函数 | 说明 |
|------|------|
| `forward_adjusted_prices(ts_code, start_date, end_date)` | 前复权（close * adj / latest_adj） |
| `backward_adjusted_prices(ts_code, start_date, end_date)` | 后复权（close * adj） |

### 技术指标

| 函数 | 默认参数 | 新增列 |
|------|----------|--------|
| `moving_average(ts_code, windows, start_date, end_date, adjusted)` | windows=[5,10,20,60] | ma5, ma10, ma20, ma60 |
| `rsi(ts_code, period, start_date, end_date, adjusted)` | period=14 | rsi |
| `macd(ts_code, fast, slow, signal, start_date, end_date, adjusted)` | fast=12, slow=26, signal=9 | macd, macd_signal, macd_hist |
| `bollinger_bands(ts_code, window, num_std, start_date, end_date, adjusted)` | window=20, num_std=2.0 | bb_upper, bb_mid, bb_lower |

所有指标默认使用前复权价格（`adjusted=True`）。

### 统计分析

| 函数 | 返回 | 说明 |
|------|------|------|
| `price_statistics(ts_code, start_date, end_date, adjusted)` | dict | 收益率/波动率/最大回撤/夏普比率 |
| `detect_corporate_actions(ts_code, start_date, end_date)` | DataFrame | 分红拆股日期 |

## 分析模板

### 均线
```bash
uv run python -c "
from analysis import moving_average
df = moving_average('000001.SZ', windows=[5, 10, 20, 60], start_date='20260101')
print(df[['trade_date','close','ma5','ma10','ma20','ma60']].tail(20).to_string(index=False))
"
```

### RSI
```bash
uv run python -c "
from analysis import rsi
df = rsi('000001.SZ', period=14, start_date='20260101')
print(df[['trade_date','close','rsi']].tail(20).to_string(index=False))
"
```

### MACD
```bash
uv run python -c "
from analysis import macd
df = macd('000001.SZ', start_date='20260101')
print(df[['trade_date','close','macd','macd_signal','macd_hist']].tail(20).to_string(index=False))
"
```

### 布林带
```bash
uv run python -c "
from analysis import bollinger_bands
df = bollinger_bands('000001.SZ', start_date='20260101')
print(df[['trade_date','close','bb_upper','bb_mid','bb_lower']].tail(20).to_string(index=False))
"
```

### 前复权价格
```bash
uv run python -c "
from analysis import forward_adjusted_prices
df = forward_adjusted_prices('000001.SZ', start_date='20260101')
print(df[['trade_date','close','close_adj','adj_factor']].tail(20).to_string(index=False))
"
```

### 收益统计
```bash
uv run python -c "
from analysis import price_statistics
stats = price_statistics('000001.SZ', start_date='20250418')
for k, v in stats.items():
    print(f'{k}: {v}')
"
```

### 检测分红拆股
```bash
uv run python -c "
from analysis import detect_corporate_actions
df = detect_corporate_actions('000001.SZ')
if df.empty:
    print('No corporate actions detected')
else:
    print(df.to_string(index=False))
"
```

### 多股票对比
```bash
uv run python -c "
from analysis import price_statistics
for code in ['000001.SZ', '600519.SH', '000858.SZ']:
    stats = price_statistics(code, start_date='20250418')
    if stats:
        print(f\"{stats['ts_code']:12s} return={stats['total_return_pct']:>7.2f}%  \"
              f\"vol={stats['annualized_volatility_pct']:>6.2f}%  \"
              f\"drawdown={stats['max_drawdown_pct']:>7.2f}%  \"
              f\"sharpe={stats['sharpe_ratio']:>6.4f}\")
"
```

## 指标解读参考

| 指标 | 多头/超买 | 空头/超卖 |
|------|----------|----------|
| RSI | > 70 超买 | < 30 超卖 |
| MACD | macd > signal（金叉） | macd < signal（死叉） |
| 布林带 | 价格触及上轨 | 价格触及下轨 |
| 均线 | 短期 > 长期（多头排列） | 短期 < 长期（空头排列） |

---

# 通用规则

1. **如果用户未指定日期**：用 `latest_trading_date()` 获取最新交易日
2. **如果没有数据**：提示用户先执行 `/amtk-skill fetch init` 抓取数据
3. **大结果集**：用 `.head(N)` 或 `.tail(N)` 控制输出行数
4. **默认使用前复权价格** — 除非用户明确要求未复权
5. **对结果做简要解读** — 帮用户理解数据含义

## 数据存储位置

```
data/quant_data/raw/
├── market_daily/{ts_code}/{year}_daily.{parquet,csv}
├── daily_basic/{ts_code}/{year}_daily_basic.{parquet,csv}
└── adj_factor/{ts_code}/{year}_adj_factor.{parquet,csv}
```

## 故障排查

- **token 错误** — 检查 `.env` 中 `TUSHARE_TOKEN`
- **缺少 pyarrow** — 运行 `uv sync`
- **中断后续跑** — 直接重新调用 `init_fetch()`，自动跳过已完成的
- **只想抓少量测试** — 设置 `limit=5`
