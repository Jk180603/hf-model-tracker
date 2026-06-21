"""
FastAPI — Serve HuggingFace model trends data
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import json
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/hf_models.db")
engine = create_engine(DB_URL)

app = FastAPI(
    title="HuggingFace Model Trends API",
    description="Explore trending AI models, architectures, and use cases from HuggingFace",
    version="1.0.0"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def root():
    with open("data/insights.json") as f:
        insights = json.load(f)
    return {
        "message": "HuggingFace Model Trends API",
        "endpoints": ["/top-models", "/tasks", "/architectures", "/use-cases", "/search", "/insights"],
        "insights": insights
    }


@app.get("/top-models")
def top_models(limit: int = Query(default=20, le=100), task: str = Query(default=None)):
    with engine.connect() as conn:
        if task:
            result = conn.execute(text(
                "SELECT model_id, task, use_case, architecture, library, "
                "downloads_last_month, likes, popularity_score "
                "FROM models WHERE task = :task "
                "ORDER BY downloads_last_month DESC LIMIT :limit"
            ), {"task": task, "limit": limit})
        else:
            result = conn.execute(text(
                "SELECT model_id, task, use_case, architecture, library, "
                "downloads_last_month, likes, popularity_score "
                "FROM models ORDER BY downloads_last_month DESC LIMIT :limit"
            ), {"limit": limit})
        
        models = [dict(row._mapping) for row in result]
    
    if not models:
        raise HTTPException(status_code=404, detail=f"No models found for task: {task}")
    return {"count": len(models), "models": models}


@app.get("/tasks")
def tasks():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT * FROM task_summary ORDER BY total_downloads DESC"
        ))
        data = [dict(row._mapping) for row in result]
    return {"count": len(data), "tasks": data}


@app.get("/architectures")
def architectures():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT * FROM architecture_summary ORDER BY total_downloads DESC"
        ))
        data = [dict(row._mapping) for row in result]
    return {"count": len(data), "architectures": data}


@app.get("/use-cases")
def use_cases():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT * FROM use_case_summary ORDER BY total_downloads DESC"
        ))
        data = [dict(row._mapping) for row in result]
    return {"count": len(data), "use_cases": data}


@app.get("/search")
def search(q: str = Query(..., min_length=2), limit: int = Query(default=10, le=50)):
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT model_id, task, use_case, architecture, downloads_last_month, likes "
            "FROM models WHERE model_id LIKE :q OR task LIKE :q OR architecture LIKE :q "
            "ORDER BY downloads_last_month DESC LIMIT :limit"
        ), {"q": f"%{q}%", "limit": limit})
        models = [dict(row._mapping) for row in result]
    return {"query": q, "count": len(models), "results": models}


@app.get("/insights")
def insights():
    with open("data/insights.json") as f:
        return json.load(f)


@app.get("/health")
def health():
    return {"status": "healthy"}