"""Synthetic data generation module for Poll Results Visualizer.

Generates reproducible poll survey responses adhering to the standardized schema:
- response_id
- submitted_at
- poll_question
- answer
- region
- age_group

Clearly labeled as synthetic data for educational and demonstration purposes.
"""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


# Default poll topics and realistic answer options
DEFAULT_POLL_CONFIG: Dict[str, Dict[str, List[str]]] = {
    "Which programming language do you prefer?": {
        "options": ["Python", "JavaScript", "TypeScript", "Go", "Java", "Rust"],
        "weights": [0.35, 0.25, 0.18, 0.08, 0.08, 0.06],
    },
    "Which learning method do you prefer?": {
        "options": [
            "Hands-on Projects",
            "Video Courses & Tutorials",
            "Reading Documentation & Books",
            "Interactive Coding Platforms",
            "Mentorship & Study Groups",
        ],
        "weights": [0.42, 0.28, 0.14, 0.10, 0.06],
    },
    "Which development platform do you use most?": {
        "options": [
            "VS Code",
            "JetBrains IDEs",
            "Neovim / Vim",
            "Cloud IDEs / GitHub Codespaces",
            "JupyterLab / Notebooks",
        ],
        "weights": [0.52, 0.22, 0.10, 0.08, 0.08],
    },
    "What is your primary career goal in tech?": {
        "options": [
            "Data Science & AI Engineer",
            "Full-Stack Web Developer",
            "Cloud & DevOps Engineer",
            "Cybersecurity Specialist",
            "Mobile App Developer",
        ],
        "weights": [0.32, 0.30, 0.18, 0.12, 0.08],
    },
}

REGIONS = ["North America", "Europe", "Asia-Pacific", "Latin America", "Middle East & Africa"]
REGION_WEIGHTS = [0.28, 0.26, 0.30, 0.09, 0.07]

AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55+"]
AGE_WEIGHTS = [0.38, 0.36, 0.15, 0.08, 0.03]


def generate_synthetic_poll_data(
    num_respondents: int = 200,
    random_seed: Optional[int] = 42,
    poll_config: Optional[Dict[str, Dict[str, List[str]]]] = None,
    start_date: str = "2026-01-15",
    end_date: str = "2026-03-31",
    add_noise: bool = False,
) -> pd.DataFrame:
    """Generate reproducible synthetic survey responses.

    Each respondent is assigned demographic characteristics (region, age_group)
    and provides responses to questions. Each row in the resulting DataFrame
    represents one question-response pair from a respondent.

    Args:
        num_respondents: Number of distinct survey participants.
        random_seed: Random seed for reproducibility.
        poll_config: Custom dictionary of questions, options, and probability weights.
        start_date: Start date for simulated submissions (YYYY-MM-DD).
        end_date: End date for simulated submissions (YYYY-MM-DD).
        add_noise: If True, injects realistic data imperfections (duplicates, whitespace,
                   malformed dates) to demonstrate data cleaning capabilities.

    Returns:
        pd.DataFrame containing standardized poll responses.
    """
    if num_respondents <= 0:
        return pd.DataFrame(
            columns=["response_id", "submitted_at", "poll_question", "answer", "region", "age_group"]
        )

    rng = np.random.default_rng(random_seed)
    config = poll_config or DEFAULT_POLL_CONFIG

    # Calculate date range span
    t_start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    t_end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    total_seconds = max(int((t_end - t_start).total_seconds()), 86400)

    records: List[Dict[str, str]] = []

    for i in range(1, num_respondents + 1):
        resp_id = f"RESP_{i:04d}"
        region = rng.choice(REGIONS, p=REGION_WEIGHTS)
        age_group = rng.choice(AGE_GROUPS, p=AGE_WEIGHTS)

        # Baseline submission time for this respondent
        random_offset = int(rng.uniform(0, total_seconds))
        submission_dt = t_start + datetime.timedelta(seconds=random_offset)
        submitted_at_str = submission_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Answer each question
        for question, q_info in config.items():
            options = q_info["options"]
            weights = q_info.get("weights")
            if weights is not None:
                # Normalize weights to sum exactly to 1.0 to avoid float precision issues
                w_arr = np.array(weights, dtype=float)
                w_norm = w_arr / w_arr.sum()
                selected_answer = rng.choice(options, p=w_norm)
            else:
                selected_answer = rng.choice(options)

            records.append({
                "response_id": resp_id,
                "submitted_at": submitted_at_str,
                "poll_question": str(question),
                "answer": str(selected_answer),
                "region": str(region),
                "age_group": str(age_group),
            })

    df = pd.DataFrame(records)

    # Optional realistic noise injection to showcase data cleaning in demos/tests
    if add_noise and len(df) > 20:
        # 1. Trailing or leading whitespace on some answers
        noisy_indices = rng.choice(len(df), size=min(15, len(df)), replace=False)
        for idx in noisy_indices[:5]:
            df.loc[idx, "answer"] = f"  {df.loc[idx, 'answer']}  "
        for idx in noisy_indices[5:10]:
            df.loc[idx, "region"] = f"{df.loc[idx, 'region']} "

        # 2. A few exact duplicate rows
        dup_rows = df.iloc[rng.choice(len(df), size=4, replace=False)].copy()
        df = pd.concat([df, dup_rows], ignore_index=True)

        # 3. A couple of malformed dates
        invalid_date_idx = rng.choice(len(df), size=2, replace=False)
        for idx in invalid_date_idx:
            df.loc[idx, "submitted_at"] = "invalid_timestamp_format"

    return df
