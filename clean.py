"""
routes/clean.py  —  Handles data cleaning.

When the user selects cleaning operations and clicks "Apply Cleaning":
  1. The browser sends a list of operation names (e.g. ["drop_duplicates", "fill_missing_mean"])
  2. This route applies those operations to the original dataset
  3. The cleaned result is saved back to memory AND written to uploads/cleaned_dataset.csv
  4. A preview of the first 10 cleaned rows is returned

The user can also download the cleaned CSV via GET /download-cleaned.

Available operations (sent from the browser):
  drop_duplicates      — remove identical rows
  fill_missing_mean    — fill empty numbers with the column average
  fill_missing_median  — fill empty numbers with the column median
  fill_missing_mode    — fill empty values with the most common value
  remove_outliers_iqr  — drop rows with extreme values (IQR method)
  drop_high_null_cols  — remove columns that are >50% empty
  normalize_numeric    — scale all numbers to the range [0, 1]
  convert_dtypes       — auto-convert columns to the best data type
"""

import os
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify, send_file
from services.data_processor import clean
from routes.upload import get_state

clean_bp = Blueprint("clean", __name__)

# The cleaned dataset is saved here so the user can download it
CLEANED_FILENAME = "uploads/cleaned_dataset.csv"


def _safe(obj):
    """
    Convert NumPy/Pandas types to plain Python types for JSON encoding.
    Replaces NaN and NaT with None (which becomes null in JSON).
    """
    if isinstance(obj, dict):
        return {k: _safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe(i) for i in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else float(obj)
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    return obj


@clean_bp.route("/clean", methods=["POST"])
def clean_data():
    """
    POST /clean
    Body (JSON): { "operations": ["drop_duplicates", "fill_missing_mean", ...] }
    Returns a preview of the cleaned dataset and shape comparison.
    """
    state = get_state()
    df = state.get("df")   # always clean from the original upload

    if df is None:
        return jsonify({"error": "No dataset loaded. Please upload a file first."}), 400

    # Read which operations the user selected from the request body
    body       = request.get_json(silent=True) or {}
    operations = body.get("operations", [])

    if not operations:
        return jsonify({"error": "No cleaning operations selected."}), 400

    # Run the cleaning — see services/data_processor.py for the logic
    try:
        cleaned_df = clean(df, operations)
    except Exception as e:
        return jsonify({"error": f"Cleaning failed: {str(e)}"}), 500

    # Save the cleaned DataFrame so other pages (visualize, report) can use it
    state["cleaned_df"] = cleaned_df

    # Also write it to disk so the user can download it
    cleaned_df.to_csv(CLEANED_FILENAME, index=False)

    # Build a preview of the first 10 rows
    preview_df = cleaned_df.head(10).where(pd.notnull(cleaned_df.head(10)), None)
    preview    = preview_df.to_dict(orient="records")

    return jsonify({
        "message":         f"Applied operations: {operations}",
        "original_shape":  {"rows": int(df.shape[0]),         "cols": int(df.shape[1])},
        "cleaned_shape":   {"rows": int(cleaned_df.shape[0]), "cols": int(cleaned_df.shape[1])},
        "columns_removed": [c for c in df.columns if c not in cleaned_df.columns],
        "rows_removed":    int(df.shape[0] - cleaned_df.shape[0]),
        "preview":         _safe(preview),
        "columns":         cleaned_df.columns.tolist(),
        "download_url":    "/download-cleaned",
    })


@clean_bp.route("/download-cleaned", methods=["GET"])
def download_cleaned():
    """
    GET /download-cleaned
    Sends the cleaned CSV file as a download attachment.
    """
    if not os.path.exists(CLEANED_FILENAME):
        return jsonify({"error": "No cleaned dataset available. Apply cleaning first."}), 404

    return send_file(
        os.path.abspath(CLEANED_FILENAME),
        mimetype="text/csv",
        as_attachment=True,
        download_name="cleaned_dataset.csv",
    )
