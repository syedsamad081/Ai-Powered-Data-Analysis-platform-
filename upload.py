"""
routes/upload.py  —  Handles file uploads.

When the user selects a file on the Upload page, the browser sends it here.
This route:
  1. Checks the file type is allowed (CSV, Excel, Word, PDF)
  2. Saves the file to the uploads/ folder
  3. Reads it into a pandas DataFrame using the appropriate parser
  4. Stores the DataFrame in memory so other pages can use it
  5. Returns a preview of the first 10 rows as JSON

Supported file types: .csv  .xlsx  .xls  .docx  .pdf
"""

import os
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from services.file_handler import parse_file

upload_bp = Blueprint("upload", __name__)

# Where uploaded files are saved on the server
UPLOAD_FOLDER = "uploads"

# Only these file extensions are accepted
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "docx", "pdf"}

# This dictionary holds the current dataset in memory.
# It acts like a simple session — all pages share this same data.
# Key: "df"         → the original DataFrame after upload
# Key: "cleaned_df" → the DataFrame after cleaning (or None if not cleaned yet)
# Key: "filepath"   → path to the saved file on disk
_state = {}


def get_state():
    """
    Returns the shared in-memory state.
    Other routes (analyze, clean, visualize, report) call this
    to access the current dataset without re-uploading it.
    """
    return _state


def _allowed(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _make_serialisable(obj):
    """
    Recursively convert a Python object to JSON-safe types.
    Pandas and NumPy use their own number types (np.int64, np.float64, etc.)
    that the JSON encoder doesn't understand — this converts them to plain
    Python int / float / None.
    """
    if isinstance(obj, dict):
        return {k: _make_serialisable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serialisable(i) for i in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    try:
        if pd.isna(obj):
            return None     # replace NaN / NaT with null in JSON
    except (TypeError, ValueError):
        pass
    return obj


@upload_bp.route("/upload", methods=["POST"])
def upload():
    """
    POST /upload
    Expects a multipart form with a field named "file".
    Returns JSON with filename, shape, column names, and a 10-row preview.
    """

    # Make sure a file was actually included in the request
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Reject unsupported file types early
    if not _allowed(file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}"}), 400

    # Sanitize the filename (removes ../ and other dangerous characters)
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Parse the file into a DataFrame using the right method for its type
    try:
        df = parse_file(filepath)
    except Exception as e:
        return jsonify({"error": f"Failed to parse file: {str(e)}"}), 422

    # Save to the shared state so other pages can use this dataset
    _state["filepath"]   = filepath
    _state["df"]         = df
    _state["cleaned_df"] = None   # reset any previous cleaning

    # Build a preview of the first 10 rows (replace NaN with None for JSON)
    preview_df = df.head(10).where(pd.notnull(df.head(10)), None)
    preview    = preview_df.to_dict(orient="records")

    return jsonify({
        "message":  "File uploaded successfully",
        "filename": filename,
        "rows":     int(df.shape[0]),
        "cols":     int(df.shape[1]),
        "columns":  df.columns.tolist(),
        "dtypes":   {col: str(dtype) for col, dtype in df.dtypes.items()},
        "preview":  _make_serialisable(preview),
    })
