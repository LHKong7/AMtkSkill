# AMtkSkill

OpenClaw skill for fetching, querying, and analyzing Chinese A-share market data via Tushare. Users only need a [`TUSHARE_TOKEN`](https://tushare.pro/) to get started.

## Install from ClawHub

```bash
openclaw skills install amtk-skill
```

Or with the ClawHub CLI:

```bash
clawhub install amtk-skill
```

After installing, start a new OpenClaw session so it picks up the skill.

## Manual Install

Clone the repo into your OpenClaw workspace `skills/` directory:

```bash
git clone <repo-url> skills/amtk-skill
```

Or copy the `skills/amtk-skill/` folder into your workspace `skills/` directory.

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

## Usage

All interaction is through a single skill `/amtk-skill`:

### Fetch Data

```
/amtk-skill fetch init              # First-time: fetch stock list + all market data
/amtk-skill fetch daily 20260420    # Daily incremental update
/amtk-skill fetch resume            # Resume interrupted fetch
/amtk-skill fetch stock-list        # Fetch stock list only
```

### Query Data

```
/amtk-skill query data overview
/amtk-skill query 000001.SZ recent quotes
/amtk-skill query banking sector stocks
/amtk-skill query top 10 gainers
/amtk-skill query lowest PE stocks
```

### Technical Analysis

```
/amtk-skill analyze 000001.SZ moving averages
/amtk-skill analyze 000001.SZ RSI
/amtk-skill analyze 000001.SZ MACD
/amtk-skill analyze 000001.SZ Bollinger Bands
/amtk-skill analyze 000001.SZ return statistics
```

## Publish to ClawHub

### 1. Install the ClawHub CLI

```bash
npm i -g clawhub
```

### 2. Login

```bash
clawhub login
```

### 3. Publish

```bash
clawhub skill publish ./skills/amtk-skill \
  --slug amtk-skill \
  --name "AMtkSkill" \
  --version 0.1.0 \
  --tags latest
```

### 4. Publish updates

```bash
clawhub skill publish ./skills/amtk-skill \
  --slug amtk-skill \
  --version 0.2.0 \
  --changelog "Added new feature X"
```

### 5. Verify

```bash
clawhub search "amtk"
```

## Data Layout

```
data/quant_data/raw/
├── market_daily/{ts_code}/{year}_daily.{parquet,csv}
├── daily_basic/{ts_code}/{year}_daily_basic.{parquet,csv}
└── adj_factor/{ts_code}/{year}_adj_factor.{parquet,csv}
```

## Python API

The skill calls these modules internally via `uv run python -c "..."`:

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
