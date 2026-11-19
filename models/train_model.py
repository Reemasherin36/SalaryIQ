"""
models/train_model.py
One-time model training script for the LinkedIn Salary Predictor.
Run once: python models/train_model.py

Trains RandomForest, GradientBoosting, and Ridge regression.
Auto-selects best model by R² and saves salary_model.pkl + encoders.pkl.
"""

from __future__ import annotations

import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # type: ignore[reportMissingModuleSource]

warnings.filterwarnings("ignore")

# ── Resolve paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODEL_OUT = os.path.join(SCRIPT_DIR, "salary_model.pkl")
ENCODERS_OUT = os.path.join(SCRIPT_DIR, "encoders.pkl")


def load_raw_data() -> pd.DataFrame:
    """Load and merge all required CSVs for training.

    Returns:
        Merged DataFrame with all required features.
    """
    print("📂 Loading postings.csv …")
    postings_path = os.path.join(DATA_DIR, "postings.csv")
    required_cols = [
        "job_id", "company_id", "title", "location",
        "normalized_salary", "pay_period", "formatted_work_type",
        "formatted_experience_level", "remote_allowed",
        "views", "applies", "currency",
    ]
    df = pd.read_csv(
        postings_path,
        usecols=lambda c: c in required_cols,
        dtype={"job_id": str, "company_id": str, "normalized_salary": float},
        low_memory=False,
    )
    total_rows = len(df)
    print(f"   Loaded {total_rows:,} rows from postings.csv")

    # Sample for memory safety
    MAX_ROWS = 100_000
    if len(df) > MAX_ROWS:
        df = df.sample(MAX_ROWS, random_state=42)
        print(f"   ⚠️  Sampled {MAX_ROWS:,} rows for training (memory optimisation).")

    # Skill counts
    print("📂 Loading job_skills.csv …")
    try:
        skill_counts = (
            pd.read_csv(os.path.join(DATA_DIR, "jobs", "job_skills.csv"),
                        dtype={"job_id": str}, low_memory=False)
            .groupby("job_id").size().reset_index(name="skill_count")
        )
        df = df.merge(skill_counts, on="job_id", how="left")
        df["skill_count"] = df["skill_count"].fillna(0).astype(int)
    except FileNotFoundError:
        df["skill_count"] = 0
        print("   ⚠️  job_skills.csv not found — skill_count set to 0.")

    # Benefit counts
    print("📂 Loading benefits.csv …")
    try:
        benefit_counts = (
            pd.read_csv(os.path.join(DATA_DIR, "jobs", "benefits.csv"),
                        dtype={"job_id": str}, low_memory=False)
            .groupby("job_id").size().reset_index(name="benefit_count")
        )
        df = df.merge(benefit_counts, on="job_id", how="left")
        df["benefit_count"] = df["benefit_count"].fillna(0).astype(int)
    except FileNotFoundError:
        df["benefit_count"] = 0
        print("   ⚠️  benefits.csv not found — benefit_count set to 0.")

    # Company size
    print("📂 Loading companies.csv …")
    try:
        companies = pd.read_csv(
            os.path.join(DATA_DIR, "companies", "companies.csv"),
            usecols=lambda c: c in ["company_id", "company_size"],
            dtype={"company_id": str}, low_memory=False,
        )
        df = df.merge(companies, on="company_id", how="left")
    except FileNotFoundError:
        df["company_size"] = "Unknown"
        print("   ⚠️  companies.csv not found.")

    # Industry (first match per job)
    print("📂 Loading industries …")
    try:
        job_ind = pd.read_csv(os.path.join(DATA_DIR, "jobs", "job_industries.csv"),
                              dtype={"job_id": str}, low_memory=False)
        ind_map = pd.read_csv(os.path.join(DATA_DIR, "mappings", "industries.csv"),
                              low_memory=False)
        merged_ind = job_ind.merge(ind_map, on="industry_id", how="left")
        first_ind = merged_ind.groupby("job_id")["industry_name"].first().reset_index()
        df = df.merge(first_ind, on="job_id", how="left")
    except (FileNotFoundError, KeyError):
        df["industry_name"] = "Unknown"
        print("   ⚠️  Industry files not found.")

    return df


def preprocess(df: pd.DataFrame):
    """Clean, encode, and split the training data.

    Args:
        df: Raw merged DataFrame.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test, encoders, feature_names).
    """
    from utils.preprocessing import (
        clean_postings, remove_salary_outliers, encode_features, build_feature_matrix
    )

    print("\n🔧 Preprocessing …")
    df = clean_postings(df)
    df = df[df["normalized_salary"].notna() & (df["normalized_salary"] > 5_000) &
            (df["normalized_salary"] < 5_000_000)].copy()
    df = remove_salary_outliers(df)
    print(f"   Rows after cleaning: {len(df):,}")

    df, encoders = encode_features(df, encoders=None)
    X, y, feature_names = build_feature_matrix(df)
    print(f"   Features: {feature_names}")
    print(f"   Training samples: {len(X):,}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    return X_train, X_test, y_train, y_test, encoders, feature_names


def build_pipeline(model) -> Pipeline:
    """Wrap a model in a sklearn Pipeline with imputer + scaler.

    Args:
        model: Scikit-learn estimator.

    Returns:
        Fitted-ready Pipeline.
    """
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", model),
    ])


def evaluate_model(pipeline: Pipeline, X_train, X_test, y_train, y_test,
                   name: str) -> dict:
    """Fit and evaluate a pipeline; print and return metrics.

    Args:
        pipeline: Sklearn Pipeline containing model.
        X_train: Training features.
        X_test: Test features.
        y_train: Training target.
        y_test: Test target.
        name: Model name for display.

    Returns:
        Dict with MAE, RMSE, R2, CV_mean, CV_std.
    """
    t0 = time.time()
    pipeline.fit(X_train, y_train)
    elapsed = time.time() - t0
    y_pred = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5,
                                scoring="r2", n_jobs=-1)
    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()

    print(f"\n  📊 {name}  ({elapsed:.1f}s)")
    print(f"     MAE:  ${mae:>12,.0f}")
    print(f"     RMSE: ${rmse:>12,.0f}")
    print(f"     R²:    {r2:.4f}")
    print(f"     5-Fold CV R²: {cv_mean:.4f} ± {cv_std:.4f}")

    return {"name": name, "pipeline": pipeline,
            "MAE": mae, "RMSE": rmse, "R2": r2,
            "CV_mean": cv_mean, "CV_std": cv_std}


def train_all_models(X_train, X_test, y_train, y_test) -> list[dict]:
    """Train RF, GradientBoosting, and Ridge; return metrics list.

    Args:
        X_train, X_test, y_train, y_test: Split data arrays.

    Returns:
        List of metric dicts from evaluate_model().
    """
    models = [
        ("Random Forest",
         RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)),
        ("Gradient Boosting",
         GradientBoostingRegressor(n_estimators=200, random_state=42)),
        ("Ridge Regression",
         Ridge(alpha=1.0)),
    ]
    results = []
    for name, model in models:
        pipe = build_pipeline(model)
        metrics = evaluate_model(pipe, X_train, X_test, y_train, y_test, name)
        results.append(metrics)
    return results


def save_best_model(results: list[dict], encoders: dict, feature_names: list) -> None:
    """Select the highest R² model and save both model and encoders to disk.

    Args:
        results: List of metric dicts from train_all_models().
        encoders: Dict of fitted encoders from encode_features().
        feature_names: List of feature column names.
    """
    best = max(results, key=lambda r: r["R2"])
    print(f"\n🏆 Best model: {best['name']}  (R² = {best['R2']:.4f})")

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    joblib.dump(best["pipeline"], MODEL_OUT)
    joblib.dump({"encoders": encoders, "feature_names": feature_names}, ENCODERS_OUT)
    print(f"✅ Model saved  → {MODEL_OUT}")
    print(f"✅ Encoders saved → {ENCODERS_OUT}")


def print_comparison_table(results: list[dict]) -> None:
    """Print a formatted comparison table of all model metrics.

    Args:
        results: List of metric dicts.
    """
    print("\n" + "=" * 65)
    print(f"{'Model':<22} {'MAE':>12} {'RMSE':>12} {'R²':>8} {'CV R²':>10}")
    print("=" * 65)
    for r in results:
        print(f"{r['name']:<22} ${r['MAE']:>11,.0f} ${r['RMSE']:>11,.0f} "
              f"{r['R2']:>8.4f} {r['CV_mean']:>8.4f}±{r['CV_std']:.4f}")
    print("=" * 65)


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 LinkedIn Salary Predictor — Model Training")
    print("=" * 55)

    df_raw = load_raw_data()
    X_train, X_test, y_train, y_test, encoders, feature_names = preprocess(df_raw)

    print("\n🤖 Training models …")
    results = train_all_models(X_train, X_test, y_train, y_test)
    print_comparison_table(results)
    save_best_model(results, encoders, feature_names)
    print("\n✅ Training complete! Run `streamlit run app.py` to launch the app.")
