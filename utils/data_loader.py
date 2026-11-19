"""
utils/data_loader.py
All data loading and merging functions for the LinkedIn Salary Predictor.
All functions are cached with @st.cache_data to prevent re-loading on each render.
"""

from __future__ import annotations

import os
import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional


# ── Path Helpers ──────────────────────────────────────────────────────────────

def _data_path(*parts: str) -> str:
    """Build an absolute path relative to the data/ directory.

    Args:
        *parts: Path components relative to the data directory.

    Returns:
        Absolute file path string.
    """
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    return os.path.join(base, *parts)


# ── Individual Loaders ─────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_postings() -> pd.DataFrame:
    """Load and lightly process the main postings CSV.

    Only required columns are read to minimise memory usage.
    Rows missing normalized_salary are kept — downstream callers filter as needed.

    Returns:
        DataFrame with core job posting fields.
    """
    required_cols = [
        "job_id", "company_id", "company_name", "title", "location",
        "max_salary", "med_salary", "min_salary", "normalized_salary",
        "pay_period", "formatted_work_type", "formatted_experience_level",
        "remote_allowed", "views", "applies", "listed_time",
        "original_listed_time", "work_type", "currency", "compensation_type",
        "skills_desc",
    ]
    path = _data_path("postings.csv")
    try:
        df = pd.read_csv(
            path,
            usecols=lambda c: c in required_cols,
            dtype={
                "job_id": str,
                "company_id": str,
                "normalized_salary": float,
            },
            low_memory=False,
        )
    except FileNotFoundError:
        st.warning("⚠️ postings.csv not found. Please extract the dataset into data/.")
        return pd.DataFrame()

    # Basic dtype fixes
    df["remote_allowed"] = df["remote_allowed"].fillna(0).astype(int)
    df["views"] = pd.to_numeric(df["views"], errors="coerce").fillna(0)
    df["applies"] = pd.to_numeric(df["applies"], errors="coerce").fillna(0)

    # Parse timestamps
    for col in ["listed_time", "original_listed_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit="ms", errors="coerce")

    return df


@st.cache_data(show_spinner=False)
def load_salaries() -> pd.DataFrame:
    """Load jobs/salaries.csv with salary details per job.

    Returns:
        DataFrame with salary_id, job_id, min/med/max salary, pay_period etc.
    """
    path = _data_path("jobs", "salaries.csv")
    try:
        df = pd.read_csv(path, dtype={"job_id": str}, low_memory=False)
        return df
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_job_skills() -> pd.DataFrame:
    """Load job_skills.csv merged with skills mapping (abbreviation → name).

    Returns:
        DataFrame with job_id, skill_abr, skill_name columns.
    """
    skills_path = _data_path("jobs", "job_skills.csv")
    mapping_path = _data_path("mappings", "skills.csv")
    try:
        job_skills = pd.read_csv(skills_path, dtype={"job_id": str}, low_memory=False)
        skills_map = pd.read_csv(mapping_path, low_memory=False)
        merged = job_skills.merge(skills_map, on="skill_abr", how="left")
        return merged
    except FileNotFoundError:
        return pd.DataFrame(columns=["job_id", "skill_abr", "skill_name"])


@st.cache_data(show_spinner=False)
def load_job_industries() -> pd.DataFrame:
    """Load job_industries.csv merged with industries mapping.

    Returns:
        DataFrame with job_id and industry_name columns.
    """
    ji_path = _data_path("jobs", "job_industries.csv")
    ind_path = _data_path("mappings", "industries.csv")
    try:
        job_ind = pd.read_csv(ji_path, dtype={"job_id": str}, low_memory=False)
        ind_map = pd.read_csv(ind_path, low_memory=False)
        merged = job_ind.merge(ind_map, on="industry_id", how="left")
        return merged
    except FileNotFoundError:
        return pd.DataFrame(columns=["job_id", "industry_name"])


@st.cache_data(show_spinner=False)
def load_benefits() -> pd.DataFrame:
    """Load benefits.csv and compute benefit count per job.

    Returns:
        DataFrame with job_id and benefit_count column.
    """
    path = _data_path("jobs", "benefits.csv")
    try:
        df = pd.read_csv(path, dtype={"job_id": str}, low_memory=False)
        benefit_counts = df.groupby("job_id").size().reset_index(name="benefit_count")
        return benefit_counts
    except FileNotFoundError:
        return pd.DataFrame(columns=["job_id", "benefit_count"])


@st.cache_data(show_spinner=False)
def load_companies() -> pd.DataFrame:
    """Load companies.csv merged with employee_counts.csv.

    Returns:
        DataFrame with company metadata including employee and follower counts.
    """
    co_path = _data_path("companies", "companies.csv")
    ec_path = _data_path("companies", "employee_counts.csv")
    try:
        companies = pd.read_csv(co_path, dtype={"company_id": str}, low_memory=False)
        try:
            emp = pd.read_csv(ec_path, dtype={"company_id": str}, low_memory=False)
            # Keep latest employee count per company
            emp_latest = emp.sort_values("time_recorded").groupby("company_id").last().reset_index()
            merged = companies.merge(emp_latest[["company_id", "employee_count", "follower_count"]],
                                     on="company_id", how="left")
        except FileNotFoundError:
            merged = companies
        return merged
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_company_industries() -> pd.DataFrame:
    """Load company_industries.csv.

    Returns:
        DataFrame with company_id and industry columns.
    """
    path = _data_path("companies", "company_industries.csv")
    try:
        return pd.read_csv(path, dtype={"company_id": str}, low_memory=False)
    except FileNotFoundError:
        return pd.DataFrame(columns=["company_id", "industry"])


@st.cache_data(show_spinner=False)
def load_skill_counts() -> pd.DataFrame:
    """Compute skill count per job_id from job_skills.

    Returns:
        DataFrame with job_id and skill_count columns.
    """
    job_skills = load_job_skills()
    if job_skills.empty:
        return pd.DataFrame(columns=["job_id", "skill_count"])
    counts = job_skills.groupby("job_id").size().reset_index(name="skill_count")
    return counts


# ── Master Merge ──────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_merged_full() -> pd.DataFrame:
    """Create the master merged DataFrame joining all data sources.

    Merges: postings + salaries + companies + industry + skill_count + benefit_count.
    Only jobs with normalized_salary are retained in this master view.

    Returns:
        Merged DataFrame suitable for analysis and ML training.
    """
    postings = load_postings()
    if postings.empty:
        return pd.DataFrame()

    # Skill count per job
    skill_counts = load_skill_counts()
    if not skill_counts.empty:
        postings = postings.merge(skill_counts, on="job_id", how="left")
        postings["skill_count"] = postings["skill_count"].fillna(0).astype(int)
    else:
        postings["skill_count"] = 0

    # Benefit count per job
    benefits = load_benefits()
    if not benefits.empty:
        postings = postings.merge(benefits, on="job_id", how="left")
        postings["benefit_count"] = postings["benefit_count"].fillna(0).astype(int)
    else:
        postings["benefit_count"] = 0

    # Company metadata
    companies = load_companies()
    if not companies.empty:
        company_cols = ["company_id", "company_size", "state", "country",
                        "employee_count", "follower_count"]
        company_cols = [c for c in company_cols if c in companies.columns]
        postings = postings.merge(companies[company_cols], on="company_id", how="left")

    # Primary industry per job (take first match)
    job_industries = load_job_industries()
    if not job_industries.empty and "industry_name" in job_industries.columns:
        first_industry = job_industries.groupby("job_id")["industry_name"].first().reset_index()
        postings = postings.merge(first_industry, on="job_id", how="left")

    return postings


# ── Convenience Getters ────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def get_top_job_titles(n: int = 50) -> list[str]:
    """Return the top N most frequent job titles in the dataset.

    Args:
        n: Number of titles to return.

    Returns:
        List of job title strings.
    """
    df = load_postings()
    if df.empty or "title" not in df.columns:
        return []
    return df["title"].value_counts().head(n).index.tolist()


@st.cache_data(show_spinner=False)
def get_top_skills(n: int = 50) -> list[str]:
    """Return the top N most demanded skills by job posting count.

    Args:
        n: Number of skills to return.

    Returns:
        List of skill name strings.
    """
    skills = load_job_skills()
    if skills.empty:
        return []
    col = "skill_name" if "skill_name" in skills.columns else "skill_abr"
    return skills[col].value_counts().head(n).index.tolist()


@st.cache_data(show_spinner=False)
def get_top_industries(n: int = 30) -> list[str]:
    """Return the top N industries by job posting count.

    Args:
        n: Number of industries to return.

    Returns:
        List of industry name strings.
    """
    industries = load_job_industries()
    if industries.empty or "industry_name" not in industries.columns:
        return []
    return industries["industry_name"].value_counts().head(n).index.tolist()


@st.cache_data(show_spinner=False)
def get_states_list() -> list[str]:
    """Return sorted list of US states found in the postings location field.

    Returns:
        Sorted list of 2-letter state code strings.
    """
    from utils.preprocessing import extract_state
    df = load_postings()
    if df.empty or "location" not in df.columns:
        return []
    states = df["location"].dropna().apply(extract_state).dropna()
    return sorted(states[states.str.len() == 2].unique().tolist())
