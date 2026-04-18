# AMtkSkill 运行手册

## 1. 环境准备

```bash
uv sync
```

## 2. 配置

在项目根目录创建 `.env` 文件：

```
TUSHARE_TOKEN=your_token
```

## 3. 使用

所有操作通过 `/amtk-skill` 完成：

### 数据抓取

```
/amtk-skill fetch init              # 首次全量抓取
/amtk-skill fetch daily 20260420    # 每日增量更新
/amtk-skill fetch resume            # 中断续跑
/amtk-skill fetch stock-list        # 仅拉取股票列表
```

### 数据查询

```
/amtk-skill query 数据总览
/amtk-skill query 000001.SZ 最近行情
/amtk-skill query 银行行业股票
/amtk-skill query 涨幅TOP10
/amtk-skill query PE最低的股票
```

### 技术分析

```
/amtk-skill analyze 000001.SZ 均线
/amtk-skill analyze 000001.SZ MACD
/amtk-skill analyze 000001.SZ 复权价格
/amtk-skill analyze 000001.SZ 收益统计
```

## 4. 运行测试

```bash
uv run python -m unittest discover -s tests
```

## 5. 常见问题

- **token 错误** — 检查 `.env` 中 `TUSHARE_TOKEN`
- **缺少 pyarrow** — 运行 `uv sync`
- **没有数据** — 先执行 `/amtk-skill fetch init`
- **中断后续跑** — 执行 `/amtk-skill fetch resume`
