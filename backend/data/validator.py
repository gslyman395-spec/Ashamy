"""
Data validator - checks the quality and completeness of OHLCV data.
"""
import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, List


class DataValidator:
    """Validates raw and processed OHLCV DataFrames."""

    REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]

    def validate(self, df: pd.DataFrame, symbol: str = "") -> Dict:
        """
        Run all validation checks and return a quality report.
        """
        report = {
            "symbol": symbol,
            "total_rows": len(df),
            "issues": [],
            "is_valid": True,
        }

        report.update(self._check_columns(df))
        report.update(self._check_missing(df))
        report.update(self._check_ohlc_consistency(df))
        report.update(self._check_volume(df))
        report.update(self._check_sufficient_data(df))

        report["is_valid"] = len(report["issues"]) == 0
        if not report["is_valid"]:
            logger.warning(f"Validation issues for {symbol}: {report['issues']}")
        else:
            logger.info(f"Data validation passed for {symbol}")
        return report

    def _check_columns(self, df: pd.DataFrame) -> Dict:
        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        issues = []
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")
        return {"missing_columns": missing_cols, "issues": issues}

    def _check_missing(self, df: pd.DataFrame) -> Dict:
        issues = []
        missing_pct = df[self.REQUIRED_COLUMNS].isnull().mean() * 100
        bad = missing_pct[missing_pct > 5]
        if not bad.empty:
            for col, pct in bad.items():
                issues.append(f"Column '{col}' has {pct:.1f}% missing values")
        return {"missing_percentages": missing_pct.to_dict(), "issues": issues}

    def _check_ohlc_consistency(self, df: pd.DataFrame) -> Dict:
        issues = []
        if "High" in df.columns and "Low" in df.columns:
            inconsistent = (df["High"] < df["Low"]).sum()
            if inconsistent > 0:
                issues.append(f"{inconsistent} rows where High < Low")
        if "Close" in df.columns and "High" in df.columns:
            above_high = (df["Close"] > df["High"] * 1.01).sum()
            if above_high > 0:
                issues.append(f"{above_high} rows where Close > High")
        if "Close" in df.columns and "Low" in df.columns:
            below_low = (df["Close"] < df["Low"] * 0.99).sum()
            if below_low > 0:
                issues.append(f"{below_low} rows where Close < Low")
        return {"ohlc_issues": issues, "issues": issues}

    def _check_volume(self, df: pd.DataFrame) -> Dict:
        issues = []
        if "Volume" in df.columns:
            zero_vol = (df["Volume"] == 0).sum()
            if zero_vol > len(df) * 0.05:
                issues.append(f"{zero_vol} rows with zero volume (>{5}% of data)")
        return {"volume_issues": issues, "issues": issues}

    def _check_sufficient_data(self, df: pd.DataFrame, min_rows: int = 100) -> Dict:
        issues = []
        if len(df) < min_rows:
            issues.append(f"Insufficient data: {len(df)} rows (need at least {min_rows})")
        return {"row_count": len(df), "issues": issues}
