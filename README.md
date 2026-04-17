# AMtkSkill

OpenClaw skills for fetching, querying, and analyzing Chinese A-share market data via Tushare. Users only need a `TUSHARE_TOKEN` to get started.

## Install from ClawHub

```bash
openclaw skills install amtk-skill
```

Or install with the ClawHub CLI:

```bash
clawhub install amtk-skill
```

After installing, start a new OpenClaw session so it picks up the skills.

## Manual Install

Clone the repo into your OpenClaw workspace `skills/` directory:

```bash
cd your-workspace
git clone <repo-url> skills/amtk-skill
```

Or copy the three skill folders (`run-pipeline`, `query-data`, `analyze-data`) into your workspace `skills/` directory.

## Setup

Install Python dependencies:

```bash
uv sync
```

Create a `.env` file in the project root:

```
TUSHARE_TOKEN=your_token_here
```

Get your token from [tushare.pro](https://tushare.pro/).

## Skills

### `/run-pipeline` — Fetch Data

Fetches A-share market data from Tushare and stores as local Parquet/CSV files.

```
/run-pipeline init              # First-time: fetch stock list + all market data
/run-pipeline daily 20260420    # Daily incremental update
/run-pipeline resume            # Resume interrupted fetch
/run-pipeline stock-list        # Fetch stock list only
```

**What it fetches:**
- OHLCV daily quotes (open, high, low, close, volume, amount, vwap)
- Valuation metrics (PE, PB, market cap, turnover rate)
- Adjustment factors (for split/dividend adjusted prices)

### `/query-data` — Query Data

Queries local Parquet/CSV data. No database required.

```
/query-data data overview
/query-data 000001.SZ recent quotes
/query-data banking sector stocks
/query-data top 10 gainers
/query-data lowest PE stocks
/query-data market cap top 10
```

### `/analyze-data` — Technical Analysis

Runs technical analysis on local data.

```
/analyze-data 000001.SZ moving averages
/analyze-data 000001.SZ RSI
/analyze-data 000001.SZ MACD
/analyze-data 000001.SZ Bollinger Bands
/analyze-data 000001.SZ adjusted prices
/analyze-data 000001.SZ return statistics
/analyze-data 000001.SZ detect dividends/splits
```

## Publish to ClawHub

### First-time publish

```bash
# Login to ClawHub
clawhub login

# Publish each skill
clawhub skill publish ./skills/run-pipeline \
  --slug amtk-run-pipeline \
  --name "AMtkSkill: Run Pipeline" \
  --version 0.1.0 \
  --tags latest

clawhub skill publish ./skills/query-data \
  --slug amtk-query-data \
  --name "AMtkSkill: Query Data" \
  --version 0.1.0 \
  --tags latest

clawhub skill publish ./skills/analyze-data \
  --slug amtk-analyze-data \
  --name "AMtkSkill: Analyze Data" \
  --version 0.1.0 \
  --tags latest
```

### Publish updates

```bash
# Bump version and publish
clawhub skill publish ./skills/run-pipeline \
  --slug amtk-run-pipeline \
  --version 0.2.0 \
  --changelog "Added new feature X"

# Or sync all skills at once
clawhub sync --all
```

### Dry-run (preview without uploading)

```bash
clawhub sync --dry-run
```

## Data Layout

```
data/quant_data/raw/
├── market_daily/{ts_code}/{year}_daily.{parquet,csv}
├── daily_basic/{ts_code}/{year}_daily_basic.{parquet,csv}
└── adj_factor/{ts_code}/{year}_adj_factor.{parquet,csv}
```

All datasets are written as both Parquet and CSV, partitioned by stock code and year.

## Python API

Skills call these modules internally. You can also use them directly via `uv run python -c "..."`:

```python
# Fetch
from fetcher.pipeline import init_fetch, daily_update
from fetcher.stock_basic import fetch_and_save_stock_basic

# Query
from query import load_market_daily, load_full_daily, search_stocks, top_movers

# Analysis
from analysis import moving_average, rsi, macd, price_statistics
```

See `devDocs/local_query_reference.md` for complete API reference.

## Requirements

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [Tushare](https://tushare.pro/) API token
