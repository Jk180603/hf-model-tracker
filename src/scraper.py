"""
HuggingFace Model Scraper — Fetches trending AI model data
"""
import requests
import pandas as pd
import json
import os
import time
from datetime import datetime

API_URL = "https://huggingface.co/api/models"

def fetch_models(limit=500, sort="downloads", direction=-1):
    """Fetch model metadata from HuggingFace API"""
    print(f"Fetching top {limit} models sorted by {sort}...")
    
    all_models = []
    batch_size = 100
    
    for offset in range(0, limit, batch_size):
        params = {
            "sort": sort,
            "direction": direction,
            "limit": batch_size,
            "offset": offset,
            "full": "true"
        }
        
        try:
            resp = requests.get(API_URL, params=params, timeout=30)
            resp.raise_for_status()
            models = resp.json()
            
            for m in models:
                model_data = {
                    "model_id": m.get("modelId", ""),
                    "author": m.get("author", "unknown"),
                    "model_name": m.get("modelId", "").split("/")[-1] if "/" in m.get("modelId", "") else m.get("modelId", ""),
                    "downloads_last_month": m.get("downloads", 0),
                    "likes": m.get("likes", 0),
                    "task": m.get("pipeline_tag", "unknown"),
                    "library": m.get("library_name", "unknown"),
                    "tags": ", ".join(m.get("tags", [])[:10]),
                    "created_at": m.get("createdAt", ""),
                    "last_modified": m.get("lastModified", ""),
                    "private": m.get("private", False),
                    "gated": m.get("gated", False),
                    "sha": m.get("sha", "")[:8],
                }
                
                # Extract architecture from tags
                tags = m.get("tags", [])
                arch_tags = [t for t in tags if t in [
                    "bert", "gpt2", "t5", "llama", "mistral", "falcon",
                    "roberta", "distilbert", "albert", "electra", "bart",
                    "whisper", "stable-diffusion", "vit", "clip", "sam",
                    "gemma", "phi", "qwen", "deepseek", "yi"
                ]]
                model_data["architecture"] = arch_tags[0] if arch_tags else "other"
                
                # Extract language
                lang_tags = [t for t in tags if len(t) == 2 and t.isalpha()]
                model_data["language"] = lang_tags[0] if lang_tags else "multilingual"
                
                # Categorize by use case
                task = m.get("pipeline_tag", "")
                if task in ["text-generation", "text2text-generation"]:
                    model_data["use_case"] = "text_generation"
                elif task in ["text-classification", "sentiment-analysis", "zero-shot-classification"]:
                    model_data["use_case"] = "classification"
                elif task in ["token-classification", "ner"]:
                    model_data["use_case"] = "ner_extraction"
                elif task in ["question-answering"]:
                    model_data["use_case"] = "question_answering"
                elif task in ["translation", "translation_xx_to_yy"]:
                    model_data["use_case"] = "translation"
                elif task in ["summarization"]:
                    model_data["use_case"] = "summarization"
                elif task in ["fill-mask"]:
                    model_data["use_case"] = "masked_language"
                elif task in ["image-classification", "object-detection", "image-segmentation"]:
                    model_data["use_case"] = "computer_vision"
                elif task in ["automatic-speech-recognition", "audio-classification"]:
                    model_data["use_case"] = "audio_speech"
                elif task in ["text-to-image", "image-to-text"]:
                    model_data["use_case"] = "image_generation"
                elif task in ["feature-extraction", "sentence-similarity"]:
                    model_data["use_case"] = "embeddings"
                else:
                    model_data["use_case"] = "other"
                
                all_models.append(model_data)
            
            print(f"  Fetched {offset + len(models)}/{limit} models")
            time.sleep(0.5)  # rate limiting
            
        except Exception as e:
            print(f"  Error at offset {offset}: {e}")
            continue
    
    df = pd.DataFrame(all_models)
    
    # Save raw data
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = f"data/hf_models_raw_{timestamp}.csv"
    df.to_csv(filepath, index=False)
    df.to_csv("data/hf_models_latest.csv", index=False)
    
    print(f"\nScraped {len(df)} models")
    print(f"Saved to {filepath}")
    print(f"\nTop 5 tasks:")
    print(df["task"].value_counts().head())
    print(f"\nTop 5 architectures:")
    print(df["architecture"].value_counts().head())
    print(f"\nTop 5 use cases:")
    print(df["use_case"].value_counts().head())
    print(f"\nTop 5 libraries:")
    print(df["library"].value_counts().head())
    
    return df


def fetch_trending():
    """Fetch currently trending models"""
    print("\nFetching trending models...")
    params = {"sort": "trending", "direction": -1, "limit": 50, "full": "true"}
    
    try:
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        models = resp.json()
        
        trending = []
        for m in models:
            trending.append({
                "model_id": m.get("modelId", ""),
                "task": m.get("pipeline_tag", "unknown"),
                "downloads": m.get("downloads", 0),
                "likes": m.get("likes", 0),
                "library": m.get("library_name", "unknown"),
                "trending_rank": len(trending) + 1
            })
        
        df_trending = pd.DataFrame(trending)
        df_trending.to_csv("data/hf_trending.csv", index=False)
        print(f"Saved {len(df_trending)} trending models")
        return df_trending
        
    except Exception as e:
        print(f"Error fetching trending: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    print("=" * 60)
    print("HuggingFace Model Scraper")
    print("=" * 60)
    
    df = fetch_models(limit=500)
    df_trending = fetch_trending()
    
    print("\n" + "=" * 60)
    print("Scraping complete!")
    print(f"Total models: {len(df)}")
    print(f"Trending models: {len(df_trending)}")
    print("=" * 60)