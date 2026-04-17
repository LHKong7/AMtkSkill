---
name: run-pipeline
description: 执行 AMtkSkill 数据管道：从 Tushare 抓取 A 股行情数据并存储为本地 Parquet/CSV 文件
when_to_use: 当用户需要抓取股票数据、执行每日更新、首次初始化数据、或排查数据管道问题时使用
argument-hint: "[场景: init | daily YYYYMMDD | resume | stock-list]"
user-invocable: true
allowed-tools: Bash(uv run *) Bash(uv sync) Read Grep
---

# AMtkSkill 数据管道

根据用户指定的场景，调用 Python 模块执行对应操作。如果用户未指定场景，先询问。

## 前置条件

项目根目录：`${CLAUDE_SKILL_DIR}/../..`

必须在 `.env` 中配置 `TUSHARE_TOKEN`。

检查依赖：
```!
uv sync
```

## 场景：`init` — 首次初始化

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
2. 以 `--resume` 模式抓取，跳过已完成的股票
3. 同时抓取 daily_basic（PE/PB/市值）和 adj_factor（复权因子）

抓取完成后验证数据：
```bash
uv run python -c "
from query import data_overview
print(data_overview().to_string(index=False))
"
```

## 场景：`daily YYYYMMDD` — 每日增量更新

收盘后增量抓取当天新数据。将用户指定的日期作为 `end_date`。

```bash
uv run python -c "
from fetcher.pipeline import daily_update
daily_update(end_date='<YYYYMMDD>')
"
```

`daily_update` 内部自动：
1. 查找已有股票列表
2. 以 `--incremental` 模式，每只股票从本地 `max(trade_date)+1` 开始补数据

## 场景：`resume` — 补抓取中断的数据

与 `init` 完全相同，`init_fetch` 本身就是 resume 模式：

```bash
uv run python -c "
from fetcher.pipeline import init_fetch
init_fetch()
"
```

## 场景：`stock-list` — 仅拉取股票列表

```bash
uv run python -c "
from fetcher.stock_basic import fetch_and_save_stock_basic
from fetcher.common import load_dotenv_if_needed
load_dotenv_if_needed(None)
fetch_and_save_stock_basic()
"
```

可选参数：
```bash
uv run python -c "
from fetcher.stock_basic import fetch_and_save_stock_basic
from fetcher.common import load_dotenv_if_needed
load_dotenv_if_needed(None)
fetch_and_save_stock_basic(list_status='L', exchange='SSE')
"
```

## 模块接口速查

### `fetcher.pipeline`

| 函数 | 参数 | 说明 |
|------|------|------|
| `init_fetch(start_date, end_date, sleep_seconds, batch_size, limit, token)` | 均可选 | 全量抓取 + resume |
| `daily_update(end_date, start_date, sleep_seconds, batch_size, limit, token)` | end_date 必填 | 增量更新 |

### `fetcher.stock_basic`

| 函数 | 参数 | 说明 |
|------|------|------|
| `fetch_and_save_stock_basic(token, list_status, exchange)` | 均可选 | 拉取股票列表存 CSV |
| `find_latest_stock_basic_csv()` | 无 | 查找最新股票列表 CSV |

### 数据存储位置

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
