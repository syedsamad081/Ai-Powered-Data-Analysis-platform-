"""
routes/visualize.py  —  Handles chart generation.

When the user clicks "Generate Charts" on the Visualize page:
  1. The current dataset is passed to the graph recommender
  2. The recommender automatically picks the best chart types based on the data
     (histograms for numeric columns, bar charts for categorical vs numeric, etc.)
  3. Each chart is rendered server-side using Matplotlib and Seaborn
  4. The charts are encoded as base64 PNG images and returned as JSON
  5. The browser displays them as <img> tags — no Chart.js needed

Chart types that may be generated:
  histogram  — distribution of each numeric column
  bar        — average of a numeric column grouped by a category
  scatter    — relationship between two numeric columns
  line       — numeric column over time (only if a datetime column exists)
  pie        — proportion of top categories
  heatmap    — correlation matrix between all numeric columns
  boxplot    — spread and outliers across numeric columns
"""

from flask import Blueprint, jsonify
from services.graph_recommender import recommend
from routes.upload import get_state

visualize_bp = Blueprint("visualize", __name__)


@visualize_bp.route("/visualize", methods=["POST"])
def visualize():
    """
    POST /visualize
    No request body needed — uses the dataset already in memory from /upload.
    Returns { chart_count: N, charts: [ { id, type, title, description, image }, ... ] }
    where image is a base64-encoded PNG data URI.
    """
    state = get_state()

    # Use the cleaned dataset if the user has already cleaned the data,
    # otherwise use the original upload
    df = state.get("cleaned_df")
    if df is None:
        df = state.get("df")

    if df is None:
        return jsonify({"error": "No dataset loaded. Please upload a file first."}), 400

    try:
        charts = recommend(df)
    except Exception as e:
        return jsonify({"error": f"Visualisation failed: {str(e)}"}), 500

    return jsonify({
        "chart_count": len(charts),
        "charts":      charts,
    })
