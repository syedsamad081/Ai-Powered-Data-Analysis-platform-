"""
services/ai_report.py  —  Generates the AI analysis report using Google Gemini.

How it works:
  1. A detailed prompt is built from the dataset profile and chart descriptions
  2. The prompt is sent to the Gemini API
  3. Gemini returns a structured Markdown report
  4. If Gemini is unavailable (quota exceeded, no API key, etc.),
     a detailed auto-generated report is built from the actual dataset statistics

The report is returned as a Markdown string. The frontend converts it to HTML
and displays it in the AI Report page.

To get your free Gemini API key: https://aistudio.google.com/apikey
Add it to your .env file as:  GEMINI_API_KEY=your_key_here
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load the .env file so GEMINI_API_KEY is available
load_dotenv()


def generate(profile: dict, charts: list) -> str:
    """
    Generate the analysis report.

    If a valid Gemini API key is configured, Gemini writes the report.
    Otherwise, a detailed report is auto-generated from the profile statistics.

    Args:
        profile — output from data_processor.profile()
        charts  — list of chart metadata dicts (type, title, description)
                  NOTE: image data must be stripped before passing here

    Returns:
        A Markdown-formatted report string.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")

    # Skip Gemini entirely if no API key has been configured
    if not api_key or api_key == "your_gemini_api_key_here":
        return _fallback_report(profile)

    genai.configure(api_key=api_key)

    # Try models in order from lightest (cheapest quota) to heavier
    # This maximises the chance of success on free-tier API keys
    models_to_try = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
    ]

    # ── Build the prompt ─────────────────────────────────────
    # Summarise the chart types so Gemini can reference them in the report
    chart_summaries = "\n".join(
        f"- {c['type'].title()}: {c['title']} — {c['description']}"
        for c in charts
    )

    # List columns that have missing values
    missing_summary = ", ".join(
        f"{col}: {info['pct']}% missing"
        for col, info in profile.get("missing_values", {}).items()
        if info["count"] > 0
    ) or "No missing values"

    prompt = f"""
You are an expert data analyst. A user has uploaded a dataset with the following properties:

**Dataset Summary:**
- Rows: {profile.get('rows', 'N/A')}
- Columns: {profile.get('cols', 'N/A')}
- Numeric Columns: {', '.join(profile.get('numeric_columns', [])) or 'None'}
- Categorical Columns: {', '.join(profile.get('categorical_columns', [])) or 'None'}
- Duplicate Rows: {profile.get('duplicate_rows', 0)}
- Missing Values: {missing_summary}

**Statistical Highlights (from describe):**
{json.dumps(profile.get('describe', {}), indent=2)[:2000]}

**Recommended Visualizations:**
{chart_summaries or 'No charts generated.'}

Generate a professional, structured data analysis report in Markdown format with these sections:

# Dataset Overview
Briefly describe the shape, column types, and overall data quality.

# Key Insights
List 5–7 numerical or categorical insights derived from the statistics.

# Trends & Patterns
Describe trends, patterns, or relationships visible in the data and recommended charts.

# Observations
Note data quality issues (missing data, duplicates, potential outliers).

# Recommendations
4–6 actionable recommendations for further analysis, modelling, or cleaning.

Keep the tone professional and concise. Use bullet points where appropriate.
"""

    # ── Try each model ────────────────────────────────────────
    last_error = None

    for model_name in models_to_try:
        try:
            model    = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text   # success — return the Gemini report

        except Exception as e:
            err = str(e)

            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                # Quota exceeded — no point trying other models for this API key
                last_error = err
                break

            # Model not found or other issue — try the next model in the list
            last_error = err
            continue

    # ── All models failed — return a detailed auto-generated report ───
    if last_error and ("429" in last_error or "quota" in last_error.lower()):
        note = (
            "\n\n> **Note:** Gemini API quota exhausted for today. "
            "This report was generated automatically from your dataset statistics. "
            "Quota resets daily — or get a new key from https://aistudio.google.com/apikey.\n"
        )
    else:
        note = f"\n\n> **Note:** Gemini was unavailable ({str(last_error)[:100]}). Auto-generated report shown.\n"

    return _fallback_report(profile) + note


def _fallback_report(profile: dict) -> str:
    """
    Build a detailed report entirely from the dataset statistics.
    This runs when Gemini is unavailable or not configured.
    All numbers come from the real data — this is not a generic template.
    """
    rows        = profile.get("rows", 0)
    cols        = profile.get("cols", 0)
    numeric     = profile.get("numeric_columns", [])
    categorical = profile.get("categorical_columns", [])
    datetime_c  = profile.get("datetime_columns", [])
    duplicates  = profile.get("duplicate_rows", 0)
    missing     = profile.get("missing_values", {})
    describe    = profile.get("describe", {})
    unique      = profile.get("unique_counts", {})

    # Calculate overall completeness
    missing_cols  = [c for c, v in missing.items() if v["count"] > 0]
    total_missing = sum(v["count"] for v in missing.values())
    completeness  = round((1 - total_missing / max(rows * cols, 1)) * 100, 1)

    # ── Key Insights — pulled directly from real statistics ───
    insights = []
    insights.append(
        f"The dataset contains **{rows:,} rows** and **{cols} columns** "
        f"({len(numeric)} numeric, {len(categorical)} categorical"
        + (f", {len(datetime_c)} datetime" if datetime_c else "") + ")."
    )
    insights.append(
        f"Data completeness is **{completeness}%** — "
        + (f"{total_missing:,} missing cells across {len(missing_cols)} column(s)."
           if missing_cols else "no missing values detected.")
    )
    insights.append(
        f"**{duplicates}** duplicate row(s) detected"
        + (" — removal recommended before modelling." if duplicates else " — all rows are unique.")
    )

    # Add per-column stats for the first 4 numeric columns
    for col in numeric[:4]:
        stats = describe.get(col, {})
        mean  = stats.get("mean")
        std   = stats.get("std")
        mn    = stats.get("min")
        mx    = stats.get("max")
        if mean is not None and std is not None:
            cv = round(abs(std / mean) * 100, 1) if mean else 0
            insights.append(
                f"**{col}**: mean = {mean:,.3f}, std = {std:,.3f} "
                f"(CV {cv}%), range [{mn:,.3f} → {mx:,.3f}]."
            )

    # Add unique-count info for categorical columns
    for col in categorical[:2]:
        u = unique.get(col)
        if u is not None:
            insights.append(f"**{col}** has **{u}** unique categories.")

    # ── Trends & Patterns ─────────────────────────────────────
    trends = []

    # Identify high-variance columns (coefficient of variation > 50%)
    high_cv_cols = []
    for col in numeric:
        stats = describe.get(col, {})
        mean  = stats.get("mean")
        std   = stats.get("std")
        if mean and std and mean != 0 and abs(std / mean) > 0.5:
            high_cv_cols.append(col)
    if high_cv_cols:
        trends.append(
            f"High variability (CV > 50%) in: **{', '.join(high_cv_cols)}** — "
            "these columns may contain outliers or represent multiple sub-groups."
        )

    # Identify skewed columns (mean deviates from median by >30%)
    skewed = []
    for col in numeric:
        stats = describe.get(col, {})
        mean  = stats.get("mean")
        p50   = stats.get("50%")
        if mean is not None and p50 is not None and p50 != 0:
            ratio = mean / p50
            if ratio > 1.3 or ratio < 0.7:
                skewed.append(col)
    if skewed:
        trends.append(
            f"Potential skew detected in: **{', '.join(skewed)}** "
            "(mean deviates from median — distribution may not be symmetric)."
        )

    if len(numeric) >= 2:
        trends.append(
            "Inspect the **Correlation Heatmap** on the Visualization page "
            "to find relationships between numeric columns."
        )

    if categorical:
        trends.append(
            f"Categorical column **{categorical[0]}** has "
            f"{unique.get(categorical[0], '?')} unique values — "
            "check the Bar and Pie charts for distribution patterns."
        )

    if not trends:
        trends.append(
            "No strong statistical anomalies detected at summary level. "
            "Explore the visualization charts for deeper pattern discovery."
        )

    # ── Observations — data quality notes ────────────────────
    observations = []
    severe   = [c for c, v in missing.items() if v["pct"] > 50]
    moderate = [c for c, v in missing.items() if 10 < v["pct"] <= 50]
    low      = [c for c, v in missing.items() if 0 < v["pct"] <= 10]

    if severe:
        observations.append(f"**Severe missing data (>50%)** in: {', '.join(severe)} — consider dropping these columns.")
    if moderate:
        observations.append(f"**Moderate missing data (10–50%)** in: {', '.join(moderate)} — imputation recommended.")
    if low:
        observations.append(f"**Low missing data (<10%)** in: {', '.join(low)} — safe to fill with mean/median/mode.")
    if not missing_cols:
        observations.append("No missing values — dataset is complete and ready for analysis.")
    if duplicates:
        observations.append(f"**{duplicates}** duplicate rows present — remove before training any model.")
    if high_cv_cols:
        observations.append(
            f"High-variance columns ({', '.join(high_cv_cols)}) may benefit "
            "from outlier removal using the IQR method."
        )

    # ── Recommendations ───────────────────────────────────────
    recs = []
    if missing_cols or duplicates:
        recs.append("Apply **Data Cleaning** (drop duplicates, fill missing values) before analysis.")
    if high_cv_cols or skewed:
        recs.append("Use **Remove Outliers (IQR)** on skewed / high-variance columns.")
    if numeric:
        recs.append("Apply **Normalize Numeric Columns** if using distance-based models (KNN, SVM).")
    if categorical:
        recs.append("One-hot encode or label-encode categorical columns before ML pipelines.")
    recs.append("Download the **Cleaned CSV** and continue analysis in Jupyter or a similar tool.")
    recs.append("Inspect the **Correlation Heatmap** and **Boxplots** for deeper insights.")

    # ── Format the report as Markdown ─────────────────────────
    def bullets(items):
        return "\n".join(f"- {i}" for i in items)

    def numbered(items):
        return "\n".join(f"{i + 1}. {v}" for i, v in enumerate(items))

    return f"""# Dataset Overview

This dataset contains **{rows:,} rows** across **{cols} columns**.

| Property | Value |
|---|---|
| Numeric columns | {len(numeric)} — {', '.join(numeric) or 'None'} |
| Categorical columns | {len(categorical)} — {', '.join(categorical) or 'None'} |
| Datetime columns | {len(datetime_c)} — {', '.join(datetime_c) or 'None'} |
| Duplicate rows | {duplicates} |
| Missing cells | {total_missing:,} ({100 - completeness:.1f}% of data) |
| Data completeness | {completeness}% |

---

# Key Insights

{bullets(insights)}

---

# Trends & Patterns

{bullets(trends)}

---

# Observations

{bullets(observations)}

---

# Recommendations

{numbered(recs)}
"""
