# Project Architecture — Poll Results Visualizer

This document details the multi-tiered software architecture, data flow pipeline, and design rationale behind the **Poll Results Visualizer** project.

---

## 1. High-Level Pipeline Architecture

The application implements a decoupled, uni-directional data pipeline ensuring separation of concerns between raw data ingestion, deterministic cleaning, statistical processing, interactive presentation, and reporting.

```
┌────────────────────────────────────────────────────────┐
│                      INPUT LAYER                       │
│  - Bundled Sample Dataset (data/sample_poll_responses) │
│  - Synthetic Generator (src/synthetic_data.py)         │
│  - User CSV Upload / Google Forms Export               │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                  PREPROCESSING LAYER                   │
│  - Schema Validation (REQUIRED_COLUMNS)                │
│  - Column Mapping Interface                            │
│  - Whitespace Normalization                            │
│  - Deduplication (Exact rows & same respondent votes)  │
│  - Safe Datetime Parsing & Missing Value Imputation    │
│  - Pipeline Audit Report Generation                    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                    ANALYTICS LAYER                     │
│  - High-level KPIs (Unique respondents, totals)        │
│  - Question-level Frequencies & Percentages            │
│  - Demographic Segment Cross-tabulation (Region/Age)   │
│  - Time-series Resampling & Aggregation                │
│  - Automated Evidence-based Insight Engine             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                  VISUALIZATION LAYER                   │
│  - Interactive Plotly Horizontal/Vertical Bar Charts   │
│  - Response Share Donut Charts                         │
│  - Grouped Segment Demographic Comparisons             │
│  - Time-series Submission Volume Area Charts           │
│  - Filter-reactive Dynamic KPI Cards                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                      │
│  - Filtered Sub-dataset Export (CSV)                   │
│  - Aggregated Analytical Summary Export (CSV)          │
│  - Executive Markdown Report Export (MD/TXT)           │
└────────────────────────────────────────────────────────┘
```

---

## 2. Layer Specifications

### 2.1 Input Layer
- **Input Modes:**
  1. *Bundled Sample Data*: Pre-generated, realistic survey response CSV with 800 responses across 200 participants.
  2. *Synthetic Simulation Generator*: Deterministic synthetic engine powered by NumPy's `default_rng` accepting customizable participant volumes, random seeds, and optional noise injection.
  3. *Custom CSV Ingestion*: Streamlit file uploader supporting standard CSVs, external exports, and Google Forms response sheets.
- **Standardized Schema:**
  - `response_id` (string): Unique identifier representing the individual respondent (e.g., `RESP_0042`).
  - `submitted_at` (timestamp / string): ISO timestamp of submission (e.g., `2026-03-15 14:22:00`).
  - `poll_question` (string): The poll question text.
  - `answer` (string): The response option chosen by the participant.
  - `region` (string): Geographic demographic classification.
  - `age_group` (string): Age bracket demographic classification.

---

### 2.2 Preprocessing & Data Cleaning Layer (`src/data_cleaning.py`)
- **Immutability Principle:** The raw uploaded DataFrame is never modified in place. All transformations yield a clean derivative.
- **Normalization:** Column headers are trimmed, downcased, and sanitized into snake_case identifiers.
- **Validation & Mapping:** Missing required columns trigger a fallback mapping interface allowing users to connect arbitrary survey headers to the canonical schema.
- **Deduplication Strategy:**
  - *Exact row duplicates* (matching across all fields) are discarded.
  - *Repeated votes by the same respondent on the same question* are discarded (preserving the first submission).
  - *Multiple questions answered by the same respondent* are preserved.
- **Missing Value Handling:**
  - Missing critical attributes (`poll_question`, `answer`) result in row exclusion.
  - Missing demographic fields (`region`, `age_group`) are imputed with `"Unknown"` to avoid throwing away valid poll votes.
- **Safe Date Parsing:** Dates are parsed using `errors='coerce'` to safeguard against malformed strings while recording audit statistics.
- **Audit Logging:** Emits a comprehensive dictionary containing initial counts, retained counts, dropped counts, and narrative explanations.

---

### 2.3 Analytics & Statistical Layer (`src/analytics.py`)
- **Decoupled Logic:** Zero UI code exists within the analytics module, ensuring 100% testability via `pytest`.
- **Mathematical Formulations:**
  $$\text{Answer Percentage} = \left( \frac{\text{Count of Answer}_i}{\sum \text{Valid Responses for Question}} \right) \times 100$$
  $$\text{Within-Segment Share} = \left( \frac{\text{Count of Answer}_i \text{ in Segment}_s}{\sum \text{Responses in Segment}_s \text{ for Question}} \right) \times 100$$
- **Safeguards:** Handles division-by-zero, empty subsets, missing categories, and single-respondent edge cases gracefully.
- **Automated Insight Generator:** Computes top choices, runner-up margin of victory, peak demographic adoption cohorts, sample size caveats, and methodological limitation notices.

---

### 2.4 Presentation & Visualization Layer (`app.py`)
- Built using **Streamlit** for state management and layout structure.
- Employs **Plotly Express** and **Plotly Graph Objects** for hardware-accelerated interactive visualizations with hover tooltips, responsive sizing, and color themes.
- Visual hierarchy features custom CSS for metric cards, status badges, insight banners, and structured tab navigation.

---

### 2.5 Output & Export Layer
- Direct in-memory buffer exports for:
  - Cleaned, filtered raw survey records (`filtered_poll_responses.csv`).
  - Grouped statistical summary tables (`poll_analytical_summary.csv`).
  - Markdown executive summaries for documentation and stakeholders (`poll_results_report.md`).
