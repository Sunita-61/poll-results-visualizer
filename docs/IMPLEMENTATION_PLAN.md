# Implementation Plan — Poll Results Visualizer

This document breaks down the end-to-end development methodology into eight structured phases. Each phase specifies **what was done**, **why it matters**, **expected outputs**, and **critical mistakes to avoid**.

---

## Phase 1: Environment Setup & Architecture Definition

### What to Do
- Define project scope, constraints, and architecture boundaries.
- Set up a clean Python virtual environment.
- Create directory structure (`data/`, `src/`, `tests/`, `docs/`, `screenshots/`).
- Configure `.gitignore`, `pytest.ini`, `conftest.py`, and `requirements.txt`.

### Why It Matters
Starting with modular packages and proper dependency pinning prevents path resolution issues, circular imports, and environment drift across development and deployment.

### Expected Output
- Verified Python environment running Pandas, Plotly, Streamlit, and Pytest.
- Clean folder hierarchy with all root configurations in place.

### Mistakes to Avoid
- Committing temporary directories (`.venv`, `__pycache__`, `.pytest_cache`).
- Storing hardcoded absolute file paths in source code instead of using `pathlib.Path`.
- Putting data cleaning and analytical code directly inside the Streamlit UI script.

---

## Phase 2: Data Schema Design & Input Engine

### What to Do
- Establish a canonical schema: `response_id`, `submitted_at`, `poll_question`, `answer`, `region`, `age_group`.
- Develop `src/synthetic_data.py` to generate reproducible synthetic responses with customizable sample size, questions, options, and fixed seeds.
- Create CLI script `generate_data.py` to produce a bundled sample dataset (`data/sample_poll_responses.csv`).
- Build support for three ingestion modes: Bundled Sample, Synthetic Generation, and CSV Upload.

### Why It Matters
Real-world data science projects must handle both known baseline datasets and unpredictable user-supplied files. Reproducible simulation enables rapid local testing and deterministic validation.

### Expected Output
- Bundled CSV containing 800 responses across 200 respondents.
- Parameterized generation function supporting noise injection (duplicates, whitespace, unparseable dates).

### Mistakes to Avoid
- Claiming synthetic survey data represents real human opinions without explicit disclosure.
- Hardcoding static response lists instead of making the generator configurable.
- Failing to seed random generators, causing non-deterministic test behavior.

---

## Phase 3: Data Cleaning & Preprocessing Pipeline

### What to Do
- Implement `src/data_cleaning.py`.
- Normalize column names (lowercase, whitespace removal, snake_case conversion).
- Implement column validation and an interactive column mapping fallback.
- Enforce deduplication rules:
  - Discard exact row duplicates.
  - Retain only the first submission when a respondent answers the same question multiple times.
  - Preserve valid multi-question survey responses from the same respondent.
- Filter out records missing critical fields (`poll_question`, `answer`).
- Impute missing demographic fields (`region`, `age_group`) with `"Unknown"`.
- Safely parse timestamps into datetime objects with `pd.to_datetime(..., errors='coerce')`.
- Produce a detailed data cleaning audit log.

### Why It Matters
Raw survey data is notorious for typos, duplicated submissions, missing responses, and inconsistent formatting. A robust cleaning layer ensures statistical validity and prevents runtime dashboard crashes.

### Expected Output
- A cleaned, normalized DataFrame and a comprehensive cleaning report dictionary.

### Mistakes to Avoid
- Silently dropping rows without logging or notifying the user.
- Modifying the original uploaded DataFrame in place (violating immutability).
- Deduplicating solely on `response_id`, which mistakenly erases legitimate answers to subsequent questions in multi-question polls.

---

## Phase 4: Exploratory Data Analysis (EDA)

### What to Do
- Build exploratory functions in `src/analytics.py`.
- Calculate aggregate KPIs: total responses, unique respondents, question count, distinct answers, demographic reach, and date span.
- Calculate frequency distributions and percentage representations.
- Build timeline resamplers to monitor submission velocity.

### Why It Matters
EDA establishes the foundational metrics and distributions required before drawing conclusions or building visual dashboards.

### Expected Output
- Tested aggregation functions that return clean, typed Pandas DataFrames and metric dictionaries.

### Mistakes to Avoid
- Confusing total response rows with unique survey participants.
- Generating metrics that fail to update when filters are applied.
- Crashing on empty datasets or single-category subsets.

---

## Phase 5: Statistical Aggregation & Demographic Analysis

### What to Do
- Implement cross-tabulation between questions, answers, and demographic segments (`region`, `age_group`).
- Formulate within-segment percentages:
  $$\text{Share} = \left(\frac{\text{Answer Count in Segment}}{\text{Total Responses in Segment for Question}}\right) \times 100$$
- Track sample size per segment to highlight low-sample variance.
- Generate an all-up summary table covering questions, answers, counts, and shares.

### Why It Matters
Demographic segmentation uncovers divergence in preference across regions or age brackets, transforming flat counts into actionable business or sociological intelligence.

### Expected Output
- Cross-tabulated DataFrames with segment totals and within-segment percentage shares.

### Mistakes to Avoid
- Dividing segment counts by total global sample size instead of within-segment totals.
- Making claims of statistical significance without formal hypothesis testing.
- Overlooking zero denominators when a segment has zero responses.

---

## Phase 6: Interactive Dashboard & UI Construction

### What to Do
- Build `app.py` using Streamlit and Plotly.
- Implement responsive layout with sidebar controls (data source selection, synthetic sliders, CSV upload, column mapper, multi-filters).
- Style dashboard using modern CSS (metric cards, status badges, insight callouts).
- Render interactive Plotly charts:
  - Frequency & percentage bar charts with hover tooltips.
  - Donut distribution share charts.
  - Segmented grouped bar charts.
  - Submission trend area charts.
- Implement data table viewers and filter reset options.

### Why It Matters
An intuitive, responsive interface allows non-technical stakeholders to explore complex survey findings effortlessly.

### Expected Output
- A web application accessible locally via `streamlit run app.py`.

### Mistakes to Avoid
- Cluttering the interface with redundant or overlapping charts.
- Using low-contrast or jarring color palettes.
- Hardcoding local file paths that break when the project is cloned by an interviewer.

---

## Phase 7: Automated Evidence-Based Insights & Export

### What to Do
- Implement `generate_automated_insights()` in `src/analytics.py`.
- Dynamically detect:
  - Top choice, count, percentage share, and lead margin over the runner-up.
  - Peak demographic and regional adoption cohorts.
  - Small sample size alerts (e.g., $N < 25$).
  - Mandatory methodological limitation notice.
- Provide direct download buttons for:
  - Filtered responses CSV.
  - Aggregated analytical summary CSV.
  - Formatted Markdown executive report.

### Why It Matters
Decision-makers need instant executive summaries alongside raw data. Automated reporting bridges the gap between charts and actionable insights.

### Expected Output
- Dynamic insight callout cards and working CSV/Markdown download buttons.

### Mistakes to Avoid
- Hardcoding static findings that fail to reflect filtered data.
- Omitting small-sample warnings, leading to over-interpretation of noisy data.
- Omitting clear disclaimer statements regarding survey generalizability.

---

## Phase 8: Testing, Documentation & Portfolio Publishing

### What to Do
- Write comprehensive unit tests in `tests/test_data_cleaning.py` and `tests/test_analytics.py`.
- Run test suite via `pytest -v` and achieve 100% pass rate.
- Create full project documentation:
  - `README.md`
  - `docs/PROJECT_ARCHITECTURE.md`
  - `docs/IMPLEMENTATION_PLAN.md`
  - `docs/INTERVIEW_PREP.md`
  - `docs/ROADMAP.md`
  - `screenshots/README.md`
- Provide exact Git commands for the user to initialize and publish to GitHub.

### Why It Matters
Interviewers and recruiters evaluate clean commit hygiene, automated test coverage, and documentation depth as indicators of engineering maturity.

### Expected Output
- Passing pytest suite.
- Portfolio-ready GitHub repository.

### Mistakes to Avoid
- Pushing to GitHub with broken tests or missing documentation.
- Committing secrets, API keys, or machine-specific virtual environment files.
- Claiming the repository is live before the user has run their git push commands.
