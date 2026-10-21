"""Analytics and statistical aggregation module for Poll Results Visualizer.

Provides KPIs, response distributions, segment breakdowns, percentage calculations,
timeline aggregations, and automated evidence-based insights.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def get_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate high-level summary KPIs for the active dataset.

    Returns:
        Dictionary containing counts of total responses, unique respondents,
        questions, answers, regions, age groups, and date range.
    """
    if df.empty:
        return {
            "total_responses": 0,
            "unique_respondents": 0,
            "num_questions": 0,
            "num_answers": 0,
            "num_regions": 0,
            "num_age_groups": 0,
            "date_min": None,
            "date_max": None,
        }

    date_series = None
    if "parsed_submitted_at" in df.columns:
        date_series = df["parsed_submitted_at"].dropna()
    elif "submitted_at" in df.columns:
        date_series = pd.to_datetime(df["submitted_at"], errors="coerce").dropna()

    date_min = date_series.min().strftime("%Y-%m-%d") if date_series is not None and not date_series.empty else None
    date_max = date_series.max().strftime("%Y-%m-%d") if date_series is not None and not date_series.empty else None

    return {
        "total_responses": int(len(df)),
        "unique_respondents": int(df["response_id"].nunique()) if "response_id" in df.columns else int(len(df)),
        "num_questions": int(df["poll_question"].nunique()) if "poll_question" in df.columns else 0,
        "num_answers": int(df["answer"].nunique()) if "answer" in df.columns else 0,
        "num_regions": int(df["region"].nunique()) if "region" in df.columns else 0,
        "num_age_groups": int(df["age_group"].nunique()) if "age_group" in df.columns else 0,
        "date_min": date_min,
        "date_max": date_max,
    }


def calculate_question_breakdown(
    df: pd.DataFrame,
    question: Optional[str] = None,
) -> pd.DataFrame:
    """Calculate response counts and percentages for answers to a specific question.

    Formula:
        Percentage = (count for an answer / total valid responses for that question) * 100

    Args:
        df: Cleaned responses DataFrame.
        question: Specific question string to filter on. If None, uses all rows.

    Returns:
        DataFrame with columns ['answer', 'count', 'percentage'] sorted descending by count.
    """
    if df.empty:
        return pd.DataFrame(columns=["answer", "count", "percentage"])

    sub_df = df.copy()
    if question is not None and "poll_question" in sub_df.columns:
        sub_df = sub_df[sub_df["poll_question"] == question]

    if sub_df.empty or "answer" not in sub_df.columns:
        return pd.DataFrame(columns=["answer", "count", "percentage"])

    counts = sub_df["answer"].value_counts().reset_index()
    counts.columns = ["answer", "count"]

    total = counts["count"].sum()
    if total > 0:
        counts["percentage"] = (counts["count"] / total * 100).round(2)
    else:
        counts["percentage"] = 0.0

    return counts


def calculate_segment_breakdown(
    df: pd.DataFrame,
    question: str,
    segment_col: str,
) -> pd.DataFrame:
    """Calculate cross-tabulated response counts and within-segment percentages.

    Formula:
        Within-Segment Percentage = (count of answer in segment / total responses in segment) * 100

    Args:
        df: Responses DataFrame.
        question: Specific question to analyze.
        segment_col: Demographic column to group by ('region' or 'age_group').

    Returns:
        DataFrame with columns: [segment_col, 'answer', 'count', 'segment_total', 'percentage']
    """
    cols = [segment_col, "answer", "count", "segment_total", "percentage"]
    if df.empty or segment_col not in df.columns or "answer" not in df.columns:
        return pd.DataFrame(columns=cols)

    sub_df = df[df["poll_question"] == question] if "poll_question" in df.columns else df
    if sub_df.empty:
        return pd.DataFrame(columns=cols)

    grouped = (
        sub_df.groupby([segment_col, "answer"], observed=False)
        .size()
        .reset_index(name="count")
    )

    # Compute segment totals
    totals = (
        sub_df.groupby(segment_col, observed=False)
        .size()
        .reset_index(name="segment_total")
    )

    merged = pd.merge(grouped, totals, on=segment_col, how="left")
    merged["percentage"] = np.where(
        merged["segment_total"] > 0,
        (merged["count"] / merged["segment_total"] * 100).round(2),
        0.0,
    )

    return merged.sort_values(by=[segment_col, "count"], ascending=[True, False]).reset_index(drop=True)


def calculate_submission_timeline(
    df: pd.DataFrame,
    question: Optional[str] = None,
    freq: str = "D",
) -> pd.DataFrame:
    """Aggregate submission volume over time.

    Args:
        df: Cleaned responses DataFrame.
        question: Optional question filter.
        freq: Resampling frequency ('D' for daily, 'W' for weekly).

    Returns:
        DataFrame with columns ['date', 'submission_count'].
    """
    cols = ["date", "submission_count"]
    if df.empty:
        return pd.DataFrame(columns=cols)

    sub_df = df.copy()
    if question is not None and "poll_question" in sub_df.columns:
        sub_df = sub_df[sub_df["poll_question"] == question]

    date_col = "parsed_submitted_at" if "parsed_submitted_at" in sub_df.columns else "submitted_at"
    if date_col not in sub_df.columns:
        return pd.DataFrame(columns=cols)

    dates = pd.to_datetime(sub_df[date_col], errors="coerce").dropna()
    if dates.empty:
        return pd.DataFrame(columns=cols)

    # Group by date period
    grouped = dates.dt.floor(freq).value_counts().sort_index().reset_index()
    grouped.columns = ["date", "submission_count"]
    grouped["date"] = grouped["date"].dt.strftime("%Y-%m-%d")
    return grouped


def generate_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a comprehensive analytical summary across all questions and answers.

    Returns:
        DataFrame with question-level totals, counts, and percentages.
    """
    cols = ["poll_question", "answer", "response_count", "question_total", "percentage"]
    if df.empty or "poll_question" not in df.columns or "answer" not in df.columns:
        return pd.DataFrame(columns=cols)

    grouped = (
        df.groupby(["poll_question", "answer"], observed=False)
        .size()
        .reset_index(name="response_count")
    )

    q_totals = (
        df.groupby("poll_question", observed=False)
        .size()
        .reset_index(name="question_total")
    )

    summary = pd.merge(grouped, q_totals, on="poll_question", how="left")
    summary["percentage"] = (summary["response_count"] / summary["question_total"] * 100).round(2)
    return summary.sort_values(
        by=["poll_question", "response_count"], ascending=[True, False]
    ).reset_index(drop=True)


def generate_automated_insights(
    df: pd.DataFrame,
    selected_question: Optional[str] = None,
    min_sample_warning: int = 25,
) -> Dict[str, Any]:
    """Derive automated, evidence-based analytical insights from the active dataset.

    Generates findings on the top-ranking answer, margin of preference,
    demographic divergences, data quality warnings, and methodological limitations.

    Args:
        df: Filtered/cleaned DataFrame.
        selected_question: Focus question or None for overall dataset insights.
        min_sample_warning: Threshold below which a small-sample caveat is triggered.

    Returns:
        Dictionary containing structured insights and limitation statements.
    """
    insights: Dict[str, Any] = {
        "question": selected_question or "All Questions Combined",
        "sample_size": len(df),
        "primary_finding": "",
        "secondary_finding": "",
        "demographic_highlight": "",
        "data_quality_notes": [],
        "limitation_statement": (
            "Methodological Limitation: All findings presented are derived exclusively "
            "from the collected or filtered sample. Because this dataset represents an "
            "opt-in or simulated poll without randomized stratified population sampling, "
            "percentages should not be interpreted as statistically generalizable to "
            "the broader global population."
        ),
    }

    if df.empty:
        insights["primary_finding"] = "No responses match the selected filters."
        insights["data_quality_notes"].append("Dataset is empty under current filter conditions.")
        return insights

    # Focus dataset
    sub_df = df[df["poll_question"] == selected_question] if selected_question else df
    sample_size = len(sub_df)
    insights["sample_size"] = sample_size

    if sample_size == 0:
        insights["primary_finding"] = f"No responses available for question '{selected_question}'."
        return insights

    # Check sample size adequacy
    if sample_size < min_sample_warning:
        insights["data_quality_notes"].append(
            f"Caution: Small sample size (N={sample_size} responses). "
            f"Segment comparisons and percentage estimates have high variance."
        )

    # 1. Top answer and runner-up
    breakdown = calculate_question_breakdown(sub_df)
    if not breakdown.empty:
        top_row = breakdown.iloc[0]
        top_answer = top_row["answer"]
        top_count = int(top_row["count"])
        top_pct = float(top_row["percentage"])

        if len(breakdown) > 1:
            second_row = breakdown.iloc[1]
            runner_up_answer = second_row["answer"]
            runner_up_pct = float(second_row["percentage"])
            margin = round(top_pct - runner_up_pct, 2)
            insights["primary_finding"] = (
                f"'{top_answer}' is the leading choice with {top_count} responses ({top_pct}% of total), "
                f"outpacing the runner-up ('{runner_up_answer}' at {runner_up_pct}%) by a {margin} percentage-point margin."
            )
        else:
            insights["primary_finding"] = (
                f"'{top_answer}' is the unanimous choice with {top_count} responses (100.0%)."
            )

    # 2. Demographic Divergence (Region)
    if "region" in sub_df.columns and selected_question:
        reg_breakdown = calculate_segment_breakdown(sub_df, selected_question, "region")
        if not reg_breakdown.empty:
            # Find the region where the top answer had its highest share
            top_ans = breakdown.iloc[0]["answer"] if not breakdown.empty else None
            if top_ans:
                top_ans_reg = reg_breakdown[reg_breakdown["answer"] == top_ans]
                if not top_ans_reg.empty:
                    peak_region_row = top_ans_reg.sort_values(by="percentage", ascending=False).iloc[0]
                    insights["demographic_highlight"] = (
                        f"Regional variation: Support for '{top_ans}' peaked in "
                        f"{peak_region_row['region']} at {peak_region_row['percentage']}% "
                        f"({peak_region_row['count']}/{peak_region_row['segment_total']} responses)."
                    )

    # 3. Age-group Divergence
    if "age_group" in sub_df.columns and selected_question:
        age_breakdown = calculate_segment_breakdown(sub_df, selected_question, "age_group")
        if not age_breakdown.empty:
            # Find which age group favored which answer
            peak_age = age_breakdown.sort_values(by="count", ascending=False).iloc[0]
            insights["secondary_finding"] = (
                f"Demographic volume: The largest cohort answering this question was "
                f"'{peak_age['age_group']}' ({peak_age['segment_total']} total segment responses)."
            )

    return insights
