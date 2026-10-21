"""Poll Results Visualizer - Interactive Streamlit Web Application.

A professional, end-to-end dashboard for survey data ingestion, validation,
cleaning, exploratory data analysis, segment comparison, and automated reporting.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.analytics import (
    calculate_question_breakdown,
    calculate_segment_breakdown,
    calculate_submission_timeline,
    generate_automated_insights,
    generate_summary_table,
    get_kpis,
)
from src.data_cleaning import (
    REQUIRED_COLUMNS,
    clean_poll_data,
    map_columns,
    normalize_column_names,
    validate_columns,
)
from src.synthetic_data import DEFAULT_POLL_CONFIG, generate_synthetic_poll_data

# Page Configuration
st.set_page_config(
    page_title="Poll Results Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Modern, Polished Styling
st.markdown(
    """
    <style>
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    /* Headers and Badges */
    .app-header {
        margin-bottom: 1.5rem;
    }
    .badge-sample {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
    }
    .badge-synthetic {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
    }
    .badge-upload {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
    }
    /* Insights Callout Box */
    .insight-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
        border-left: 4px solid #10b981;
        padding: 16px 20px;
        border-radius: 6px;
        margin-bottom: 16px;
    }
    .caution-box {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 14px;
        font-size: 0.92rem;
    }
    .limitation-box {
        background: #f1f5f9;
        border-left: 4px solid #64748b;
        padding: 12px 16px;
        border-radius: 6px;
        margin-top: 14px;
        font-size: 0.88rem;
        color: #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_bundled_sample() -> Tuple[pd.DataFrame, str]:
    """Load the bundled sample CSV file."""
    sample_file = ROOT_DIR / "data" / "sample_poll_responses.csv"
    if sample_file.exists():
        df = pd.read_csv(sample_file)
        return df, "Bundled Sample Dataset (N=800)"
    # Fallback to generating it if missing
    df = generate_synthetic_poll_data(num_respondents=200, random_seed=42)
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(sample_file, index=False)
    return df, "Bundled Sample Dataset (Auto-generated)"


def format_markdown_report(
    kpis: Dict[str, Any],
    insights: Dict[str, Any],
    summary_df: pd.DataFrame,
    source_name: str,
) -> str:
    """Generate a clean downloadable Markdown summary report."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = f"""# Poll Results Visualizer — Analytical Report
**Generated on:** {now_str}  
**Data Source:** {source_name}  

---

## 1. Key Performance Indicators
- **Total Valid Responses:** {kpis['total_responses']:,}
- **Unique Respondents:** {kpis['unique_respondents']:,}
- **Number of Poll Questions:** {kpis['num_questions']}
- **Distinct Answers Recorded:** {kpis['num_answers']}
- **Demographic Segments:** {kpis['num_regions']} Regions | {kpis['num_age_groups']} Age Groups
- **Submission Date Range:** {kpis['date_min'] or 'N/A'} to {kpis['date_max'] or 'N/A'}

---

## 2. Automated Insights & Key Findings
- **Focus Scope:** {insights['question']}
- **Primary Finding:** {insights['primary_finding']}
- **Demographic Highlight:** {insights.get('demographic_highlight', 'N/A')}
- **Secondary Finding:** {insights.get('secondary_finding', 'N/A')}

### Methodological Limitation
> {insights['limitation_statement']}

---

## 3. Question & Answer Breakdown Summary Table
| Poll Question | Answer Option | Count | Total Question Responses | Percentage (%) |
|---|---|---|---|---|
"""
    for _, row in summary_df.iterrows():
        md += f"| {row['poll_question']} | {row['answer']} | {row['response_count']:,} | {row['question_total']:,} | {row['percentage']}% |\n"

    md += "\n---\n*Report generated via Poll Results Visualizer.*"
    return md


# -------------------------------------------------------------
# SIDEBAR: DATA INPUT & CONFIGURATION
# -------------------------------------------------------------
st.sidebar.title("⚙️ Data Configuration")

input_mode = st.sidebar.radio(
    "Choose Data Source:",
    ["Bundled Sample Dataset", "Generate Synthetic Data", "Upload CSV File"],
    index=0,
)

raw_df: Optional[pd.DataFrame] = None
data_source_label = "Sample"
source_badge_html = '<span class="badge-sample">Bundled Sample Data</span>'

if input_mode == "Bundled Sample Dataset":
    raw_df, label = load_bundled_sample()
    data_source_label = "Bundled Sample"
    source_badge_html = '<span class="badge-sample">📁 Bundled Sample Data (Pre-loaded)</span>'
    st.sidebar.success("Loaded default survey response dataset.")

elif input_mode == "Generate Synthetic Data":
    data_source_label = "Synthetic"
    source_badge_html = '<span class="badge-synthetic">🧪 Synthetic Simulation</span>'
    st.sidebar.markdown("**Simulation Parameters:**")
    n_respondents = st.sidebar.slider("Number of Respondents", min_value=50, max_value=1000, value=250, step=25)
    seed = st.sidebar.number_input("Random Seed", value=42, step=1)
    inject_noise = st.sidebar.checkbox(
        "Inject Minor Imperfections",
        value=False,
        help="Introduces duplicate rows, trailing whitespace, and an invalid timestamp to test the data cleaning pipeline.",
    )

    if st.sidebar.button("Generate Fresh Dataset", use_container_width=True) or "synthetic_df" not in st.session_state:
        st.session_state.synthetic_df = generate_synthetic_poll_data(
            num_respondents=n_respondents,
            random_seed=int(seed),
            add_noise=inject_noise,
        )
    raw_df = st.session_state.synthetic_df
    st.sidebar.info(f"Generated {len(raw_df)} response rows from {n_respondents} simulated participants.")

elif input_mode == "Upload CSV File":
    data_source_label = "Uploaded"
    source_badge_html = '<span class="badge-upload">📤 User Uploaded CSV</span>'
    uploaded_file = st.sidebar.file_uploader(
        "Upload Poll Responses CSV",
        type=["csv"],
        help="Upload a standard poll CSV or a Google Forms export.",
    )

    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            st.sidebar.success(f"Loaded file with {len(uploaded_df)} rows and {len(uploaded_df.columns)} columns.")

            # Check if columns match or need mapping
            norm_df = normalize_column_names(uploaded_df)
            is_valid, missing = validate_columns(norm_df)

            if not is_valid:
                st.sidebar.warning(f"Missing standard columns: {', '.join(missing)}")
                with st.sidebar.expander("🛠️ Column Mapping Tool (Google Forms / Custom CSV)", expanded=True):
                    st.caption("Map your CSV columns to the standardized schema:")
                    column_map: Dict[str, str] = {}
                    for req_col in REQUIRED_COLUMNS:
                        default_idx = 0
                        opts = ["-- Select Column --"] + list(uploaded_df.columns)
                        # Check if a close match exists
                        for idx, c in enumerate(uploaded_df.columns, start=1):
                            if req_col in c.lower() or c.lower() in req_col:
                                default_idx = idx
                                break
                        choice = st.selectbox(f"Map to '{req_col}':", opts, index=default_idx, key=f"map_{req_col}")
                        if choice != "-- Select Column --":
                            column_map[choice] = req_col

                    if st.button("Apply Mapping", use_container_width=True):
                        mapped_df = map_columns(uploaded_df, column_map)
                        m_valid, m_missing = validate_columns(mapped_df)
                        if m_valid:
                            st.session_state.mapped_uploaded_df = mapped_df
                            st.rerun()
                        else:
                            st.error(f"Still missing required columns: {', '.join(m_missing)}")

                if "mapped_uploaded_df" in st.session_state:
                    raw_df = st.session_state.mapped_uploaded_df
                else:
                    st.warning("Please map required columns to proceed with analysis.")
            else:
                raw_df = norm_df

        except Exception as e:
            st.sidebar.error(f"Error parsing CSV file: {str(e)}")
    else:
        st.info("👈 Please upload a CSV file from the sidebar to begin analysis, or switch to Sample Dataset.")

# If no data is available yet, stop
if raw_df is None or raw_df.empty:
    st.stop()

# -------------------------------------------------------------
# DATA CLEANING PIPELINE
# -------------------------------------------------------------
cleaned_df, cleaning_report = clean_poll_data(raw_df)

# -------------------------------------------------------------
# MAIN HEADER
# -------------------------------------------------------------
st.markdown('<div class="app-header">', unsafe_allow_html=True)
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("📊 Poll Results Visualizer")
    st.caption("Interactive Exploratory Data Analysis & Statistical Aggregation for Poll Responses")
with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(source_badge_html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filter Responses")

# Question Filter
all_questions = sorted(list(cleaned_df["poll_question"].dropna().unique()))
question_options = ["All Questions"] + all_questions
selected_question_option = st.sidebar.selectbox("Poll Question:", question_options, index=1 if all_questions else 0)

# Region Filter
available_regions = sorted(list(cleaned_df["region"].dropna().unique()))
select_all_regions = st.sidebar.checkbox("Select All Regions", value=True)
if select_all_regions:
    selected_regions = available_regions
else:
    selected_regions = st.sidebar.multiselect("Regions:", available_regions, default=available_regions[:2])

# Age Group Filter
available_ages = sorted(list(cleaned_df["age_group"].dropna().unique()))
select_all_ages = st.sidebar.checkbox("Select All Age Groups", value=True)
if select_all_ages:
    selected_ages = available_ages
else:
    selected_ages = st.sidebar.multiselect("Age Groups:", available_ages, default=available_ages[:2])

# Date Range Filter (if valid dates exist)
date_series = cleaned_df["parsed_submitted_at"].dropna() if "parsed_submitted_at" in cleaned_df.columns else pd.Series([], dtype="datetime64[ns]")
date_filter_active = False
start_date_val = None
end_date_val = None

if not date_series.empty:
    min_dt = date_series.min().date()
    max_dt = date_series.max().date()
    if min_dt < max_dt:
        selected_date_range = st.sidebar.date_input(
            "Submission Date Range:",
            value=(min_dt, max_dt),
            min_value=min_dt,
            max_value=max_dt,
        )
        if isinstance(selected_date_range, (list, tuple)) and len(selected_date_range) == 2:
            start_date_val, end_date_val = selected_date_range
            date_filter_active = True

# Filter the DataFrame
filtered_df = cleaned_df.copy()

if selected_question_option != "All Questions":
    filtered_df = filtered_df[filtered_df["poll_question"] == selected_question_option]

if selected_regions:
    filtered_df = filtered_df[filtered_df["region"].isin(selected_regions)]
else:
    filtered_df = filtered_df.iloc[0:0]

if selected_ages:
    filtered_df = filtered_df[filtered_df["age_group"].isin(selected_ages)]
else:
    filtered_df = filtered_df.iloc[0:0]

if date_filter_active and start_date_val and end_date_val and "parsed_submitted_at" in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df["parsed_submitted_at"].dt.date >= start_date_val)
        & (filtered_df["parsed_submitted_at"].dt.date <= end_date_val)
    ]

# -------------------------------------------------------------
# KPI METRICS SECTION
# -------------------------------------------------------------
kpis = get_kpis(filtered_df)

kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5, kpi_c6 = st.columns(6)
with kpi_c1:
    st.metric("Total Responses", f"{kpis['total_responses']:,}")
with kpi_c2:
    st.metric("Unique Respondents", f"{kpis['unique_respondents']:,}")
with kpi_c3:
    st.metric("Questions Active", kpis["num_questions"])
with kpi_c4:
    st.metric("Distinct Answers", kpis["num_answers"])
with kpi_c5:
    st.metric("Active Regions", kpis["num_regions"])
with kpi_c6:
    st.metric("Age Cohorts", kpis["num_age_groups"])

# Data Cleaning & Health Audit Expander
with st.expander("🛡️ Data Cleaning & Pipeline Audit Report", expanded=False):
    c_a, c_b, c_c, c_d = st.columns(4)
    c_a.write(f"**Input Rows:** {cleaning_report['input_rows']}")
    c_b.write(f"**Retained Rows:** {cleaning_report['retained_rows']}")
    c_c.write(f"**Exact Duplicates Dropped:** {cleaning_report['exact_duplicates_removed']}")
    c_d.write(f"**Respondent Overwrites Dropped:** {cleaning_report['duplicate_responses_removed']}")

    if cleaning_report["cleaning_log"]:
        st.markdown("**Cleaning Decision Log:**")
        for log_entry in cleaning_report["cleaning_log"]:
            st.markdown(f"- `{log_entry}`")
    else:
        st.caption("No records required modification or removal. Input dataset was clean.")

# Check for empty filter results
if filtered_df.empty:
    st.warning("⚠️ No responses match your current filter selection. Please broaden your filters in the sidebar.")
    st.stop()

# -------------------------------------------------------------
# DASHBOARD TABS
# -------------------------------------------------------------
tab_dist, tab_segments, tab_timeline, tab_insights, tab_data, tab_export = st.tabs([
    "📊 Response Distribution",
    "👥 Demographic Segments",
    "📈 Timeline Trends",
    "💡 Automated Insights",
    "📋 Response Table",
    "💾 Export & Reports",
])

# -------------------------------------------------------------
# TAB 1: RESPONSE DISTRIBUTION
# -------------------------------------------------------------
with tab_dist:
    active_q = None if selected_question_option == "All Questions" else selected_question_option
    breakdown_df = calculate_question_breakdown(filtered_df, active_q)

    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.subheader("Answer Frequency & Percentage Distribution")
        chart_type = st.radio("Display Mode:", ["Response Counts", "Percentage (%)"], horizontal=True)

        y_metric = "count" if chart_type == "Response Counts" else "percentage"
        y_title = "Response Count" if chart_type == "Response Counts" else "Percentage (%)"

        fig_bar = px.bar(
            breakdown_df,
            x="answer",
            y=y_metric,
            text=y_metric,
            color="answer",
            title=f"Response Breakdown for: {selected_question_option}",
            labels={"answer": "Answer Option", y_metric: y_title},
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        fig_bar.update_traces(
            texttemplate="%{text}" if chart_type == "Response Counts" else "%{text:.1f}%",
            textposition="outside",
        )
        fig_bar.update_layout(
            xaxis_tickangle=-25,
            showlegend=False,
            height=420,
            margin=dict(l=20, r=20, t=50, b=50),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.subheader("Answer Share")
        fig_pie = px.pie(
            breakdown_df,
            names="answer",
            values="count",
            hole=0.45,
            title="Distribution Share",
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        fig_pie.update_traces(textinfo="percent+label", hoverinfo="label+value+percent")
        fig_pie.update_layout(showlegend=False, height=420, margin=dict(l=10, r=10, t=50, b=30))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Detailed Table
    st.markdown("##### Frequency Table")
    st.dataframe(
        breakdown_df.rename(
            columns={"answer": "Answer Option", "count": "Response Count", "percentage": "Share (%)"}
        ),
        use_container_width=True,
        hide_index=True,
    )

# -------------------------------------------------------------
# TAB 2: DEMOGRAPHIC SEGMENTS
# -------------------------------------------------------------
with tab_segments:
    st.subheader("Demographic & Segment Cross-Tabulation")

    # If "All Questions" is selected, choose a specific question for meaningful segment comparison
    segment_q = selected_question_option
    if segment_q == "All Questions":
        segment_q = st.selectbox(
            "Select Question for Segment Analysis:",
            all_questions,
            key="segment_q_select",
        )

    segment_dim = st.radio(
        "Segment Dimension:",
        ["Region", "Age Group"],
        horizontal=True,
    )
    seg_col = "region" if segment_dim == "Region" else "age_group"

    seg_df = calculate_segment_breakdown(filtered_df, segment_q, seg_col)

    if not seg_df.empty:
        col_seg_chart, col_seg_table = st.columns([3, 2])

        with col_seg_chart:
            seg_metric = st.radio("Bar Values:", ["Within-Segment Percentage (%)", "Raw Count"], horizontal=True)
            y_seg = "percentage" if "Percentage" in seg_metric else "count"
            y_label = f"Share within {segment_dim} (%)" if "Percentage" in seg_metric else "Response Count"

            fig_seg = px.bar(
                seg_df,
                x=seg_col,
                y=y_seg,
                color="answer",
                barmode="group",
                title=f"Responses by {segment_dim} ({segment_q})",
                labels={seg_col: segment_dim, y_seg: y_label, "answer": "Answer Option"},
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_seg.update_layout(height=430, margin=dict(l=20, r=20, t=50, b=40))
            st.plotly_chart(fig_seg, use_container_width=True)

        with col_seg_table:
            st.markdown(f"##### {segment_dim} Comparison Breakdown")
            display_seg = seg_df[[seg_col, "answer", "count", "segment_total", "percentage"]].rename(
                columns={
                    seg_col: segment_dim,
                    "answer": "Answer",
                    "count": "Responses",
                    "segment_total": "Total in Segment",
                    "percentage": "Share (%)",
                }
            )
            st.dataframe(display_seg, use_container_width=True, hide_index=True)
    else:
        st.info("No data available for this segment breakdown under current filters.")

# -------------------------------------------------------------
# TAB 3: TIMELINE TRENDS
# -------------------------------------------------------------
with tab_timeline:
    st.subheader("Submission Volume Over Time")
    active_q_tl = None if selected_question_option == "All Questions" else selected_question_option

    time_freq = st.radio("Aggregation Interval:", ["Daily ('D')", "Weekly ('W')"], horizontal=True)
    freq_code = "D" if "Daily" in time_freq else "W"

    timeline_df = calculate_submission_timeline(filtered_df, active_q_tl, freq=freq_code)

    if not timeline_df.empty and len(timeline_df) > 1:
        fig_time = px.area(
            timeline_df,
            x="date",
            y="submission_count",
            title=f"Submission Trend ({'Daily' if freq_code == 'D' else 'Weekly'})",
            labels={"date": "Submission Date", "submission_count": "Responses Logged"},
            color_discrete_sequence=["#0284c7"],
        )
        fig_time.update_traces(mode="lines+markers", marker=dict(size=6))
        fig_time.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=40))
        st.plotly_chart(fig_time, use_container_width=True)

        # Quick statistics
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("Peak Single-Day Responses", int(timeline_df["submission_count"].max()))
        tc2.metric("Average Responses / Interval", f"{timeline_df['submission_count'].mean():.1f}")
        tc3.metric("Total Intervals Observed", len(timeline_df))
    else:
        st.info("Insufficient timestamp data or single-interval responses available for time series visualization.")

# -------------------------------------------------------------
# TAB 4: AUTOMATED INSIGHTS
# -------------------------------------------------------------
with tab_insights:
    st.subheader("💡 Evidence-Based Automated Insights")

    insights_q = None if selected_question_option == "All Questions" else selected_question_option
    insights = generate_automated_insights(filtered_df, selected_question=insights_q)

    # Primary Finding Box
    st.markdown(
        f"""
        <div class="insight-box">
            <h4 style="margin: 0 0 8px 0; color: #065f46;">🎯 Primary Analytical Finding</h4>
            <p style="margin: 0; font-size: 1.05rem; color: #047857;">{insights['primary_finding']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ins1, col_ins2 = st.columns(2)

    with col_ins1:
        if insights.get("demographic_highlight"):
            st.markdown(
                f"""
                <div style="background: #f8fafc; border: 1px solid #cbd5e1; padding: 14px 18px; border-radius: 8px;">
                    <h5 style="margin:0 0 6px 0; color: #334155;">🌍 Regional Divergence</h5>
                    <p style="margin:0; color: #475569;">{insights['demographic_highlight']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_ins2:
        if insights.get("secondary_finding"):
            st.markdown(
                f"""
                <div style="background: #f8fafc; border: 1px solid #cbd5e1; padding: 14px 18px; border-radius: 8px;">
                    <h5 style="margin:0 0 6px 0; color: #334155;">👥 Demographic Volume</h5>
                    <p style="margin:0; color: #475569;">{insights['secondary_finding']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Data Quality Notes / Small Sample Warnings
    if insights["data_quality_notes"]:
        for note in insights["data_quality_notes"]:
            st.markdown(
                f"""
                <div class="caution-box">
                    <strong>⚠️ Statistical Caution:</strong> {note}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Methodological Limitation Statement
    st.markdown(
        f"""
        <div class="limitation-box">
            <strong>📋 Data Integrity & Limitation Notice:</strong><br>
            {insights['limitation_statement']}
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------------------
# TAB 5: RAW RESPONSE TABLE
# -------------------------------------------------------------
with tab_data:
    st.subheader("Filtered Response Records")
    st.caption(f"Displaying {len(filtered_df):,} cleaned and filtered records.")

    display_cols = ["response_id", "submitted_at", "poll_question", "answer", "region", "age_group"]
    existing_disp = [c for c in display_cols if c in filtered_df.columns]
    st.dataframe(filtered_df[existing_disp], use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# TAB 6: EXPORT & REPORTS
# -------------------------------------------------------------
with tab_export:
    st.subheader("💾 Export Data & Download Reports")
    st.caption("Generate downloadable analytical summaries and cleaned datasets.")

    summary_export_df = generate_summary_table(filtered_df)

    col_exp1, col_exp2, col_exp3 = st.columns(3)

    # Download Filtered CSV
    with col_exp1:
        st.markdown("##### Filtered Records")
        st.caption("Download the current filtered dataset as a CSV file.")
        filtered_csv = filtered_df[existing_disp].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered CSV",
            data=filtered_csv,
            file_name="filtered_poll_responses.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Download Analytical Summary CSV
    with col_exp2:
        st.markdown("##### Analytical Summary")
        st.caption("Download aggregated counts and percentages across all questions.")
        summary_csv = summary_export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📊 Download Summary CSV",
            data=summary_csv,
            file_name="poll_analytical_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Download Markdown Report
    with col_exp3:
        st.markdown("##### Analytical Report")
        st.caption("Download a formatted Markdown summary report.")
        markdown_text = format_markdown_report(
            kpis=kpis,
            insights=insights,
            summary_df=summary_export_df,
            source_name=data_source_label,
        )
        st.download_button(
            label="📑 Download Report (Markdown)",
            data=markdown_text.encode("utf-8"),
            file_name="poll_results_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("##### Report Preview")
    with st.expander("👁️ View Markdown Report Content", expanded=False):
        st.markdown(markdown_text)
