---
name: query-data
description: 查询 AMtkSkill 本地 Parquet/CSV 数据中的 A 股行情、估值、复权因子数据
when_to_use: 当用户需要查询股票数据、查看行情、分析估值、检查数据质量、搜索股票信息时使用
argument-hint: "[查询意图，如：000001.SZ 最近行情 | 涨幅TOP10 | 银行行业 | 数据总览]"
user-invocable: true
allowed-tools: Bash(uv run *) Read Grep
---

# AMtkSkill 本地数据查询

根据用户的查询意图，使用 `query` 模块查询本地 Parquet/CSV 数据。所有查询通过 `uv run python -c "..."` 执行。

## 项目根目录

`${CLAUDE_SKILL_DIR}/../..`

## query 模块函数参考

### 数据加载

| 函数 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `load_stock_basic(list_status=None)` | list_status: L/D/P/None | DataFrame | 加载股票列表 CSV |
| `load_market_daily(ts_code, start_date, end_date)` | 均可选 | DataFrame | OHLCV + VWAP |
| `load_daily_basic(ts_code, start_date, end_date)` | 均可选 | DataFrame | PE/PB/市值/换手率 |
| `load_adj_factor(ts_code, start_date, end_date)` | 均可选 | DataFrame | 复权因子 |
| `load_full_daily(ts_code, start_date, end_date)` | ts_code 必填 | DataFrame | 合并三表 |

### 查询辅助

| 函数 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `data_overview()` | 无 | DataFrame | 各数据集行数/日期范围/股票数 |
| `search_stocks(keyword, industry, exchange)` | 均可选 | DataFrame | 搜索股票 |
| `latest_trading_date()` | 无 | str \| None | 最近交易日 (YYYYMMDD) |
| `cross_section(trade_date, sort_by, limit)` | trade_date 必填 | DataFrame | 某日全市场截面 |
| `top_movers(trade_date, direction, limit)` | trade_date 必填 | DataFrame | 涨跌幅 TOP N |

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

按行业/交易所搜索：
```bash
uv run python -c "
from query import search_stocks
result = search_stocks(industry='银行', exchange='SSE')
print(result[['ts_code','name','industry','market']].to_string(index=False))
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

### 单只股票指定日期范围
```bash
uv run python -c "
from query import load_market_daily
df = load_market_daily('000001.SZ', '20260101', '20260418')
print(df.to_string(index=False))
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

### 涨幅 TOP 10
```bash
uv run python -c "
from query import top_movers
df = top_movers('20260417', direction='up', limit=10)
print(df.to_string(index=False))
"
```

### 跌幅 TOP 10
```bash
uv run python -c "
from query import top_movers
df = top_movers('20260417', direction='down', limit=10)
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

### 市值 TOP 10
```bash
uv run python -c "
from query import load_daily_basic, load_stock_basic, latest_trading_date
date = latest_trading_date()
db = load_daily_basic(start_date=date, end_date=date)
db = db.nlargest(10, 'total_mv')
sb = load_stock_basic(list_status=None)
result = db.merge(sb[['ts_code','name','industry']], on='ts_code', how='left')
print(result[['ts_code','name','industry','total_mv','circ_mv','pe','pb']].to_string(index=False))
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

### market_daily（日行情）
ts_code, trade_date, open, high, low, close, vol(手), amount(千元), vwap

### daily_basic（估值指标）
ts_code, trade_date, turnover_rate(%), pe, pe_ttm, pb, total_mv(万元), circ_mv(万元)

### adj_factor（复权因子）
ts_code, trade_date, adj_factor

### stock_basic（股票基础信息）
ts_code, symbol, name, area, industry, market, exchange, list_status, list_date

## 执行规则

1. **如果用户未指定日期**：用 `latest_trading_date()` 获取最新交易日
2. **如果用户未指定股票代码**：根据查询类型决定是否需要
3. **大结果集**：用 `.head(N)` 或 `.tail(N)` 控制输出行数
4. **如果没有数据**：提示用户先运行 `/run-pipeline init` 抓取数据
5. **对查询结果做简要解读**：帮用户理解数据含义
