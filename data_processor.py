"""
services/data_processor.py  —  Data profiling and cleaning engine.

This file contains two main functions:

  profile(df)  →  Returns a dictionary of statistics about the dataset.
                  Used by the Data Profile page and the AI Report.

  clean(df, operations)  →  Applies a list of cleaning operations to the
                             dataset and returns the cleaned copy.
                             Used by the Data Cleaning page.

All processing is done with pandas and NumPy — no external ML libraries needed.
"""

import pandas as pd
import numpy as np


# ── PROFILING ─────────────────────────────────────────────────

def profile(df: pd.DataFrame) -> dict:
    """
    Generate a comprehensive statistical profile of the DataFrame.

    Returns a dictionary with:
      - Basic shape (rows, cols)
      - Column type breakdown (numeric, categorical, datetime)
      - Missing value counts and percentages per column
      - Descriptive statistics (mean, std, min, max, quartiles)
      - Duplicate row count
      - Unique value counts per column

    The returned dict is JSON-serialisable (no numpy types).
    """
    rows, cols = df.shape

    # Separate columns into their types so we can profile them differently
    numeric_cols     = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()

    # Count missing values per column — returned as count AND percentage
    missing = {
        col: {
            "count": int(df[col].isna().sum()),
            "pct":   round(float(df[col].isna().mean()) * 100, 2),
        }
        for col in df.columns
    }

    # pandas describe() gives count, mean, std, min, 25%, 50%, 75%, max
    # for all numeric columns at once
    describe_raw = df.describe(include=[np.number])
    describe = {
        col: {stat: _safe_val(val) for stat, val in describe_raw[col].items()}
        for col in describe_raw.columns
    }

    return {
        "rows":               int(rows),
        "cols":               int(cols),
        "numeric_columns":    numeric_cols,
        "categorical_columns":categorical_cols,
        "datetime_columns":   datetime_cols,
        "missing_values":     missing,
        "duplicate_rows":     int(df.duplicated().sum()),
        "dtypes":             {col: str(dtype) for col, dtype in df.dtypes.items()},
        "unique_counts":      {col: int(df[col].nunique()) for col in df.columns},
        "describe":           describe,
        "column_names":       df.columns.tolist(),
    }


# ── CLEANING ──────────────────────────────────────────────────

def clean(df: pd.DataFrame, operations: list) -> pd.DataFrame:
    """
    Apply a list of cleaning operations to a copy of the DataFrame.
    The original is never modified.

    Supported operation strings:
      "drop_duplicates"      — remove identical rows
      "drop_high_null_cols"  — remove columns with >50% missing values
      "fill_missing_mean"    — fill numeric NaNs with the column mean
      "fill_missing_median"  — fill numeric NaNs with the column median
      "fill_missing_mode"    — fill NaNs with the most frequent value
      "remove_outliers_iqr"  — remove rows with extreme outliers (IQR method)
      "normalize_numeric"    — scale numeric columns to the range [0, 1]
      "convert_dtypes"       — let pandas auto-detect the best data type per column
    """
    df = df.copy()   # always work on a copy — never mutate the original

    if "drop_duplicates" in operations:
        df = df.drop_duplicates()

    if "drop_high_null_cols" in operations:
        df = _drop_high_null_cols(df)

    # Only one fill strategy runs — whichever appears first in priority order
    if "fill_missing_mean" in operations:
        df = _fill_missing(df, strategy="mean")
    elif "fill_missing_median" in operations:
        df = _fill_missing(df, strategy="median")
    elif "fill_missing_mode" in operations:
        df = _fill_missing(df, strategy="mode")

    if "remove_outliers_iqr" in operations:
        df = _remove_outliers_iqr(df)

    if "normalize_numeric" in operations:
        df = _normalize_numeric(df)

    if "convert_dtypes" in operations:
        df = df.convert_dtypes()

    return df


# ── PRIVATE HELPERS ───────────────────────────────────────────

def _drop_high_null_cols(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Remove columns where more than 50% of values are missing.
    A column with that many nulls usually isn't useful for analysis.
    """
    null_fractions = df.isna().mean()
    cols_to_keep   = null_fractions[null_fractions <= threshold].index
    return df[cols_to_keep]


def _fill_missing(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """
    Fill missing values in the DataFrame.

    For numeric columns:
      "mean"   → replace NaN with the column average
      "median" → replace NaN with the column middle value
      "mode"   → replace NaN with the most common value

    For text/category columns:
      Always uses mode (most common value) regardless of strategy.
    """
    df = df.copy()

    # Fill numeric columns
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isna().any():
            if strategy == "mean":
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == "median":
                df[col] = df[col].fillna(df[col].median())
            elif strategy == "mode":
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])

    # Fill text columns with their most common value
    for col in df.select_dtypes(include=["object"]).columns:
        if df[col].isna().any():
            mode_val = df[col].mode()
            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val[0])

    return df


def _remove_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows that contain outlier values using the IQR (interquartile range) method.

    For each numeric column, a row is considered an outlier if its value is:
      - Below  Q1 - 1.5 × IQR  (lower fence)
      - Above  Q3 + 1.5 × IQR  (upper fence)

    Rows that have any outlier value in any numeric column are dropped.
    """
    df           = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    # Start with all rows marked as "keep" (True)
    mask = pd.Series(True, index=df.index)

    for col in numeric_cols:
        q1  = df[col].quantile(0.25)
        q3  = df[col].quantile(0.75)
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr

        # Mark rows outside the fences as "remove" (False)
        mask &= df[col].between(lower_fence, upper_fence)

    return df[mask]


def _normalize_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scale all numeric columns to the range [0, 1] using min-max normalization.

    Formula:  new_value = (value - min) / (max - min)

    This is useful before applying distance-based algorithms like KNN or SVM
    where the scale of numbers matters.
    NumPy is used directly — no scikit-learn needed.
    """
    df           = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    for col in numeric_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        rng     = col_max - col_min

        if rng and not np.isnan(rng):
            df[col] = (df[col] - col_min) / rng
        else:
            # All values are the same — set to 0 to avoid division by zero
            df[col] = 0.0

    return df


def _safe_val(v):
    """Convert NumPy scalar types to plain Python types for JSON encoding."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else float(v)
    return v
