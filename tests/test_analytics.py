"""Unit tests for the analytics and statistical aggregation module.

Tests cover:
- KPI metrics accuracy on populated and empty DataFrames
- Response count and percentage calculations
- Percentages summing to ~100%
- Demographic segment breakdowns and sample sizes
- Timeline aggregation
- Automated evidence-based insight generation
- Edge cases (empty data, missing categories, division by zero prevention)
- Synthetic data reproducibility with fixed random seed
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.analytics import (
    calculate_question_breakdown,
    calculate_segment_breakdown,
    calculate_submission_timeline,
    generate_automated_insights,
    generate_summary_table,
    get_kpis,
)
from src.synthetic_data import generate_synthetic_poll_data


@pytest.fixture
def sample_test_df() -> pd.DataFrame:
    """Fixture providing a deterministic, manually verifiable test dataset."""
    return pd.DataFrame([
        # Question 1: 6 responses (Python: 3, JS: 2, Go: 1)
        {"response_id": "R01", "submitted_at": "2026-03-01 10:00:00", "poll_question": "Preferred Language?", "answer": "Python", "region": "North America", "age_group": "18-24"},
        {"response_id": "R02", "submitted_at": "2026-03-01 11:00:00", "poll_question": "Preferred Language?", "answer": "Python", "region": "North America", "age_group": "25-34"},
        {"response_id": "R03", "submitted_at": "2026-03-02 09:00:00", "poll_question": "Preferred Language?", "answer": "Python", "region": "Europe", "age_group": "18-24"},
        {"response_id": "R04", "submitted_at": "2026-03-02 14:00:00", "poll_question": "Preferred Language?", "answer": "JavaScript", "region": "Europe", "age_group": "25-34"},
        {"response_id": "R05", "submitted_at": "2026-03-03 16:00:00", "poll_question": "Preferred Language?", "answer": "JavaScript", "region": "Asia-Pacific", "age_group": "18-24"},
        {"response_id": "R06", "submitted_at": "2026-03-03 17:00:00", "poll_question": "Preferred Language?", "answer": "Go", "region": "Asia-Pacific", "age_group": "35-44"},

        # Question 2: 4 responses (Remote: 3, In-office: 1)
        {"response_id": "R01", "submitted_at": "2026-03-01 10:00:00", "poll_question": "Work Preference?", "answer": "Remote", "region": "North America", "age_group": "18-24"},
        {"response_id": "R02", "submitted_at": "2026-03-01 11:00:00", "poll_question": "Work Preference?", "answer": "Remote", "region": "North America", "age_group": "25-34"},
        {"response_id": "R03", "submitted_at": "2026-03-02 09:00:00", "poll_question": "Work Preference?", "answer": "Remote", "region": "Europe", "age_group": "18-24"},
        {"response_id": "R04", "submitted_at": "2026-03-02 14:00:00", "poll_question": "Work Preference?", "answer": "In-office", "region": "Europe", "age_group": "25-34"},
    ])


def test_get_kpis_populated(sample_test_df: pd.DataFrame) -> None:
    """Test KPI calculations with a populated DataFrame."""
    kpis = get_kpis(sample_test_df)

    assert kpis["total_responses"] == 10
    assert kpis["unique_respondents"] == 6
    assert kpis["num_questions"] == 2
    assert kpis["num_answers"] == 5  # Python, JS, Go, Remote, In-office
    assert kpis["num_regions"] == 3  # North America, Europe, Asia-Pacific
    assert kpis["num_age_groups"] == 3  # 18-24, 25-34, 35-44
    assert kpis["date_min"] == "2026-03-01"
    assert kpis["date_max"] == "2026-03-03"


def test_get_kpis_empty() -> None:
    """Test KPI calculations with an empty DataFrame."""
    empty_df = pd.DataFrame()
    kpis = get_kpis(empty_df)

    assert kpis["total_responses"] == 0
    assert kpis["unique_respondents"] == 0
    assert kpis["num_questions"] == 0
    assert kpis["date_min"] is None


def test_calculate_question_breakdown(sample_test_df: pd.DataFrame) -> None:
    """Test answer frequency counts, percentages, and sorting."""
    breakdown = calculate_question_breakdown(sample_test_df, "Preferred Language?")

    assert len(breakdown) == 3
    # Top answer must be Python (count 3 of 6 = 50.0%)
    assert breakdown.iloc[0]["answer"] == "Python"
    assert breakdown.iloc[0]["count"] == 3
    assert breakdown.iloc[0]["percentage"] == pytest.approx(50.0, 0.01)

    # Second answer: JavaScript (count 2 of 6 = 33.33%)
    assert breakdown.iloc[1]["answer"] == "JavaScript"
    assert breakdown.iloc[1]["count"] == 2
    assert breakdown.iloc[1]["percentage"] == pytest.approx(33.33, 0.01)

    # Third answer: Go (count 1 of 6 = 16.67%)
    assert breakdown.iloc[2]["answer"] == "Go"
    assert breakdown.iloc[2]["count"] == 1
    assert breakdown.iloc[2]["percentage"] == pytest.approx(16.67, 0.01)

    # Percentages must sum to ~100%
    assert breakdown["percentage"].sum() == pytest.approx(100.0, 0.1)


def test_calculate_question_breakdown_empty() -> None:
    """Test question breakdown returns empty DataFrame when given empty input."""
    res = calculate_question_breakdown(pd.DataFrame(), "Non-existent Question")
    assert res.empty
    assert list(res.columns) == ["answer", "count", "percentage"]


def test_calculate_segment_breakdown(sample_test_df: pd.DataFrame) -> None:
    """Test demographic segment cross-tabulation and within-segment percentages."""
    reg_breakdown = calculate_segment_breakdown(
        sample_test_df, question="Preferred Language?", segment_col="region"
    )

    # In North America, total responses = 2, both chose Python -> 100%
    na_python = reg_breakdown[
        (reg_breakdown["region"] == "North America") & (reg_breakdown["answer"] == "Python")
    ].iloc[0]
    assert na_python["count"] == 2
    assert na_python["segment_total"] == 2
    assert na_python["percentage"] == pytest.approx(100.0, 0.01)

    # In Asia-Pacific, total responses = 2 (1 JS, 1 Go) -> 50% each
    ap_js = reg_breakdown[
        (reg_breakdown["region"] == "Asia-Pacific") & (reg_breakdown["answer"] == "JavaScript")
    ].iloc[0]
    assert ap_js["count"] == 1
    assert ap_js["segment_total"] == 2
    assert ap_js["percentage"] == pytest.approx(50.0, 0.01)


def test_calculate_submission_timeline(sample_test_df: pd.DataFrame) -> None:
    """Test timeline daily and weekly grouping."""
    timeline_d = calculate_submission_timeline(sample_test_df, question="Preferred Language?", freq="D")
    assert len(timeline_d) == 3
    # Day 1: 2 responses, Day 2: 2 responses, Day 3: 2 responses
    assert list(timeline_d["submission_count"]) == [2, 2, 2]

    # Test weekly grouping (Pandas 3.0 non-fixed frequency safe)
    timeline_w = calculate_submission_timeline(sample_test_df, question="Preferred Language?", freq="W")
    assert len(timeline_w) >= 1
    assert timeline_w["submission_count"].sum() == 6


def test_generate_summary_table(sample_test_df: pd.DataFrame) -> None:
    """Test comprehensive analytical summary across questions."""
    summary = generate_summary_table(sample_test_df)
    assert len(summary) == 5
    assert "question_total" in summary.columns
    assert "percentage" in summary.columns


def test_generate_automated_insights(sample_test_df: pd.DataFrame) -> None:
    """Test evidence-based insight generation and limitation statement."""
    insights = generate_automated_insights(sample_test_df, selected_question="Preferred Language?")

    assert "Python" in insights["primary_finding"]
    assert "50.0%" in insights["primary_finding"]
    assert len(insights["limitation_statement"]) > 20
    # Sample size is 6, which is < default warning threshold 25, so caution note must exist
    assert any("Small sample size" in note for note in insights["data_quality_notes"])


def test_synthetic_data_reproducibility() -> None:
    """Test that synthetic data generated with same seed produces identical results."""
    df1 = generate_synthetic_poll_data(num_respondents=50, random_seed=999)
    df2 = generate_synthetic_poll_data(num_respondents=50, random_seed=999)
    pd.testing.assert_frame_equal(df1, df2)

    # Different seed should yield different result
    df3 = generate_synthetic_poll_data(num_respondents=50, random_seed=123)
    assert not df1.equals(df3)
