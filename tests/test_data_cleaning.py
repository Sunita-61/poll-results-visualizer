"""Unit tests for the data cleaning module.

Tests cover:
- Column normalization
- Missing required columns detection
- Column mapping
- Exact duplicate handling
- Repeated response_id handling per question
- Critical vs demographic missing value handling
- Safe datetime parsing with invalid dates
- Whitespace trimming
- Empty dataset handling
- Immutability of original DataFrame
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data_cleaning import (
    REQUIRED_COLUMNS,
    clean_poll_data,
    map_columns,
    normalize_column_name,
    normalize_column_names,
    validate_columns,
)


def test_normalize_column_name() -> None:
    """Test normalization of individual column names."""
    assert normalize_column_name("  Response ID  ") == "response_id"
    assert normalize_column_name("Poll-Question") == "poll_question"
    assert normalize_column_name("Age Group (Years)") == "age_group_years"
    assert normalize_column_name("Submitted At") == "submitted_at"


def test_normalize_column_names_dataframe() -> None:
    """Test normalization across DataFrame headers."""
    df = pd.DataFrame(columns=[" Response ID ", "Poll Question", "Answer", "Region "])
    normalized = normalize_column_names(df)
    assert list(normalized.columns) == ["response_id", "poll_question", "answer", "region"]
    # Ensure original df unchanged
    assert list(df.columns) == [" Response ID ", "Poll Question", "Answer", "Region "]


def test_validate_columns_valid() -> None:
    """Test validation when all required columns are present."""
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    is_valid, missing = validate_columns(df)
    assert is_valid is True
    assert missing == []


def test_validate_columns_missing() -> None:
    """Test validation when required columns are absent."""
    df = pd.DataFrame(columns=["response_id", "answer", "region"])
    is_valid, missing = validate_columns(df)
    assert is_valid is False
    assert "poll_question" in missing
    assert "submitted_at" in missing
    assert "age_group" in missing


def test_map_columns() -> None:
    """Test mapping non-standard column names to standard schema."""
    df = pd.DataFrame({
        "Timestamp": ["2026-03-01 10:00:00"],
        "User ID": ["USR_01"],
        "Question": ["Favorite Language?"],
        "Choice": ["Python"],
        "Country": ["Europe"],
        "Age": ["25-34"],
    })
    mapping = {
        "Timestamp": "submitted_at",
        "User ID": "response_id",
        "Question": "poll_question",
        "Choice": "answer",
        "Country": "region",
        "Age": "age_group",
    }
    mapped_df = map_columns(df, mapping)
    is_valid, missing = validate_columns(mapped_df)
    assert is_valid is True
    assert missing == []
    assert mapped_df.iloc[0]["answer"] == "Python"


def test_clean_poll_data_exact_duplicates() -> None:
    """Test removal of exact duplicate records."""
    data = [
        {"response_id": "R1", "submitted_at": "2026-01-01", "poll_question": "Q1", "answer": "A", "region": "NA", "age_group": "18-24"},
        {"response_id": "R1", "submitted_at": "2026-01-01", "poll_question": "Q1", "answer": "A", "region": "NA", "age_group": "18-24"},
        {"response_id": "R2", "submitted_at": "2026-01-01", "poll_question": "Q1", "answer": "B", "region": "EU", "age_group": "25-34"},
    ]
    df = pd.DataFrame(data)
    cleaned, report = clean_poll_data(df)

    assert report["input_rows"] == 3
    assert report["exact_duplicates_removed"] == 1
    assert report["retained_rows"] == 2
    assert len(cleaned) == 2


def test_clean_poll_data_question_duplicates() -> None:
    """Test dropping multiple votes from the same respondent for the same question."""
    data = [
        {"response_id": "R1", "submitted_at": "2026-01-01 10:00:00", "poll_question": "Q1", "answer": "Option A", "region": "NA", "age_group": "18-24"},
        {"response_id": "R1", "submitted_at": "2026-01-01 10:05:00", "poll_question": "Q1", "answer": "Option B", "region": "NA", "age_group": "18-24"},
        # R1 answering a DIFFERENT question (Q2) should be retained
        {"response_id": "R1", "submitted_at": "2026-01-01 10:00:00", "poll_question": "Q2", "answer": "Option X", "region": "NA", "age_group": "18-24"},
    ]
    df = pd.DataFrame(data)
    cleaned, report = clean_poll_data(df)

    assert report["duplicate_responses_removed"] == 1
    assert len(cleaned) == 2
    # Check that first answer was kept
    q1_row = cleaned[cleaned["poll_question"] == "Q1"].iloc[0]
    assert q1_row["answer"] == "Option A"


def test_clean_poll_data_missing_fields_and_whitespace() -> None:
    """Test whitespace trimming, dropping missing questions/answers, and imputing demographics."""
    data = [
        # Normal row with whitespace
        {"response_id": "R1 ", "submitted_at": "2026-01-01", "poll_question": " Q1 ", "answer": " Python ", "region": " Asia ", "age_group": " 18-24 "},
        # Missing answer (critical field - should be dropped)
        {"response_id": "R2", "submitted_at": "2026-01-01", "poll_question": "Q1", "answer": None, "region": "Europe", "age_group": "25-34"},
        # Missing question (critical field - should be dropped)
        {"response_id": "R3", "submitted_at": "2026-01-01", "poll_question": "", "answer": "Go", "region": "NA", "age_group": "35-44"},
        # Missing region (demographic - should be imputed to 'Unknown')
        {"response_id": "R4", "submitted_at": "2026-01-01", "poll_question": "Q1", "answer": "Rust", "region": None, "age_group": "25-34"},
    ]
    df = pd.DataFrame(data)
    cleaned, report = clean_poll_data(df)

    assert report["input_rows"] == 4
    assert report["missing_critical_fields_removed"] == 2
    assert report["imputed_demographics_count"] >= 1
    assert len(cleaned) == 2

    # Check trimmed values
    first = cleaned[cleaned["response_id"] == "R1"].iloc[0]
    assert first["poll_question"] == "Q1"
    assert first["answer"] == "Python"
    assert first["region"] == "Asia"

    # Check imputed value
    r4_row = cleaned[cleaned["response_id"] == "R4"].iloc[0]
    assert r4_row["region"] == "Unknown"


def test_clean_poll_data_invalid_dates() -> None:
    """Test safe parsing of invalid dates without crashing."""
    data = [
        {"response_id": "R1", "submitted_at": "2026-02-15 14:30:00", "poll_question": "Q1", "answer": "A", "region": "NA", "age_group": "18-24"},
        {"response_id": "R2", "submitted_at": "not-a-valid-date", "poll_question": "Q1", "answer": "B", "region": "EU", "age_group": "25-34"},
    ]
    df = pd.DataFrame(data)
    cleaned, report = clean_poll_data(df)

    assert report["invalid_dates_count"] == 1
    assert len(cleaned) == 2
    assert pd.notna(cleaned.iloc[0]["parsed_submitted_at"])
    assert pd.isna(cleaned.iloc[1]["parsed_submitted_at"])


def test_clean_poll_data_empty() -> None:
    """Test that cleaning an empty DataFrame handles gracefully."""
    df = pd.DataFrame()
    cleaned, report = clean_poll_data(df)
    assert cleaned.empty
    assert report["input_rows"] == 0
    assert report["retained_rows"] == 0
