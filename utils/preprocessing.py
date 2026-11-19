"""
utils/preprocessing.py
Data cleaning, encoding, and feature engineering for the LinkedIn Salary Predictor.
"""

from __future__ import annotations

import re
import numpy as np
import pandas as pd
from typing import Optional, Tuple
import joblib


# ── State Abbreviation Lookup ─────────────────────────────────────────────────

_STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC",
}
_ABBR_SET = set(_STATE_ABBR.values())


def extract_state(location_str: Optional[str]) -> Optional[str]:
    """Extract a 2-letter US state code from a location string.

    Handles formats like "San Francisco, CA", "New York, New York", "Remote".

    Args:
        location_str: Raw location string from the dataset.

    Returns:
        2-letter state abbreviation or None if not extractable.
    """
    if not isinstance(location_str, str) or not location_str.strip():
        return None

    # Already an abbreviation at end: "City, ST"
    match = re.search(r",\s*([A-Z]{2})\s*$", location_str.strip())
    if match:
        code = match.group(1)
        if code in _ABBR_SET:
            return code

    # Full state name present
    for name, abbr in _STATE_ABBR.items():
        if name.lower() in location_str.lower():
            return abbr

    # Two-letter word anywhere
    match = re.search(r"\b([A-Z]{2})\b", location_str)
    if match and match.group(1) in _ABBR_SET:
        return match.group(1)

    return None


# ── Cleaning Functions ─────────────────────────────────────────────────────────

def clean_postings(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates, fix dtypes, and add derived columns to postings.

    Args:
        df: Raw postings DataFrame from load_postings().

    Returns:
        Cleaned DataFrame with duplicate job_ids removed.
    """
    if df.empty:
        return df
    df = df.drop_duplicates(subset=["job_id"], keep="first").copy()
    df["normalized_salary"] = pd.to_numeric(df.get("normalized_salary"), errors="coerce")

    # Derived columns
    if "location" in df.columns:
        df["state"] = df["location"].apply(extract_state)

    if "remote_allowed" in df.columns:
        df["remote_allowed"] = df["remote_allowed"].fillna(0).astype(int)

    return df


def parse_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Unix millisecond timestamps to datetime columns.

    Args:
        df: DataFrame with listed_time / original_listed_time columns.

    Returns:
        DataFrame with datetime columns added.
    """
    for col in ["listed_time", "original_listed_time"]:
        if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], unit="ms", errors="coerce")
    return df


def normalize_to_annual(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all salary values are annualised (USD/year).

    Applies: HOURLY × 2080, MONTHLY × 12, YEARLY unchanged.
    Works on normalized_salary when pay_period is present.

    Args:
        df: DataFrame with normalized_salary and pay_period columns.

    Returns:
        DataFrame with normalized_salary converted to annual.
    """
    if "pay_period" not in df.columns or "normalized_salary" not in df.columns:
        return df
    df = df.copy()
    hourly_mask = df["pay_period"].str.upper() == "HOURLY"
    monthly_mask = df["pay_period"].str.upper() == "MONTHLY"
    df.loc[hourly_mask, "normalized_salary"] *= 2080
    df.loc[monthly_mask, "normalized_salary"] *= 12
    return df


def remove_salary_outliers(df: pd.DataFrame, col: str = "normalized_salary") -> pd.DataFrame:
    """Remove extreme salary outliers using the IQR method.

    Args:
        df: DataFrame containing the salary column.
        col: Name of the salary column.

    Returns:
        DataFrame with outlier rows removed.
    """
    if col not in df.columns:
        return df
    q1 = df[col].quantile(0.05)
    q3 = df[col].quantile(0.95)
    iqr = q3 - q1
    lower = q1 - 3 * iqr
    upper = q3 + 3 * iqr
    return df[(df[col] >= max(lower, 0)) & (df[col] <= upper)].copy()


# ── Encoding Helpers ───────────────────────────────────────────────────────────

_EXPERIENCE_ORDER = {
    "Internship": 0,
    "Entry level": 1,
    "Associate": 2,
    "Mid-Senior level": 3,
    "Director": 4,
    "Executive": 5,
}

_COMPANY_SIZE_ORDER = {
    "1-10": 0,
    "11-50": 1,
    "51-200": 2,
    "201-500": 3,
    "501-1000": 4,
    "1001-5000": 5,
    "5001-10000": 6,
    "10001+": 7,
}

_PAY_PERIOD_ORDER = {
    "HOURLY": 0,
    "WEEKLY": 1,
    "BIWEEKLY": 2,
    "MONTHLY": 3,
    "YEARLY": 4,
}


def encode_features(df: pd.DataFrame, encoders: Optional[dict] = None) -> Tuple[pd.DataFrame, dict]:
    """Apply all label and ordinal encodings needed for ML.

    If encoders is None, fit new encoders from df.
    Otherwise transform df using the provided encoders (inference mode).

    Args:
        df: DataFrame with raw feature columns.
        encoders: Optional dict of {column_name: mapping_dict or LabelEncoder}.

    Returns:
        Tuple of (encoded DataFrame, encoders dict).
    """
    df = df.copy()
    if encoders is None:
        encoders = {}
        fit_mode = True
    else:
        fit_mode = False

    # ── Ordinal Encodings ──────────────────────────────────────
    def ordinal_encode(col: str, order_map: dict, fill_val: int = -1) -> None:
        if col not in df.columns:
            df[col + "_encoded"] = fill_val
            return
        if fit_mode:
            encoders[col] = order_map
        df[col + "_encoded"] = df[col].map(order_map).fillna(fill_val).astype(int)

    ordinal_encode("formatted_experience_level", _EXPERIENCE_ORDER)
    ordinal_encode("company_size", _COMPANY_SIZE_ORDER)

    # Pay period
    if "pay_period" in df.columns:
        pp_map = _PAY_PERIOD_ORDER if fit_mode else encoders.get("pay_period", _PAY_PERIOD_ORDER)
        if fit_mode:
            encoders["pay_period"] = pp_map
        df["pay_period_encoded"] = df["pay_period"].str.upper().map(pp_map).fillna(3).astype(int)

    # ── Label Encodings ────────────────────────────────────────
    def label_encode(col: str, new_col: Optional[str] = None) -> None:
        target = new_col or (col + "_encoded")
        if col not in df.columns:
            df[target] = -1
            return
        if fit_mode:
            categories = df[col].fillna("Unknown").astype(str).unique().tolist()
            mapping = {cat: idx for idx, cat in enumerate(sorted(categories))}
            encoders[col] = mapping
        else:
            mapping = encoders.get(col, {})
        df[target] = df[col].fillna("Unknown").astype(str).map(mapping).fillna(-1).astype(int)

    label_encode("formatted_work_type", "work_type_encoded")
    label_encode("state", "state_encoded")
    label_encode("industry_name", "industry_encoded")

    # ── Binary ─────────────────────────────────────────────────
    df["remote_allowed"] = df.get("remote_allowed", pd.Series(0)).fillna(0).astype(int)

    # ── Log transforms ─────────────────────────────────────────
    df["log_views"] = np.log1p(df.get("views", pd.Series(0)).fillna(0))
    df["log_applies"] = np.log1p(df.get("applies", pd.Series(0)).fillna(0))

    return df, encoders


def build_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]:
    """Build the feature matrix X and target vector y for ML training.

    Args:
        df: Encoded DataFrame from encode_features().

    Returns:
        Tuple of (X DataFrame, y Series, feature_names list).
    """
    feature_names = [
        "formatted_experience_level_encoded",
        "work_type_encoded",
        "remote_allowed",
        "state_encoded",
        "company_size_encoded",
        "industry_encoded",
        "pay_period_encoded",
        "skill_count",
        "benefit_count",
        "log_views",
        "log_applies",
    ]
    # Only keep features that exist
    available = [f for f in feature_names if f in df.columns]
    target_col = "normalized_salary"

    mask = df[target_col].notna()
    X = df.loc[mask, available].fillna(-1)
    y = df.loc[mask, target_col]

    return X, y, available


def encode_single_input(input_dict: dict, encoders: dict) -> pd.DataFrame:
    """Encode a single prediction input dict using saved encoders.

    Args:
        input_dict: Dict with raw feature values from the UI form.
        encoders: Encoders dict loaded from encoders.pkl.

    Returns:
        Single-row DataFrame ready for model.predict().
    """
    row = {}

    # Experience
    row["formatted_experience_level_encoded"] = _EXPERIENCE_ORDER.get(
        input_dict.get("formatted_experience_level", ""), -1
    )
    # Work type
    wt_map = encoders.get("formatted_work_type", {})
    row["work_type_encoded"] = wt_map.get(str(input_dict.get("formatted_work_type", "")), -1)
    # Remote
    row["remote_allowed"] = int(input_dict.get("remote_allowed", 0))
    # State
    st_map = encoders.get("state", {})
    row["state_encoded"] = st_map.get(str(input_dict.get("state", "")), -1)
    # Company size
    row["company_size_encoded"] = _COMPANY_SIZE_ORDER.get(
        str(input_dict.get("company_size", "")), -1
    )
    # Industry
    ind_map = encoders.get("industry_name", {})
    row["industry_encoded"] = ind_map.get(str(input_dict.get("industry_name", "")), -1)
    # Pay period
    pp_map = encoders.get("pay_period", _PAY_PERIOD_ORDER)
    row["pay_period_encoded"] = pp_map.get(
        str(input_dict.get("pay_period", "YEARLY")).upper(), 3
    )
    # Counts
    row["skill_count"] = int(input_dict.get("skill_count", 0))
    row["benefit_count"] = int(input_dict.get("benefit_count", 0))
    row["log_views"] = np.log1p(float(input_dict.get("views", 0)))
    row["log_applies"] = np.log1p(float(input_dict.get("applies", 0)))

    return pd.DataFrame([row])
