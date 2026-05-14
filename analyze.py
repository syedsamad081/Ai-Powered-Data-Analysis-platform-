"""
routes/analyze.py  —  Handles data profiling.

When the user clicks "Run Analysis" on the Data Profile page, this route:
  1. Gets the current dataset from memory (cleaned version if available, otherwise original)
  2. Passes it to the profiler in services/data_processor.py
  3. Returns a JSON object with statistics, missing values, data types, etc.

The frontend (profile.js) then displays this as stat cards, progress bars, and a table.
"""

from flask import Blueprint, jsonify
from services.data_processor import profile
from routes.upload import get_state

analyze_bp = Blueprint("analyze", __name__)


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    POST /analyze
    No request body needed — uses the dataset already in memory from /upload.
    Returns a full statistical profile as JSON.
    """
    state = get_state()

    # Use the cleaned dataset if the user has already applied cleaning,
    # otherwise fall back to the original uploaded dataset
    df = state.get("cleaned_df")
    if df is None:
        df = state.get("df")

    # If no dataset is loaded yet, tell the user to upload first
    if df is None:
        return jsonify({"error": "No dataset loaded. Please upload a file first."}), 400

    try:
        stats = profile(df)
    except Exception as e:
        return jsonify({"error": f"Profiling failed: {str(e)}"}), 500

    return jsonify(stats)
