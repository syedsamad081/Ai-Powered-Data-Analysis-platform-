"""
routes/report.py  —  Handles AI report generation.

When the user clicks "Generate AI Report":
  1. The current dataset is profiled (row counts, statistics, missing values, etc.)
  2. Charts are recommended and their metadata (type, title, description) is extracted
     — the actual image data is stripped out because it's too large to send to Gemini
  3. Both the profile and chart metadata are passed to Gemini via the ai_report service
  4. Gemini writes a structured Markdown report and returns it
  5. The Markdown and a summary of the profile are sent back to the browser

If the Gemini API key is missing or quota is exceeded, a detailed auto-generated
report is returned instead (built from the actual dataset statistics).
"""

from flask import Blueprint, jsonify
from services.data_processor  import profile
from services.graph_recommender import recommend
from services.ai_report        import generate
from routes.upload             import get_state

report_bp = Blueprint("report", __name__)


@report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """
    POST /generate-report
    No request body needed — uses the dataset already in memory from /upload.
    Returns { report: "...(Markdown)...", profile_summary: {...} }
    """
    state = get_state()

    # Use the cleaned dataset if available, otherwise the original upload
    df = state.get("cleaned_df")
    if df is None:
        df = state.get("df")

    if df is None:
        return jsonify({"error": "No dataset loaded. Please upload a file first."}), 400

    try:
        # Step 1 — Profile the dataset (statistics, missing values, etc.)
        prof = profile(df)

        # Step 2 — Get chart recommendations to describe what visualizations exist
        charts = recommend(df)

        # Step 3 — Strip the base64 image data — Gemini only needs the chart descriptions,
        #           not the actual PNG images (they would make the prompt too large)
        charts_meta = [
            {"type": c["type"], "title": c["title"], "description": c["description"]}
            for c in charts
        ]

        # Step 4 — Call Gemini (or fall back to auto-generated report)
        report_md = generate(prof, charts_meta)

    except Exception as e:
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500

    return jsonify({
        "report": report_md,
        # Also send a brief profile summary so the frontend can display stat chips
        "profile_summary": {
            "rows":               prof["rows"],
            "cols":               prof["cols"],
            "numeric_columns":    prof["numeric_columns"],
            "categorical_columns":prof["categorical_columns"],
            "duplicate_rows":     prof["duplicate_rows"],
        },
    })
