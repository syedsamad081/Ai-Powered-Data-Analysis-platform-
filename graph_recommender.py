"""
services/graph_recommender.py  —  Auto-generates charts from the dataset.

This module looks at the columns in the DataFrame and automatically decides
which chart types make sense, then renders them as PNG images using
Matplotlib and Seaborn.

Charts are returned as base64-encoded PNG strings so the browser can display
them directly in an <img> tag without any separate image files.

Charts generated (depending on what columns exist):
  Histogram    — distribution of each numeric column (up to 3)
  Bar chart    — average of a numeric column grouped by a categorical column
  Scatter plot — relationship between two numeric columns
  Line chart   — a numeric value over time (requires a datetime column)
  Pie chart    — proportion of top categories in a categorical column
  Heatmap      — correlation matrix of all numeric columns (requires >= 3)
  Boxplot      — spread and outliers for numeric columns (up to 6)

Colour palette used throughout: #452829 · #57595B · #E8D1C5 · #F3E8DF
"""

import io
import base64
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")   # use non-interactive backend (no screen/window needed)
import matplotlib.pyplot as plt
import seaborn as sns

# ── Colour palette (matches the frontend CSS palette) ─────────
PALETTE_DARK  = "#452829"   # dark brown  — primary chart colour
PALETTE_GREY  = "#57595B"   # medium grey — secondary colour
PALETTE_WARM  = "#E8D1C5"   # warm beige  — light fills
PALETTE_CREAM = "#F3E8DF"   # cream       — backgrounds

# Apply a light theme that matches the website's look
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "figure.facecolor":  PALETTE_CREAM,   # outside the axes
    "axes.facecolor":    "#FFFFFF",        # inside the axes
    "savefig.facecolor": PALETTE_CREAM,
    "axes.edgecolor":    PALETTE_GREY,
    "axes.labelcolor":   PALETTE_DARK,
    "xtick.color":       PALETTE_GREY,
    "ytick.color":       PALETTE_GREY,
    "text.color":        PALETTE_DARK,
    "axes.titlecolor":   PALETTE_DARK,
    "grid.color":        PALETTE_WARM,
    "axes.titleweight":  "bold",
    "font.size":         10,
})


def recommend(df: pd.DataFrame) -> list:
    """
    Analyse the DataFrame and return a list of chart objects.

    Each chart object contains:
      id          — unique identifier string
      type        — chart type (histogram, bar, scatter, etc.)
      title       — human-readable chart title
      description — one-sentence explanation of what the chart shows
      image       — base64-encoded PNG data URI ("data:image/png;base64,...")
    """
    charts = []

    # Separate columns by type so we know what charts are possible
    numeric_cols     = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()

    # ── 1. Histograms — one per numeric column (max 3) ────────
    # Shows how values are distributed — useful for spotting skew and outliers
    for col in numeric_cols[:3]:
        values = df[col].dropna()
        if len(values) == 0:
            continue

        fig, ax = plt.subplots(figsize=(7, 4))
        sns.histplot(values, bins=20, kde=True,
                     color=PALETTE_DARK, edgecolor=PALETTE_CREAM, ax=ax)
        ax.set_title(f"Distribution of {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Frequency")

        charts.append({
            "id":          f"hist_{col}",
            "type":        "histogram",
            "title":       f"Distribution of {col}",
            "description": f"Histogram with KDE curve for '{col}'. "
                           "Shows how values are spread — symmetry suggests normal distribution.",
            "image":       _fig_to_b64(fig),
        })

    # ── 2. Bar chart — categorical vs numeric ─────────────────
    # Shows the average of a number broken down by category
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        grouped = (df.groupby(cat_col)[num_col]
                     .mean().dropna()
                     .sort_values(ascending=False)
                     .head(15))

        if 1 < len(grouped):
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.barplot(x=grouped.index.astype(str), y=grouped.values,
                        ax=ax, color=PALETTE_GREY, edgecolor=PALETTE_DARK)
            ax.set_title(f"Average {num_col} by {cat_col}")
            ax.set_xlabel(cat_col)
            ax.set_ylabel(f"Avg {num_col}")
            plt.xticks(rotation=45, ha="right")

            charts.append({
                "id":          f"bar_{cat_col}_{num_col}",
                "type":        "bar",
                "title":       f"Average {num_col} by {cat_col}",
                "description": f"Average of '{num_col}' for each category in '{cat_col}' (top 15).",
                "image":       _fig_to_b64(fig),
            })

    # ── 3. Scatter plot — two numeric columns ─────────────────
    # Reveals whether two columns have a relationship (correlation)
    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        sample = df[[x_col, y_col]].dropna()
        if len(sample) > 300:
            sample = sample.sample(300, random_state=42)   # limit to 300 for speed

        fig, ax = plt.subplots(figsize=(7, 4))
        sns.scatterplot(data=sample, x=x_col, y=y_col,
                        ax=ax, color=PALETTE_DARK, alpha=0.65, edgecolor="none")
        ax.set_title(f"{x_col} vs {y_col}")

        charts.append({
            "id":          f"scatter_{x_col}_{y_col}",
            "type":        "scatter",
            "title":       f"{x_col} vs {y_col}",
            "description": f"Scatter plot showing the relationship between '{x_col}' and '{y_col}'. "
                           "A clear pattern suggests correlation.",
            "image":       _fig_to_b64(fig),
        })

    # ── 4. Line chart — numeric value over time ───────────────
    # Only generated when a datetime column exists
    if datetime_cols and numeric_cols:
        time_col = datetime_cols[0]
        val_col  = numeric_cols[0]
        ts = (df[[time_col, val_col]].dropna()
                .sort_values(time_col)
                .head(200))

        if len(ts) > 1:
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.lineplot(data=ts, x=time_col, y=val_col,
                         ax=ax, color=PALETTE_DARK, linewidth=2)
            ax.set_title(f"{val_col} over {time_col}")
            plt.xticks(rotation=45, ha="right")

            charts.append({
                "id":          f"line_{time_col}_{val_col}",
                "type":        "line",
                "title":       f"{val_col} over {time_col}",
                "description": f"Time series showing how '{val_col}' changes over '{time_col}'.",
                "image":       _fig_to_b64(fig),
            })

    # ── 5. Pie chart — top categories ─────────────────────────
    # Shows what percentage of the data each category takes up
    if categorical_cols:
        cat_col = categorical_cols[0]
        vc      = df[cat_col].value_counts().head(8)

        if 1 < len(vc) <= 8:
            fig, ax = plt.subplots(figsize=(6, 6))
            # Build a gradient palette from the 4 brand colours
            colors = sns.blend_palette(
                [PALETTE_DARK, PALETTE_GREY, PALETTE_WARM, PALETTE_CREAM],
                n_colors=len(vc),
            )
            ax.pie(vc.values, labels=vc.index, autopct="%1.1f%%",
                   colors=colors,
                   textprops={"color": PALETTE_DARK},
                   wedgeprops={"edgecolor": PALETTE_CREAM, "linewidth": 1.5})
            ax.set_title(f"Proportion of {cat_col}")

            charts.append({
                "id":          f"pie_{cat_col}",
                "type":        "pie",
                "title":       f"Proportion of {cat_col}",
                "description": f"Share of the top {len(vc)} categories in '{cat_col}'.",
                "image":       _fig_to_b64(fig),
            })

    # ── 6. Correlation heatmap — all numeric columns ──────────
    # Requires at least 3 numeric columns.
    # Values close to +1 = strong positive correlation,
    # close to -1 = strong negative, close to 0 = no relationship.
    if len(numeric_cols) >= 3:
        corr = df[numeric_cols].corr()
        fig, ax = plt.subplots(figsize=(8, 6))
        cmap = sns.blend_palette(
            [PALETTE_DARK, PALETTE_WARM, PALETTE_CREAM, PALETTE_WARM, PALETTE_GREY],
            as_cmap=True,
        )
        sns.heatmap(corr, annot=True, cmap=cmap, center=0,
                    fmt=".2f", ax=ax,
                    linewidths=0.5, linecolor=PALETTE_CREAM,
                    cbar_kws={"shrink": 0.8},
                    annot_kws={"color": PALETTE_DARK})
        ax.set_title("Correlation Heatmap")

        charts.append({
            "id":          "heatmap_corr",
            "type":        "heatmap",
            "title":       "Correlation Heatmap",
            "description": "Pearson correlation between all numeric columns. "
                           "Dark cells = strong relationship, light cells = weak relationship.",
            "image":       _fig_to_b64(fig),
        })

    # ── 7. Boxplot — numeric spread and outliers ──────────────
    # Shows median, quartiles, and any outlier points for each numeric column
    if numeric_cols:
        cols_to_plot = numeric_cols[:6]   # limit to 6 columns for readability
        fig, ax = plt.subplots(figsize=(7, 4))
        box_palette = sns.blend_palette(
            [PALETTE_DARK, PALETTE_GREY, PALETTE_WARM],
            n_colors=len(cols_to_plot),
        )
        sns.boxplot(data=df[cols_to_plot], ax=ax,
                    palette=box_palette, linecolor=PALETTE_DARK)
        ax.set_title("Numeric Distributions (Boxplot)")
        plt.xticks(rotation=30, ha="right")

        charts.append({
            "id":          "boxplot_numeric",
            "type":        "boxplot",
            "title":       "Numeric Distributions",
            "description": f"Boxplots for {len(cols_to_plot)} numeric columns. "
                           "Points beyond the whiskers are outliers.",
            "image":       _fig_to_b64(fig),
        })

    return charts


def _fig_to_b64(fig) -> str:
    """
    Save a Matplotlib figure to memory as PNG and encode it as a base64 string.
    The result can be used directly as the src attribute of an HTML <img> tag.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight",
                dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)   # free memory — important when generating many charts
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")
