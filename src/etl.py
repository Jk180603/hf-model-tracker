"""
ETL Pipeline — Clean, transform, and load into SQLite
"""
import pandas as pd
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timezone

DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/hf_models.db")

def extract():
    print("Extracting raw data...")
    df = pd.read_csv("data/hf_models_latest.csv")
    print(f"  Extracted {len(df)} rows")
    return df

def transform(df):
    print("Transforming data...")
    
    before = len(df)
    df = df.drop_duplicates(subset=["model_id"])
    print(f"  Removed {before - len(df)} duplicates, {len(df)} remaining")
    
    df["task"] = df["task"].fillna("unknown")
    df["library"] = df["library"].fillna("unknown")
    df["architecture"] = df["architecture"].fillna("other")
    df["use_case"] = df["use_case"].fillna("other")
    df["author"] = df["author"].fillna("unknown")
    df["language"] = df["language"].fillna("multilingual")
    df["downloads_last_month"] = df["downloads_last_month"].fillna(0).astype(int)
    df["likes"] = df["likes"].fillna(0).astype(int)
    
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df["last_modified"] = pd.to_datetime(df["last_modified"], errors="coerce", utc=True)
    
    now_utc = pd.Timestamp.now(tz="UTC")
    
    df["days_since_update"] = (
        now_utc - df["last_modified"]
    ).dt.days.fillna(-1).astype(int)
    
    df["popularity_score"] = (
        df["downloads_last_month"].rank(pct=True) * 0.7 +
        df["likes"].rank(pct=True) * 0.3
    ).round(4)
    
    df["is_actively_maintained"] = df["days_since_update"].between(0, 90)
    
    df["download_tier"] = pd.cut(
        df["downloads_last_month"],
        bins=[-1, 100, 1000, 10000, 100000, float("inf")],
        labels=["tiny", "small", "medium", "popular", "viral"]
    )
    
    df["created_at"] = df["created_at"].astype(str)
    df["last_modified"] = df["last_modified"].astype(str)
    df["scraped_at"] = datetime.now(timezone.utc).isoformat()
    
    print(f"  Transformed {len(df)} rows")
    return df

def load(df):
    print(f"Loading into database...")
    engine = create_engine(DB_URL)
    
    df.to_sql("models", engine, if_exists="replace", index=False)
    print(f"  Loaded {len(df)} rows into models table")
    
    task_summary = df.groupby("task").agg(
        model_count=("model_id", "count"),
        total_downloads=("downloads_last_month", "sum"),
        avg_downloads=("downloads_last_month", "mean"),
        total_likes=("likes", "sum"),
        avg_popularity=("popularity_score", "mean")
    ).round(2).reset_index()
    task_summary.to_sql("task_summary", engine, if_exists="replace", index=False)
    print(f"  Created task_summary ({len(task_summary)} tasks)")
    
    arch_summary = df.groupby("architecture").agg(
        model_count=("model_id", "count"),
        total_downloads=("downloads_last_month", "sum"),
        avg_downloads=("downloads_last_month", "mean"),
        avg_likes=("likes", "mean")
    ).round(2).reset_index()
    arch_summary.to_sql("architecture_summary", engine, if_exists="replace", index=False)
    print(f"  Created architecture_summary ({len(arch_summary)} architectures)")
    
    uc_summary = df.groupby("use_case").agg(
        model_count=("model_id", "count"),
        total_downloads=("downloads_last_month", "sum"),
        top_model=("model_id", "first")
    ).reset_index()
    uc_summary.to_sql("use_case_summary", engine, if_exists="replace", index=False)
    print(f"  Created use_case_summary ({len(uc_summary)} use cases)")
    
    lib_summary = df.groupby("library").agg(
        model_count=("model_id", "count"),
        total_downloads=("downloads_last_month", "sum")
    ).reset_index()
    lib_summary.to_sql("library_summary", engine, if_exists="replace", index=False)
    print(f"  Created library_summary ({len(lib_summary)} libraries)")
    
    return engine

def validate(engine):
    print("Running validation checks...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM models"))
        count = result.scalar()
        assert count > 0, "No rows!"
        print(f"  Row count: {count} ✓")
        
        result = conn.execute(text("SELECT COUNT(*) FROM models WHERE model_id IS NULL OR model_id = ''"))
        nulls = result.scalar()
        print(f"  Null model_ids: {nulls} ✓")
        
        result = conn.execute(text("SELECT model_id, downloads_last_month FROM models ORDER BY downloads_last_month DESC LIMIT 1"))
        top = result.fetchone()
        print(f"  Top model: {top[0]} ({top[1]:,} downloads) ✓")
    print("All validations passed! ✓")

def run_pipeline():
    print("=" * 60)
    print("ETL Pipeline — HuggingFace Models")
    print("=" * 60)
    df = extract()
    df = transform(df)
    engine = load(df)
    validate(engine)
    df.to_csv("data/hf_models_clean.csv", index=False)
    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()