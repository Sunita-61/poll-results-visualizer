"""Data cleaning and preprocessing module for Poll Results Visualizer.

Provides deterministic cleaning, schema validation, whitespace trimming,
safe date parsing, duplicate management, and detailed cleaning audit reports.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


# Required schema columns
REQUIRED_COLUMNS = [
    "response_id",
    "submitted_at",
    "poll_question",
    "answer",
    "region",
    "age_group",
]


def normalize_column_name(col: str) -> str:
    """Normalize a single column name.

    Converts to lowercase, strips leading/trailing whitespace, and replaces
    spaces and hyphens with underscores.
    """
    clean = str(col).strip().lower()
    clean = re.sub(r"[\s\-]+", "_", clean)
    clean = re.sub(r"[^\w_]", "", clean)
    return clean


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Return a new DataFrame with normalized column names.

    Original DataFrame is not modified in place.
    """
    df_copy = df.copy()
    df_copy.columns = [normalize_column_name(c) for c in df_copy.columns]
    return df_copy


def validate_columns(
    df: pd.DataFrame,
    required_cols: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """Check if all required columns exist in the DataFrame.

    Args:
        df: Input DataFrame to check.
        required_cols: List of required column names (defaults to REQUIRED_COLUMNS).

    Returns:
        Tuple of (is_valid: bool, missing_columns: List[str]).
    """
    if required_cols is None:
        required_cols = REQUIRED_COLUMNS
    existing_cols = set(df.columns)
    missing = [col for col in required_cols if col not in existing_cols]
    return len(missing) == 0, missing


def map_columns(
    df: pd.DataFrame,
    column_mapping: Dict[str, str],
) -> pd.DataFrame:
    """Rename columns in a DataFrame using a mapping dictionary.

    Args:
        df: Original DataFrame.
        column_mapping: Dict mapping source column names to standardized schema names.

    Returns:
        A copy of the DataFrame with renamed columns.
    """
    df_copy = df.copy()
    return df_copy.rename(columns=column_mapping)


def clean_poll_data(
    df: pd.DataFrame,
    drop_exact_duplicates: bool = True,
    drop_question_duplicates: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean and standardize poll response data.

    Preserves the original DataFrame in memory. Generates an audit report
    explaining all cleaning decisions and record counts.

    Cleaning Rules:
    1. Trim leading and trailing whitespace from all string/text columns.
    2. Drop exact duplicate rows (all columns identical).
    3. Drop duplicate responses where the same respondent submitted multiple
       answers to the same question (keeps first occurrence). Note that the same
       respondent answering different questions is valid survey behavior and kept.
    4. Remove rows where critical fields ('poll_question' or 'answer') are missing/null/empty.
    5. Impute missing demographic fields ('region', 'age_group') with 'Unknown'
       to avoid discarding otherwise valid poll votes.
    6. Safely parse timestamps in 'submitted_at' using pd.to_datetime with errors='coerce'.

    Args:
        df: Input DataFrame conforming to the standardized schema.
        drop_exact_duplicates: If True, drops identical repeated rows.
        drop_question_duplicates: If True, retains only first answer per (response_id, poll_question).

    Returns:
        Tuple of (cleaned_df: pd.DataFrame, cleaning_report: Dict[str, Any]).
    """
    report: Dict[str, Any] = {
        "input_rows": len(df),
        "retained_rows": 0,
        "exact_duplicates_removed": 0,
        "duplicate_responses_removed": 0,
        "missing_critical_fields_removed": 0,
        "invalid_dates_count": 0,
        "imputed_demographics_count": 0,
        "cleaning_log": [],
    }

    if df.empty:
        report["cleaning_log"].append("Input dataset was empty. Returned empty DataFrame.")
        return df.copy(), report

    # Work on a fresh copy
    cleaned = df.copy()

    # Step 1: Trim whitespace across all string/object columns
    for col in cleaned.columns:
        if pd.api.types.is_string_dtype(cleaned[col]) or cleaned[col].dtype == "object":
            cleaned[col] = cleaned[col].astype(str).str.strip()
            # Replace literal 'nan', 'None', or empty string representations with actual NaN
            cleaned[col] = cleaned[col].replace(["nan", "None", "<NA>", ""], pd.NA)

    # Step 2: Remove exact duplicate rows
    if drop_exact_duplicates:
        initial_count = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        exact_dups = initial_count - len(cleaned)
        report["exact_duplicates_removed"] = exact_dups
        if exact_dups > 0:
            report["cleaning_log"].append(
                f"Removed {exact_dups} exact duplicate rows matching across all fields."
            )

    # Step 3: Handle duplicate answers from same respondent for same question
    if drop_question_duplicates and "response_id" in cleaned.columns and "poll_question" in cleaned.columns:
        initial_count = len(cleaned)
        # Drop duplicates on (response_id, poll_question) keeping first valid submission
        cleaned = cleaned.drop_duplicates(subset=["response_id", "poll_question"], keep="first")
        q_dups = initial_count - len(cleaned)
        report["duplicate_responses_removed"] = q_dups
        if q_dups > 0:
            report["cleaning_log"].append(
                f"Removed {q_dups} duplicate response rows from respondents who submitted multiple answers for the same question."
            )

    # Step 4: Drop rows missing critical fields: 'poll_question' or 'answer'
    initial_count = len(cleaned)
    critical_cols = [c for c in ["poll_question", "answer"] if c in cleaned.columns]
    if critical_cols:
        cleaned = cleaned.dropna(subset=critical_cols)
        # Also drop rows where they might be empty strings
        for c in critical_cols:
            cleaned = cleaned[cleaned[c].astype(str).str.strip() != ""]
        missing_crit = initial_count - len(cleaned)
        report["missing_critical_fields_removed"] = missing_crit
        if missing_crit > 0:
            report["cleaning_log"].append(
                f"Dropped {missing_crit} records missing required question or answer values."
            )

    # Step 5: Impute missing demographic fields with 'Unknown'
    imputed_count = 0
    for demo_col in ["region", "age_group"]:
        if demo_col in cleaned.columns:
            missing_mask = cleaned[demo_col].isna() | (cleaned[demo_col].astype(str).str.strip() == "")
            missing_n = int(missing_mask.sum())
            if missing_n > 0:
                cleaned.loc[missing_mask, demo_col] = "Unknown"
                imputed_count += missing_n
                report["cleaning_log"].append(
                    f"Imputed {missing_n} missing/blank '{demo_col}' values with 'Unknown'."
                )
    report["imputed_demographics_count"] = imputed_count

    # Step 6: Safe timestamp parsing
    if "submitted_at" in cleaned.columns:
        parsed_dates = pd.to_datetime(cleaned["submitted_at"], errors="coerce")
        invalid_mask = parsed_dates.isna() & cleaned["submitted_at"].notna()
        invalid_count = int(invalid_mask.sum())
        report["invalid_dates_count"] = invalid_count
        cleaned["parsed_submitted_at"] = parsed_dates
        if invalid_count > 0:
            report["cleaning_log"].append(
                f"Identified {invalid_count} unparseable timestamps (set to NaT for timeline analysis)."
            )

    report["retained_rows"] = len(cleaned)
    cleaned = cleaned.reset_index(drop=True)
    return cleaned, report
