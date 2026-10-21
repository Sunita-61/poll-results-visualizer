# Project Roadmap — Poll Results Visualizer

This roadmap outlines planned enhancements and feature milestones for future iterations of the **Poll Results Visualizer**.

---

## 🚀 Version 1.1 — Statistical Rigor & Hypothesis Testing

- [ ] **Chi-Square ($\chi^2$) Test of Independence:**
  - Automatically evaluate whether differences in answers across demographic segments (regions or age groups) are statistically significant.
  - Display $p$-values and degrees of freedom alongside segment comparison charts.
  - Highlight findings where $p < 0.05$ with confidence annotations.
- [ ] **Margin of Error & Confidence Intervals:**
  - Calculate 95% Wilson score confidence intervals for all answer proportions.
  - Add optional error bars to frequency bar charts.

---

## 🗳️ Version 1.2 — Extended Question Types

- [ ] **Multi-Select Question Support (Checkbox Surveys):**
  - Parse delimiter-separated answers (e.g., `"Python; TypeScript; Go"`).
  - Calculate response rates based on total respondents rather than total choices selected.
- [ ] **Likert Scale & Rating Aggregations:**
  - Support 1–5 or 1–10 satisfaction scales.
  - Compute Net Promoter Score (NPS), weighted averages, and standard deviations.
- [ ] **Ranked-Choice Voting Analysis:**
  - Implement instant-runoff simulations to determine winners in preferential ballot surveys.

---

## 🔗 Version 1.3 — Live Ingestion & Cloud Connectors

- [ ] **Google Sheets Live Sync:**
  - Connect directly to Google Forms response sheets via Google Sheets Service Account credentials.
  - Provide a 1-click "Refresh from Google Sheets" button in the sidebar.
- [ ] **Webhook & REST API Ingestion:**
  - Create a FastAPI endpoint to stream incoming survey responses into SQLite/DuckDB in real time.

---

## 💬 Version 1.4 — Natural Language Processing for Free-Text Feedback

- [ ] **Open-Ended Text Analysis:**
  - Ingest free-text survey comments.
  - Perform automated sentiment classification (Positive / Neutral / Negative).
  - Extract top unigram/bigram keyword frequencies and render an interactive word cloud.

---

## 📑 Version 1.5 — Executive Export Enhancements

- [ ] **Automated PDF Report Generation:**
  - Convert summary findings, KPI cards, and chart screenshots into an executive-ready multi-page PDF report using WeasyPrint or ReportLab.
- [ ] **Interactive HTML Standalone Package:**
  - Export a self-contained HTML file bundling Plotly graphs for offline sharing.

---

## ⚙️ Version 1.6 — DevOps & CI/CD Automation

- [ ] **GitHub Actions Workflow:**
  - Run `pytest` and code linting (`ruff`, `flake8`) automatically on every push or pull request.
- [ ] **Docker Containerization:**
  - Provide a production-ready `Dockerfile` and `docker-compose.yml` for single-command container deployment.
