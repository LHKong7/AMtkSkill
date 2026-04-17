---
name: analyze-data
description: 对 AMtkSkill 本地数据进行技术分析：复权价格、均线、RSI、MACD、布林带、统计指标
when_to_use: 当用户需要技术分析、计算均线、查看RSI/MACD、计算复权价格、统计收益率波动率、检测分红拆股时使用
argument-hint: "[分析意图，如：000001.SZ 均线 | MACD | 复权价格 | 收益统计 | 分红拆股]"
user-invocable: true
allowed-tools: Bash(uv run *) Read Grep
---

# AMtkSkill 技术分析

根据用户的分析意图，使用 `analysis` 模块执行技术分析。所有分析通过 `uv run python -c "..."` 执行。

## 项目根目录

`${CLAUDE_SKILL_DIR}/../..`

## analysis 模块函数参考

### 复权价格

| 函数 | 说明 |
|------|------|
| `forward_adjusted_prices(ts_code, start_date, end_date)` | 前复权（close * adj / latest_adj） |
| `backward_adjusted_prices(ts_code, start_date, end_date)` | 后复权（close * adj） |

返回 DataFrame，原始列 + `*_adj` 后缀列（open_adj, high_adj, low_adj, close_adj, vwap_adj）。

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
| `detect_corporate_actions(ts_code, start_date, end_date)` | DataFrame | 分红拆股日期（复权因子变化点） |

## 分析模板

### 均线分析
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

### 多指标组合
```bash
uv run python -c "
from analysis import moving_average, rsi, price_statistics

ma = moving_average('000001.SZ', windows=[5, 20], start_date='20260101')
r = rsi('000001.SZ', start_date='20260101')
combined = ma.merge(r[['trade_date','rsi']], on='trade_date')
print(combined[['trade_date','close','ma5','ma20','rsi']].tail(10).to_string(index=False))

print()
stats = price_statistics('000001.SZ', start_date='20250418')
for k, v in stats.items():
    print(f'{k}: {v}')
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

| 指标 | 多头/超买信号 | 空头/超卖信号 |
|------|-------------|-------------|
| RSI | > 70 超买 | < 30 超卖 |
| MACD | macd > signal（金叉） | macd < signal（死叉） |
| 布林带 | 价格触及上轨 | 价格触及下轨 |
| 均线 | 短期 > 长期（多头排列） | 短期 < 长期（空头排列） |

## 执行规则

1. **默认使用前复权价格** — 除非用户明确要求未复权
2. **如果没有数据** — 提示用户先运行 `/run-pipeline init`
3. **如果没有复权因子** — 设 `adjusted=False` 使用未复权价格
4. **对结果做简要解读** — 如 RSI 数值含义、均线排列状态等
