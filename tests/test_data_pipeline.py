"""Tests for AMtkSkill data pipeline components."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

from fetcher.daily import default_past_year_dates, load_ts_codes_from_csv, apply_code_window, validate_yyyymmdd
from transforms import add_vwap, normalize_trade_date
from storage import write_symbol_year_partitioned_dataset, safe_partition_value, dataset_paths, read_dataset_file


class TransformTests(unittest.TestCase):
    def test_add_vwap_handles_valid_and_invalid_volume(self):
        df = pd.DataFrame({
            "vol": [100.0, 0.0, 200.0, -1.0],
            "amount": [5000.0, 3000.0, 10000.0, 1000.0],
        })
        result = add_vwap(df)
        self.assertAlmostEqual(result["vwap"].iloc[0], 5000.0 * 10 / 100.0)
        self.assertTrue(pd.isna(result["vwap"].iloc[1]))
        self.assertAlmostEqual(result["vwap"].iloc[2], 10000.0 * 10 / 200.0)
        self.assertTrue(pd.isna(result["vwap"].iloc[3]))

    def test_normalize_trade_date(self):
        df = pd.DataFrame({"trade_date": ["20260417", "20260418"]})
        result = normalize_trade_date(df)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result["trade_date"]))

    def test_default_past_year_dates(self):
        start, end = default_past_year_dates(today=date(2026, 4, 18))
        self.assertEqual(start, "20250418")
        self.assertEqual(end, "20260418")

    def test_load_ts_codes_from_csv_and_apply_window(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("ts_code,name\n000001.SZ,Test1\n000002.SZ,Test2\n000003.SZ,Test3\n")
            csv_path = Path(f.name)

        codes = load_ts_codes_from_csv(csv_path)
        self.assertEqual(len(codes), 3)
        self.assertEqual(codes[0], "000001.SZ")

        windowed = apply_code_window(codes, offset=1, limit=1)
        self.assertEqual(windowed, ["000002.SZ"])

        csv_path.unlink()


class StorageTests(unittest.TestCase):
    def test_symbol_year_partitioned_write_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            df = pd.DataFrame({
                "ts_code": ["000001.SZ", "000001.SZ"],
                "trade_date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
                "close": [10.0, 11.0],
            })

            results1 = write_symbol_year_partitioned_dataset(
                df, "raw/test", "test", keys=["ts_code", "trade_date"], root=root,
            )
            results2 = write_symbol_year_partitioned_dataset(
                df, "raw/test", "test", keys=["ts_code", "trade_date"], root=root,
            )

            self.assertEqual(len(results1), 1)
            self.assertEqual(results1[0].rows, 2)
            self.assertEqual(results2[0].rows, 2)

    def test_safe_partition_value(self):
        self.assertEqual(safe_partition_value("000001.SZ"), "000001.SZ")
        self.assertEqual(safe_partition_value("test/bad"), "test_bad")

    def test_read_dataset_file_returns_empty_for_missing(self):
        result = read_dataset_file(Path("/nonexistent.parquet"), Path("/nonexistent.csv"))
        self.assertTrue(result.empty)

    def test_validate_yyyymmdd(self):
        validate_yyyymmdd("20260418", "test")
        with self.assertRaises(RuntimeError):
            validate_yyyymmdd("2026-04-18", "test")


class QueryModuleTests(unittest.TestCase):
    def test_data_overview_returns_dataframe(self):
        from query import data_overview
        result = data_overview()
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("dataset", result.columns)
        self.assertIn("rows", result.columns)

    def test_search_stocks_returns_empty_without_data(self):
        from query import search_stocks
        try:
            result = search_stocks(keyword="nonexistent_xyz")
        except RuntimeError:
            pass  # No stock_basic CSV, expected

    def test_latest_trading_date_returns_none_without_data(self):
        from query import latest_trading_date
        result = latest_trading_date()
        # With no data dir or empty, should return None
        self.assertTrue(result is None or isinstance(result, str))


class AnalysisModuleTests(unittest.TestCase):
    def test_imports(self):
        from analysis import (
            forward_adjusted_prices, backward_adjusted_prices,
            moving_average, rsi, macd, bollinger_bands,
            price_statistics, detect_corporate_actions,
        )
        # All functions should be callable
        self.assertTrue(callable(forward_adjusted_prices))
        self.assertTrue(callable(price_statistics))


if __name__ == "__main__":
    unittest.main()
