"""
Analysis — Generate insights from the HuggingFace model data
"""
import pandas as pd
from sqlalchemy import create_engine, text
import json
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/hf_models.db")

def analyze():
    engine = create_engine(DB_URL)
    
    print("=" * 60)
    print("HuggingFace Model Trends Analysis")
    print("=" * 60)
    
    with engine.connect() as conn:
        
        # 1. Most popular tasks
        print("\n📊 TOP 10 TASKS BY TOTAL DOWNLOADS:")
        result = conn.execute(text(
            "SELECT task, model_count, total_downloads, ROUND(avg_downloads, 0) as avg_dl "
            "FROM task_summary ORDER BY total_downloads DESC LIMIT 10"
        ))
        for row in result:
            print(f"  {row[0]:30s} | {row[1]:4d} models | {row[2]:>15,} downloads | avg: {int(row[3]):>10,}")
        
        # 2. Most popular architectures
        print("\n🧠 TOP 10 ARCHITECTURES:")
        result = conn.execute(text(
            "SELECT architecture, model_count, total_downloads "
            "FROM architecture_summary ORDER BY total_downloads DESC LIMIT 10"
        ))
        for row in result:
            print(f"  {row[0]:20s} | {row[1]:4d} models | {row[2]:>15,} downloads")
        
        # 3. Use case distribution
        print("\n🎯 USE CASE DISTRIBUTION:")
        result = conn.execute(text(
            "SELECT use_case, model_count, total_downloads "
            "FROM use_case_summary ORDER BY total_downloads DESC"
        ))
        for row in result:
            print(f"  {row[0]:25s} | {row[1]:4d} models | {row[2]:>15,} downloads")
        
        # 4. Most downloaded models overall
        print("\n🏆 TOP 10 MOST DOWNLOADED MODELS:")
        result = conn.execute(text(
            "SELECT model_id, task, downloads_last_month, likes "
            "FROM models ORDER BY downloads_last_month DESC LIMIT 10"
        ))
        for i, row in enumerate(result, 1):
            print(f"  {i:2d}. {row[0]:45s} | {row[1]:25s} | {row[2]:>12,} dl | {row[3]:>6,} likes")
        
        # 5. Library ecosystem
        print("\n📚 LIBRARY ECOSYSTEM:")
        result = conn.execute(text(
            "SELECT library, model_count, total_downloads "
            "FROM library_summary ORDER BY total_downloads DESC LIMIT 8"
        ))
        for row in result:
            print(f"  {row[0]:25s} | {row[1]:4d} models | {row[2]:>15,} downloads")
        
        # 6. Actively maintained percentage
        result = conn.execute(text(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN is_actively_maintained = 1 THEN 1 ELSE 0 END) as active "
            "FROM models"
        ))
        row = result.fetchone()
        pct = (row[1] / row[0] * 100) if row[0] > 0 else 0
        print(f"\n🔄 MAINTENANCE STATUS:")
        print(f"  {row[1]}/{row[0]} models ({pct:.1f}%) updated in last 90 days")
        
        # 7. Generate insights JSON
        insights = {
            "total_models_analyzed": row[0],
            "actively_maintained_pct": round(pct, 1),
            "generated_at": pd.Timestamp.now().isoformat(),
        }
        
        # Top task
        result = conn.execute(text(
            "SELECT task, total_downloads FROM task_summary ORDER BY total_downloads DESC LIMIT 1"
        ))
        top_task = result.fetchone()
        insights["most_popular_task"] = {"task": top_task[0], "downloads": top_task[1]}
        
        # Top architecture
        result = conn.execute(text(
            "SELECT architecture, total_downloads FROM architecture_summary ORDER BY total_downloads DESC LIMIT 1"
        ))
        top_arch = result.fetchone()
        insights["most_popular_architecture"] = {"architecture": top_arch[0], "downloads": top_arch[1]}
        
        with open("data/insights.json", "w") as f:
            json.dump(insights, f, indent=2)
        
        print(f"\n💾 Insights saved to data/insights.json")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    analyze()