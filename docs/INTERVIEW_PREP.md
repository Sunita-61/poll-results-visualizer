# Interview Preparation Guide — Poll Results Visualizer

This guide equips you to confidently discuss the **Poll Results Visualizer** project during college placement interviews, technical screenings, and data science internship evaluations.

---

## 1. Quick Pitches

### The 30-Second Elevator Pitch
> *"I built the **Poll Results Visualizer**, an end-to-end data analytics application that transforms messy survey and poll responses into clean, interactive intelligence. It accepts custom CSVs, Google Forms exports, or synthetic datasets, applies an audited cleaning and deduplication pipeline, performs demographic and time-series aggregations using Pandas, and presents interactive Plotly visualizations and automated insights through a modern Streamlit web dashboard. The entire pipeline is fully decoupled and tested with a 100% passing pytest suite."*

---

### The 2-Minute Technical Walkthrough
> *"When designing this project, my primary goal was to demonstrate production-grade data science practices rather than just building a simple visual dashboard.*
>
> *First, in the **Data Ingestion & Cleaning Layer**, I implemented a modular module (`data_cleaning.py`) that enforces a canonical schema: `response_id`, `submitted_at`, `poll_question`, `answer`, `region`, and `age_group`. It handles messy real-world survey quirks: it trims whitespace, validates headers with an interactive Google Forms mapper, safely parses timestamps using `pd.to_datetime(..., errors='coerce')`, and removes exact duplicate rows. Crucially, its deduplication logic differentiates between a single respondent answering multiple questions—which is valid survey behavior—versus someone voting multiple times on the same question, where only the initial vote is preserved. Every decision is tracked in a transparent audit report.*
>
> *Second, in the **Analytics Layer** (`analytics.py`), the logic is strictly separated from the presentation UI. It computes essential KPIs, answer distributions, cross-tabulated demographic breakdowns across regions and age groups, and time-series submission volumes. Percentages are dynamically calculated within specific question and segment denominators, preventing statistical distortion.*
>
> *Third, the application features an **Automated Insight Engine** that dynamically computes top choices, margins of victory, and regional divergences, while actively warning users if segment sample sizes are too small to draw sound conclusions.*
>
> *Finally, the dashboard is built with **Streamlit** and **Plotly**, featuring full filter reactivity and instant exports for filtered data, analytical summaries, and executive Markdown reports. The codebase follows PEP 8 standards, is fully typed, and is validated by 19 unit tests running under Pytest."*

---

## 2. Technical Decisions & Justifications

| Technology | Why It Was Chosen | Alternatives Considered & Why Rejected |
|---|---|---|
| **Python 3** | Standard language for data analysis; rich ecosystem of data manipulation tools. | R (smaller web dashboard ecosystem), JavaScript/Node (steeper barrier for data analytics). |
| **Pandas** | High-performance vectorized DataFrame operations, grouping, and aggregations. | Plain Python dictionaries (too slow and verbose for aggregations), Polars (overkill for survey datasets < 1M rows). |
| **Streamlit** | Fast, pythonic web application framework with reactive state management and minimal boilerplate. | Flask/Django + React (requires heavy frontend/backend separation without adding analytical value for this scope). |
| **Plotly** | Client-side interactive graphics with zoom, hover tooltips, and responsive layout. | Matplotlib/Seaborn (static images without interactivity), D3.js (complex web development overhead). |
| **Pytest** | Industry-standard test runner with clean fixtures, assertion introspection, and fast execution. | Unittest (more boilerplate), manual testing (error-prone and non-repeatable). |

---

## 3. Deep-Dive Concepts

### Data Cleaning Approach
1. **Immutability:** The raw input DataFrame is copied before processing so that original user data remains unaltered.
2. **Multi-Question Deduplication Rule:**
   - A single respondent (`response_id`) often answers multiple poll questions.
   - Deduplicating strictly on `response_id` would erase answers to questions 2, 3, etc.
   - Therefore, deduplication is executed on the composite key `(response_id, poll_question)`.
3. **Missing Critical vs Demographic Values:**
   - Missing `poll_question` or `answer` makes a row unusable; these rows are dropped.
   - Missing `region` or `age_group` is imputed with `"Unknown"` so the participant's vote is not discarded.
4. **Safe Timestamp Parsing:** `errors='coerce'` converts unparseable dates to `NaT` (Not-a-Time), which is logged and filtered from timeline charts without crashing the application.

---

### Mathematical Formulations

#### Question-Level Share
$$\text{Percentage} = \left( \frac{\text{Count of Answer}_i}{\sum_{j} \text{Count of Answer}_j} \right) \times 100$$
- Evaluated over all valid responses to that specific question.
- Verified in tests to sum to $100.0\% \pm 0.1\%$.

#### Within-Segment Demographic Share
$$\text{Within-Segment Percentage} = \left( \frac{\text{Count of Answer}_i \text{ in Segment}_s}{\text{Total Responses in Segment}_s \text{ for that Question}} \right) \times 100$$
- Prevents regional or age-group population imbalances from skewing segment preferences.

---

## 4. Key Engineering Challenges & Solutions

### Challenge 1: String Dtype Compatibility in Modern Pandas (Pandas 3.0+)
- **Problem:** In newer versions of Pandas, string columns default to PyArrow-backed string types rather than traditional NumPy `object` dtype. Checking `df[col].dtype == 'object'` failed to detect string columns, preventing whitespace trimming.
- **Solution:** Upgraded the type check to use `pd.api.types.is_string_dtype(col) or col.dtype == 'object'`, ensuring backwards and forwards compatibility across all Pandas releases.

### Challenge 2: Non-Standard CSV Headers (Google Forms Exports)
- **Problem:** Google Forms and external survey platforms export headers like *"What is your age?"* or *"Timestamp"* rather than standardized database field names.
- **Solution:** Built an interactive column-mapping component in the Streamlit sidebar allowing users to map arbitrary survey headers directly into the canonical schema before running the pipeline.

### Challenge 3: Small-Sample Distortion
- **Problem:** When multiple filters (e.g., specific age + specific region + specific question) are applied, sample size can shrink to very small counts (e.g., $N=4$), where percentages (like 75%) misrepresent certainty.
- **Solution:** Implemented automated statistical caution alerts whenever sample size drops below 25, explicitly cautioning users against over-interpreting high-variance percentages.

---

## 5. 15 Likely Interview Questions & Model Answers

### Q1: Why did you separate data processing logic from the Streamlit UI?
**Answer:** Putting analytical logic inside the UI script binds business logic to the presentation layer. By decoupling `data_cleaning.py` and `analytics.py`, the core data processing functions can be imported into automated test suites, CLI tools, or batch scripts without needing Streamlit to run.

### Q2: What is your strategy for handling missing values in survey data?
**Answer:** I distinguish between critical survey fields and contextual demographics. If an answer or question is missing, the response cannot be analyzed, so it is dropped. However, if a demographic field like region is missing, discarding the row would suppress the respondent's vote. I impute missing demographics with `"Unknown"` and record the count in the cleaning audit report.

### Q3: How do you prevent division-by-zero errors during percentage calculations?
**Answer:** In `src/analytics.py`, every percentage calculation verifies that the denominator (total responses or segment total) is greater than zero. If the count is zero or the dataset is empty, it assigns a default percentage of `0.0%` rather than attempting division.

### Q4: How does your deduplication handle a participant answering four different poll questions?
**Answer:** If we deduplicated solely on `response_id`, only the first question would survive and the other three would be deleted. Instead, I deduplicate on the composite key `['response_id', 'poll_question']`. This allows one respondent to have one vote per distinct question, while eliminating duplicate submissions for the same question.

### Q5: What is the difference between response count and unique respondents?
**Answer:** In a multi-question survey, one participant (unique respondent) may generate multiple response records (one per question answered). If 200 participants each answer 4 questions, there are 200 unique respondents and 800 total responses. The dashboard displays both metrics clearly to prevent ambiguity.

### Q6: Why did you use Plotly instead of Matplotlib or Seaborn?
**Answer:** Matplotlib and Seaborn generate static raster or vector images. For web dashboards, users expect interactivity—hovering to see exact numbers, toggling legend categories on and off, and zooming into time-series intervals. Plotly provides responsive, client-side interactivity natively in Streamlit.

### Q7: How does your synthetic data generator ensure reproducible outputs?
**Answer:** It uses NumPy's `default_rng(seed)` with an explicitly passed integer seed. When the seed is constant, NumPy's pseudo-random number generator produces the exact same sequence of choices every time. I verified this with a dedicated unit test asserting that two runs with seed 42 generate identical DataFrames.

### Q8: What statistical tests could you add to verify if regional differences are significant?
**Answer:** A Chi-Square Test of Independence ($\chi^2$) would be ideal here. It compares observed response frequencies across regions against expected frequencies under the null hypothesis of independence. If the $p$-value is below 0.05, we could state with statistical confidence that geographic region significantly influences answer preference.

### Q9: How do you handle malformed or unexpected date formats?
**Answer:** I use `pd.to_datetime(df['submitted_at'], errors='coerce')`. The `errors='coerce'` parameter prevents Python from raising an unhandled exception on malformed strings like `"N/A"` or `"invalid_date"`, converting them to `NaT` (Not-a-Time). The count of unparseable dates is logged in the audit report, and timeline charts drop `NaT` entries while preserving the rest of the survey row.

### Q10: How did you structure your unit tests with Pytest?
**Answer:** I created two test suites: `test_data_cleaning.py` and `test_analytics.py`. Each test uses small, deterministic, manually calculated datasets where the expected count, percentage, or deduplicated row count is known in advance. I test normal operation, edge cases (empty DataFrames, zero responses), and mathematical constraints (percentages summing to 100%).

### Q11: What is the limitation statement displayed on your dashboard?
**Answer:** It reminds viewers that the findings reflect only the sample of respondents collected. Without randomized, stratified probability sampling, opt-in or simulated poll results cannot be generalized to broader populations. Including this disclaimer demonstrates methodological awareness and data ethics.

### Q12: How would you scale this application if the dataset grew to 10 million responses?
**Answer:** For 10 million rows, in-memory Pandas and single-node Streamlit would face memory and latency bottlenecks. I would:
1. Store raw data in a columnar database like DuckDB, ClickHouse, or PostgreSQL.
2. Push aggregations (group by, count) down to the database engine using SQL.
3. Transmit only the aggregated summary data to Streamlit.
4. Implement caching using `@st.cache_data` to avoid redundant queries.

### Q13: What does `validate_columns` do and why is it important?
**Answer:** It inspects the input DataFrame against the expected list of required columns (`REQUIRED_COLUMNS`). If any are missing, it returns a boolean flag and a list of missing column names. This enables graceful error handling and triggers the column-mapping interface rather than causing an unhandled `KeyError`.

### Q14: How does the dashboard maintain state when a user adjusts filters?
**Answer:** Streamlit reruns the script top-to-bottom upon widget interactions. Filters (question selectbox, region multiselect, date slider) operate sequentially on the cleaned DataFrame copy. We also use `st.session_state` to persist generated synthetic datasets and custom column mappings across reruns.

### Q15: If you had two more weeks to work on this, what would you prioritize?
**Answer:** I would implement:
1. Chi-Square hypothesis testing to flag statistically significant demographic variations.
2. PDF executive report generation using ReportLab or WeasyPrint.
3. Support for multi-select questions (checkboxes where respondents select multiple options).
4. Direct webhook integration with Google Sheets or Typeform for live real-time response polling.
