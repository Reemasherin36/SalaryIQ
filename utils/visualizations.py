"""
utils/visualizations.py
Reusable Plotly chart factory functions for the LinkedIn Salary Predictor.
All functions return Plotly Figure objects ready for st.plotly_chart().
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import streamlit as st

# ── Brand Colors ──────────────────────────────────────────────────────────────
LINKEDIN_BLUE = "#0077B5"
LINKEDIN_DARK = "#004471"
ACCENT_GREEN = "#00A651"
ACCENT_ORANGE = "#F5A623"
ACCENT_RED = "#E34D3A"
PALETTE = [LINKEDIN_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED,
           "#6C5CE7", "#00CEC9", "#FDCB6E", "#E17055"]


def _apply_base_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply consistent LinkedIn-themed layout to any figure.

    Args:
        fig: Plotly Figure to update.
        title: Chart title string.

    Returns:
        Updated Figure with branded layout.
    """
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1A1A1A", family="Arial")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color="#333333"),
        margin=dict(t=50, b=40, l=40, r=20),
        legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#E0E0E0", borderwidth=1),
    )
    fig.update_xaxes(gridcolor="#F0F0F0", zeroline=False)
    fig.update_yaxes(gridcolor="#F0F0F0", zeroline=False)
    return fig


# ── Histogram ─────────────────────────────────────────────────────────────────

def plot_salary_histogram(df: pd.DataFrame, col: str = "normalized_salary",
                          title: str = "Salary Distribution") -> go.Figure:
    """Salary distribution histogram with KDE overlay.

    Args:
        df: DataFrame containing the salary column.
        col: Column name with salary values.
        title: Chart title.

    Returns:
        Plotly Figure.
    """
    clean = df[col].dropna()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=clean,
        nbinsx=60,
        marker_color=LINKEDIN_BLUE,
        opacity=0.75,
        name="Count",
        hovertemplate="Salary: $%{x:,.0f}<br>Count: %{y}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Annual Salary (USD)",
        yaxis_title="Number of Jobs",
        bargap=0.05,
    )
    return _apply_base_layout(fig, title)


# ── Box Plot ──────────────────────────────────────────────────────────────────

def plot_salary_boxplot(df: pd.DataFrame, x: str, y: str,
                        title: str = "Salary Distribution",
                        sort_by_median: bool = True) -> go.Figure:
    """Box plot of salary by a categorical variable, sorted by median.

    Args:
        df: Source DataFrame.
        x: Categorical column name.
        y: Numeric salary column name.
        title: Chart title.
        sort_by_median: Whether to sort categories by median value.

    Returns:
        Plotly Figure.
    """
    temp = df[[x, y]].dropna()
    if sort_by_median:
        order = temp.groupby(x)[y].median().sort_values().index.tolist()
    else:
        order = sorted(temp[x].unique().tolist())

    fig = px.box(
        temp, x=x, y=y,
        category_orders={x: order},
        color_discrete_sequence=[LINKEDIN_BLUE],
        points=False,
    )
    fig.update_layout(yaxis_title="Annual Salary (USD)", xaxis_title="")
    return _apply_base_layout(fig, title)


# ── Bar Chart ─────────────────────────────────────────────────────────────────

def plot_bar_chart(df: pd.DataFrame, x: str, y: str,
                   title: str = "", orientation: str = "v",
                   color: str = LINKEDIN_BLUE,
                   color_col: Optional[str] = None) -> go.Figure:
    """Generic bar chart factory.

    Args:
        df: Source DataFrame.
        x: Column for x-axis (or value in horizontal mode).
        y: Column for y-axis (or label in horizontal mode).
        title: Chart title.
        orientation: 'v' for vertical, 'h' for horizontal.
        color: Single bar colour hex string.
        color_col: Optional column for colour mapping.

    Returns:
        Plotly Figure.
    """
    if color_col:
        fig = px.bar(df, x=x, y=y, color=color_col,
                     orientation=orientation,
                     color_discrete_sequence=PALETTE)
    else:
        fig = px.bar(df, x=x, y=y, orientation=orientation,
                     color_discrete_sequence=[color])
    if orientation == "h":
        fig.update_layout(xaxis_title="", yaxis_title="")
    return _apply_base_layout(fig, title)


# ── Scatter ───────────────────────────────────────────────────────────────────

def plot_scatter(df: pd.DataFrame, x: str, y: str,
                 color_col: Optional[str] = None,
                 size_col: Optional[str] = None,
                 title: str = "") -> go.Figure:
    """Interactive scatter plot, optionally coloured and sized by columns.

    Args:
        df: Source DataFrame.
        x: X-axis column.
        y: Y-axis column.
        color_col: Optional column for point colour.
        size_col: Optional column for point size.
        title: Chart title.

    Returns:
        Plotly Figure.
    """
    fig = px.scatter(
        df, x=x, y=y,
        color=color_col, size=size_col,
        color_discrete_sequence=PALETTE,
        opacity=0.65,
        render_mode="webgl",
    )
    return _apply_base_layout(fig, title)


# ── Heatmap ───────────────────────────────────────────────────────────────────

def plot_heatmap(matrix_df: pd.DataFrame, title: str = "",
                 x_label: str = "", y_label: str = "") -> go.Figure:
    """Plotly heatmap from a pivot-style DataFrame.

    Args:
        matrix_df: 2D DataFrame (rows = y categories, columns = x categories).
        title: Chart title.
        x_label: X-axis label.
        y_label: Y-axis label.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure(data=go.Heatmap(
        z=matrix_df.values,
        x=matrix_df.columns.tolist(),
        y=matrix_df.index.tolist(),
        colorscale=[[0, "#E8F4FD"], [0.5, LINKEDIN_BLUE], [1, LINKEDIN_DARK]],
        hovertemplate=f"{x_label}: %{{x}}<br>{y_label}: %{{y}}<br>Value: %{{z:,.0f}}<extra></extra>",
    ))
    fig.update_layout(xaxis_title=x_label, yaxis_title=y_label)
    return _apply_base_layout(fig, title)


# ── Line Chart ────────────────────────────────────────────────────────────────

def plot_line_chart(df: pd.DataFrame, x: str, y: str,
                    title: str = "", color_col: Optional[str] = None) -> go.Figure:
    """Line chart for time-series or continuous data.

    Args:
        df: Source DataFrame.
        x: X-axis column (usually datetime or ordered category).
        y: Y-axis numeric column.
        title: Chart title.
        color_col: Optional column for multi-line colour grouping.

    Returns:
        Plotly Figure.
    """
    fig = px.line(df, x=x, y=y, color=color_col,
                  color_discrete_sequence=PALETTE,
                  markers=True)
    fig.update_traces(line_width=2.5)
    return _apply_base_layout(fig, title)


# ── Gauge Chart ───────────────────────────────────────────────────────────────

def plot_gauge_chart(predicted: float, min_val: float, max_val: float,
                     title: str = "Predicted Salary") -> go.Figure:
    """Gauge/speedometer chart showing predicted salary on a scale.

    Args:
        predicted: Model output salary value.
        min_val: Minimum of the gauge scale.
        max_val: Maximum of the gauge scale.
        title: Chart title.

    Returns:
        Plotly Figure.
    """
    mid = (min_val + max_val) / 2
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=predicted,
        number=dict(prefix="$", valueformat=",.0f", font=dict(size=28, color=LINKEDIN_DARK)),
        delta=dict(reference=mid, valueformat=",.0f",
                   increasing=dict(color=ACCENT_GREEN),
                   decreasing=dict(color=ACCENT_RED)),
        gauge=dict(
            axis=dict(range=[min_val, max_val],
                      tickformat="$,.0f",
                      tickfont=dict(size=11)),
            bar=dict(color=LINKEDIN_BLUE, thickness=0.3),
            bgcolor="white",
            steps=[
                dict(range=[min_val, min_val + (max_val - min_val) * 0.33], color="#E8F4FD"),
                dict(range=[min_val + (max_val - min_val) * 0.33,
                             min_val + (max_val - min_val) * 0.66], color="#BDD9EE"),
                dict(range=[min_val + (max_val - min_val) * 0.66, max_val], color="#8BC4E2"),
            ],
            threshold=dict(line=dict(color=ACCENT_GREEN, width=4), thickness=0.85, value=predicted),
        ),
        title=dict(text=title, font=dict(size=15)),
    ))
    fig.update_layout(height=300, margin=dict(t=40, b=10, l=20, r=20),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


# ── Salary Distribution with Markers ─────────────────────────────────────────

def plot_salary_distribution_with_markers(series: pd.Series,
                                          current: float, target: float,
                                          median: float, p75: float,
                                          title: str = "Your Salary vs Market") -> go.Figure:
    """Histogram with vertical lines for current, target, median, and 75th percentile.

    Args:
        series: Full salary distribution Series.
        current: User's current salary.
        target: User's target salary.
        median: Market median salary.
        p75: Market 75th-percentile salary.
        title: Chart title.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=series.dropna(),
        nbinsx=60,
        marker_color=LINKEDIN_BLUE,
        opacity=0.5,
        name="Market Distribution",
    ))
    markers = [
        (current, ACCENT_ORANGE, "Your Current"),
        (target, ACCENT_GREEN, "Your Target"),
        (median, "#6C5CE7", "Market Median"),
        (p75, ACCENT_RED, "75th Pct"),
    ]
    for val, color, name in markers:
        if val and val > 0:
            fig.add_vline(x=val, line_color=color, line_width=2.5,
                          line_dash="dash",
                          annotation_text=name,
                          annotation_position="top right",
                          annotation_font_color=color)
    fig.update_layout(xaxis_title="Annual Salary (USD)", yaxis_title="Jobs", bargap=0.05)
    return _apply_base_layout(fig, title)


# ── Feature Importance ────────────────────────────────────────────────────────

def plot_feature_importance(feature_names: list, importances: list,
                             title: str = "Top Feature Importances") -> go.Figure:
    """Horizontal bar chart of model feature importances.

    Args:
        feature_names: List of feature label strings.
        importances: Corresponding importance values.
        title: Chart title.

    Returns:
        Plotly Figure.
    """
    df = pd.DataFrame({"Feature": feature_names, "Importance": importances})
    df = df.sort_values("Importance", ascending=True).tail(10)
    fig = px.bar(df, x="Importance", y="Feature", orientation="h",
                 color="Importance", color_continuous_scale=["#E8F4FD", LINKEDIN_BLUE])
    fig.update_layout(coloraxis_showscale=False, yaxis_title="")
    return _apply_base_layout(fig, title)


# ── Actual vs Predicted ───────────────────────────────────────────────────────

def plot_actual_vs_predicted(y_test: pd.Series, y_pred: np.ndarray) -> go.Figure:
    """Scatter plot comparing actual vs. predicted salary values.

    Args:
        y_test: Actual salary values.
        y_pred: Model predicted salary values.

    Returns:
        Plotly Figure with perfect-prediction diagonal line.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=y_test, y=y_pred,
        mode="markers",
        marker=dict(color=LINKEDIN_BLUE, opacity=0.4, size=5),
        name="Predictions",
        hovertemplate="Actual: $%{x:,.0f}<br>Predicted: $%{y:,.0f}<extra></extra>",
    ))
    lo = min(y_test.min(), y_pred.min())
    hi = max(y_test.max(), y_pred.max())
    fig.add_trace(go.Scatter(
        x=[lo, hi], y=[lo, hi],
        mode="lines",
        line=dict(color=ACCENT_GREEN, dash="dash", width=2),
        name="Perfect Prediction",
    ))
    fig.update_layout(xaxis_title="Actual Salary", yaxis_title="Predicted Salary")
    return _apply_base_layout(fig, "Actual vs Predicted Salary")


# ── Residuals ─────────────────────────────────────────────────────────────────

def plot_residuals(y_test: pd.Series, y_pred: np.ndarray) -> go.Figure:
    """Histogram of prediction residuals (actual − predicted).

    Args:
        y_test: Actual salary values.
        y_pred: Model predicted salary values.

    Returns:
        Plotly Figure.
    """
    residuals = np.array(y_test) - y_pred
    fig = go.Figure(go.Histogram(
        x=residuals,
        nbinsx=50,
        marker_color=ACCENT_ORANGE,
        opacity=0.75,
        hovertemplate="Residual: $%{x:,.0f}<br>Count: %{y}<extra></extra>",
    ))
    fig.add_vline(x=0, line_color=LINKEDIN_DARK, line_width=2, line_dash="dash")
    fig.update_layout(xaxis_title="Residual (Actual − Predicted)", yaxis_title="Count")
    return _apply_base_layout(fig, "Residuals Distribution")


# ── Pie / Donut ───────────────────────────────────────────────────────────────

def plot_donut(labels: list, values: list, title: str = "") -> go.Figure:
    """Donut (pie) chart for categorical distributions.

    Args:
        labels: Category label list.
        values: Corresponding counts or percentages.
        title: Chart title.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.45,
        marker_colors=PALETTE,
        hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>",
    ))
    fig.update_layout(showlegend=True,
                      legend=dict(orientation="v", xanchor="right", x=1.1))
    return _apply_base_layout(fig, title)


# ── Word Cloud ────────────────────────────────────────────────────────────────

def plot_wordcloud(text_series: pd.Series, title: str = "Skills Word Cloud"):
    """Generate a word cloud image from a text Series and render in Streamlit.

    Args:
        text_series: Series of strings (skill names, words).
        title: Section heading shown above the image.
    """
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        text = " ".join(text_series.dropna().astype(str).tolist())
        wc = WordCloud(
            width=900, height=450,
            background_color="white",
            colormap="Blues",
            max_words=120,
            collocations=False,
        ).generate(text)
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        plt.tight_layout(pad=0)
        st.subheader(title)
        st.pyplot(fig)
        plt.close(fig)
    except ImportError:
        st.info("Install `wordcloud` to enable the skill cloud visualisation.")
