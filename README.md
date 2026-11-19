# 💼 LinkedIn Salary Predictor & AI-Powered Negotiation Advisor

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?logo=streamlit)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.5-orange?logo=scikit-learn)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-green)
![Plotly](https://img.shields.io/badge/Plotly-5.22-blue?logo=plotly)

> **Know Your Worth. Negotiate Smarter.**
> A production-grade Streamlit application that predicts your expected salary using Machine Learning and generates AI-powered, data-driven salary negotiation strategies — all based on 33,000+ real LinkedIn job postings.

---

## ✨ Features

- 📊 **Salary Dashboard** — KPIs, salary distributions, trends over time
- 💰 **Deep Salary Analysis** — Box plots, percentile tables, outlier analysis, interactive salary filters
- 🛠️ **Skills & Salary Impact** — Demand charts, salary-boosting skills, bubble charts, word clouds
- 🏭 **Industry Insights** — Salary ranges, remote rates, experience-level heatmaps
- 📍 **Location Analysis** — Salary by US state, remote trends, state × experience heatmaps
- 🏢 **Company Analysis** — Top hirers, company size distributions, salary by company
- 🔮 **ML Salary Predictor** — Random Forest / Gradient Boosting / Ridge pipeline with gauge chart, similar jobs, and feature importance
- 🤝 **AI Negotiation Advisor** — 5 personalised talking points, skill gap analysis, and a ready-to-send negotiation script

---

## 📂 Dataset — 11 CSV Files

| File | Description |
|------|-------------|
| `postings.csv` | 33K+ job postings with salary, location, experience, work type |
| `jobs/salaries.csv` | Detailed salary ranges per job |
| `jobs/job_skills.csv` | Skills required per job |
| `jobs/job_industries.csv` | Industry tags per job |
| `jobs/benefits.csv` | Benefits per job |
| `companies/companies.csv` | Company metadata (size, location, URL) |
| `companies/employee_counts.csv` | Employee and follower counts |
| `companies/company_industries.csv` | Industry per company |
| `companies/company_specialities.csv` | Specialities per company |
| `mappings/industries.csv` | industry_id → industry_name |
| `mappings/skills.csv` | skill_abr → skill_name |

---

## 🛠️ Tech Stack

| Component | Library |
|-----------|---------|
| Web framework | Streamlit 1.35 |
| Data manipulation | Pandas 2.2, NumPy 1.26 |
| Machine Learning | Scikit-learn 1.5, XGBoost 2.0 |
| Charts | Plotly 5.22, Matplotlib 3.9 |
| Word Cloud | wordcloud 1.9 |
| Model persistence | Joblib 1.4 |
| Styling | Custom CSS (LinkedIn palette) |

---

## 📁 Project Structure

```
linkedin_salary_predictor/
│
├── app.py                              ← Homepage & entry point
├── pages/
│   ├── 01_Salary_Dashboard.py
│   ├── 02_Salary_Analysis.py
│   ├── 03_Skills_vs_Salary.py
│   ├── 04_Industry_Insights.py
│   ├── 05_Location_Analysis.py
│   ├── 06_Company_Analysis.py
│   ├── 07_Salary_Predictor.py          ← ⭐ ML prediction
│   └── 08_Negotiation_Advisor.py       ← ⭐ AI negotiation
│
├── utils/
│   ├── data_loader.py                  ← @st.cache_data loaders
│   ├── preprocessing.py                ← Cleaning & feature engineering
│   ├── visualizations.py              ← Plotly chart factories
│   └── helpers.py                      ← Formatting & UI utilities
│
├── models/
│   ├── train_model.py                  ← One-time training script
│   ├── salary_model.pkl                ← Best model (after training)
│   └── encoders.pkl                    ← Label encoders & feature names
│
├── assets/
│   └── style.css                       ← LinkedIn-inspired CSS
│
├── data/                               ← Extracted CSVs (gitignored)
│   ├── postings.csv
│   ├── jobs/
│   ├── companies/
│   └── mappings/
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Setup Instructions

```bash
# 1. Clone or create the project folder
mkdir linkedin_salary_predictor && cd linkedin_salary_predictor

# 2. Extract dataset into data/ folder
unzip /path/to/archive.zip -d data/

# 3. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Train the ML model (one time only — takes 2–5 minutes)
python models/train_model.py

# 6. Launch the app
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 🤖 ML Model Details

**Target variable:** `normalized_salary` (USD annual, pre-normalised in dataset)

**Features:**

| Feature | Encoding |
|---------|----------|
| Experience Level | Ordinal (0–5) |
| Work Type | Label Encoded |
| Remote Allowed | Binary (0/1) |
| State | Label Encoded |
| Company Size | Ordinal (0–7) |
| Industry | Label Encoded |
| Pay Period | Ordinal (0–4) |
| Skill Count | Count (from job_skills join) |
| Benefit Count | Count (from benefits join) |
| Log Views | log1p transform |
| Log Applies | log1p transform |

**Models trained:**

| Model | Notes |
|-------|-------|
| Random Forest (200 trees) | Best overall performance |
| Gradient Boosting (200 trees) | Strong on non-linear patterns |
| Ridge Regression | Baseline linear model |

**Auto-selects best R² model** → saves to `models/salary_model.pkl`

---

## 📸 Screenshots

*(Add screenshots here after running the app)*

---

## 📄 License

MIT License — free for personal and educational use.

---

*Built with ❤️ using Streamlit, Scikit-learn, and real LinkedIn job data.*
