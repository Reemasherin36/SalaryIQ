"""
utils/india_loader.py
Loads and combines all 3 Naukri CSV files into one clean DataFrame.
Estimates salaries in LPA based on experience + location since
Package data is mostly "Not disclosed".
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import re

# ── Indian Salary Estimation (based on real market data 2024) ─────────────────
# Source: Naukri.com, AmbitionBox, LinkedIn India salary reports

CITY_TIER = {
    "bangalore": 1.25, "bengaluru": 1.25, "mumbai": 1.20, "hyderabad": 1.20,
    "delhi": 1.15, "gurgaon": 1.15, "gurugram": 1.15, "pune": 1.12,
    "noida": 1.10, "chennai": 1.10, "kolkata": 1.05, "ahmedabad": 1.00,
    "jaipur": 0.95, "kochi": 0.95, "coimbatore": 0.90, "indore": 0.90,
}

# Base LPA by experience midpoint (Data Science / Analytics domain)
def estimate_lpa(min_exp: float, max_exp: float, city: str,
                 skill_count: int) -> float:
    """Estimate salary in LPA using Indian DS market data.

    Args:
        min_exp: Minimum years of experience required.
        max_exp: Maximum years of experience required.
        city: Primary city name (lowercase).
        skill_count: Number of skills listed.

    Returns:
        Estimated annual salary in Lakhs Per Annum.
    """
    mid_exp = (min_exp + max_exp) / 2

    # Base salary curve (LPA) for Data Science / Analytics in India
    if mid_exp <= 1:
        base = np.random.uniform(3.5, 6.0)
    elif mid_exp <= 2:
        base = np.random.uniform(5.0, 9.0)
    elif mid_exp <= 4:
        base = np.random.uniform(8.0, 15.0)
    elif mid_exp <= 6:
        base = np.random.uniform(13.0, 22.0)
    elif mid_exp <= 8:
        base = np.random.uniform(18.0, 32.0)
    elif mid_exp <= 12:
        base = np.random.uniform(28.0, 50.0)
    elif mid_exp <= 16:
        base = np.random.uniform(45.0, 80.0)
    else:
        base = np.random.uniform(70.0, 130.0)

    # City multiplier
    city_mult = 1.0
    for key, mult in CITY_TIER.items():
        if key in city.lower():
            city_mult = mult
            break

    # Skills bonus (more skills = slight premium)
    skill_bonus = min(skill_count * 0.02, 0.20)

    return round(base * city_mult * (1 + skill_bonus), 1)


def parse_experience(exp_str: str):
    """Extract min and max years from strings like '4-6 Yrs' or '2 Yrs'.

    Args:
        exp_str: Raw experience string.

    Returns:
        Tuple of (min_exp, max_exp) as floats.
    """
    if not isinstance(exp_str, str):
        return 2.0, 5.0
    nums = re.findall(r"\d+\.?\d*", exp_str)
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    elif len(nums) == 1:
        v = float(nums[0])
        return v, v + 2
    return 2.0, 5.0


def exp_to_level(min_exp: float) -> str:
    """Map minimum experience years to experience level label.

    Args:
        min_exp: Minimum years of experience.

    Returns:
        Experience level string matching the app's standard labels.
    """
    if min_exp == 0:
        return "Internship"
    elif min_exp <= 2:
        return "Entry level"
    elif min_exp <= 5:
        return "Associate"
    elif min_exp <= 10:
        return "Mid-Senior level"
    elif min_exp <= 15:
        return "Director"
    else:
        return "Executive"


@st.cache_data(show_spinner=False)
def load_india_data() -> pd.DataFrame:
    """Load, combine, and clean all 3 Naukri CSV files.

    Normalises column names, estimates salaries, and maps fields
    to match the app's standard LinkedIn dataset structure.

    Returns:
        Combined and cleaned DataFrame ready for all app pages.
    """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base, "data")

    # ── Load all 3 Naukri files ──────────────────────────────────────────────
    file_configs = [
        {
            "file": "NaukriData_data analytics.csv",
            "col_map": {
                "Job_Titles": "title",
                "Company_Names": "company_name",
                "Experience_Required": "experience_raw",
                "Package_Details": "package_raw",
                "Locations": "location",
                "Skills": "skills_desc",
                "Post_Url": "job_url",
                "Post_Time": "post_time",
            },
        },
        {
            "file": "NaukriData_Data Science.csv",
            "col_map": {
                "Job_Titles": "title",
                "Company_Names": "company_name",
                "Experience_Required": "experience_raw",
                "Package_Details": "package_raw",
                "Locations": "location",
                "Skills": "skills_desc",
                "Post_Url": "job_url",
                "Post_Time": "post_time",
            },
        },
        {
            "file": "Naukri_Data_Scientist_and_Data_Analytics_Jobs_Data.csv",
            "col_map": {
                "Job Titles": "title",
                "Company Names": "company_name",
                "Experience Required": "experience_raw",
                "Package": "package_raw",
                "Locations": "location",
                "Skills": "skills_desc",
            },
        },
    ]

    dfs = []
    for cfg in file_configs:
        path = os.path.join(data_dir, cfg["file"])
        try:
            df = pd.read_csv(path, encoding="utf-8",
                             on_bad_lines="skip", low_memory=False)
            df = df.rename(columns=cfg["col_map"])
            dfs.append(df)
        except FileNotFoundError:
            continue
        except Exception as e:
            continue

    if not dfs:
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)

    # ── Drop duplicates ──────────────────────────────────────────────────────
    combined = combined.drop_duplicates(
        subset=["title", "company_name", "experience_raw"], keep="first"
    ).reset_index(drop=True)

    # ── Generate job IDs ─────────────────────────────────────────────────────
    combined["job_id"] = [f"IN_{i}" for i in range(len(combined))]

    # ── Parse experience ─────────────────────────────────────────────────────
    exp_parsed = combined["experience_raw"].apply(parse_experience)
    combined["min_exp"] = exp_parsed.apply(lambda x: x[0])
    combined["max_exp"] = exp_parsed.apply(lambda x: x[1])
    combined["formatted_experience_level"] = combined["min_exp"].apply(exp_to_level)

    # ── Extract primary city ──────────────────────────────────────────────────
    combined["location"] = (
        combined["location"].astype(str)
        .str.split("/").str[0]
        .str.split(",").str[0]
        .str.strip()
    )
    combined["state"] = combined["location"]

    # ── Estimate salary in LPA ────────────────────────────────────────────────
    np.random.seed(42)
    combined["skill_count"] = (
        combined["skills_desc"].astype(str)
        .apply(lambda x: len([s for s in x.split() if len(s) > 2]))
        .clip(1, 20)
    )
    combined["normalized_salary"] = combined.apply(
        lambda row: estimate_lpa(
            row["min_exp"], row["max_exp"],
            str(row["location"]).lower(),
            int(row["skill_count"])
        ), axis=1
    )
    combined["min_salary"] = (combined["normalized_salary"] * 0.85).round(1)
    combined["max_salary"] = (combined["normalized_salary"] * 1.20).round(1)

    # ── Standard fields ───────────────────────────────────────────────────────
    combined["formatted_work_type"] = "Full-time"
    combined["remote_allowed"] = 0
    combined["currency"] = "INR"
    combined["pay_period"] = "YEARLY"
    combined["views"] = 0
    combined["applies"] = 0
    combined["compensation_type"] = "BASE_SALARY"

    # ── Clean skills ──────────────────────────────────────────────────────────
    combined["skills_desc"] = combined["skills_desc"].astype(str)

    # ── Industry from job title ───────────────────────────────────────────────
    def infer_industry(title: str) -> str:
        t = str(title).lower()
        if any(k in t for k in ["data science", "ml", "machine learning", "ai"]):
            return "Artificial Intelligence & Machine Learning"
        if any(k in t for k in ["analyst", "analytics", "bi ", "business intel"]):
            return "Data Analytics & Business Intelligence"
        if any(k in t for k in ["engineer", "software", "developer"]):
            return "Software Engineering"
        if any(k in t for k in ["manager", "lead", "head", "director"]):
            return "Management & Leadership"
        if any(k in t for k in ["research", "scientist"]):
            return "Research & Development"
        return "Information Technology"

    combined["industry_name"] = combined["title"].apply(infer_industry)

    keep_cols = [
        "job_id", "title", "company_name", "location", "state",
        "normalized_salary", "min_salary", "max_salary",
        "formatted_experience_level", "formatted_work_type",
        "remote_allowed", "skills_desc", "skill_count",
        "industry_name", "currency", "pay_period",
        "views", "applies", "compensation_type",
        "min_exp", "max_exp",
    ]
    if "job_url" in combined.columns:
        keep_cols.append("job_url")

    return combined[[c for c in keep_cols if c in combined.columns]].copy()


@st.cache_data(show_spinner=False)
def get_india_skills(n: int = 50) -> list:
    """Extract top N skills from the Naukri dataset.

    Args:
        n: Number of top skills to return.

    Returns:
        List of skill name strings.
    """
    df = load_india_data()
    if df.empty or "skills_desc" not in df.columns:
        return []
    all_skills = (
        df["skills_desc"].astype(str)
        .apply(lambda x: [s.strip().title() for s in
                          re.split(r"[,|;\n]|(?<=[a-z])(?=[A-Z])", x)
                          if len(s.strip()) > 2])
        .explode()
        .dropna()
    )
    return all_skills.value_counts().head(n).index.tolist()


@st.cache_data(show_spinner=False)
def get_india_titles(n: int = 50) -> list:
    """Return top N job titles from the Indian dataset.

    Args:
        n: Number of titles to return.

    Returns:
        List of job title strings.
    """
    df = load_india_data()
    if df.empty or "title" not in df.columns:
        return []
    return df["title"].value_counts().head(n).index.tolist()


@st.cache_data(show_spinner=False)
def get_india_cities(n: int = 30) -> list:
    """Return top N Indian cities from the dataset.

    Args:
        n: Number of cities to return.

    Returns:
        List of city name strings.
    """
    df = load_india_data()
    if df.empty or "location" not in df.columns:
        return []
    return df["location"].value_counts().head(n).index.tolist()
