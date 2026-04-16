from __future__ import annotations
import os
from pathlib import Path
import math
import pickle
import json
from typing import List, Optional, Dict, Any

import pandas as pd

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:
    TfidfVectorizer = None
    cosine_similarity = None

# Globals
CATALOG: Optional[pd.DataFrame] = None
TFIDF: Optional[Any] = None
TFIDF_MATRIX: Optional[Any] = None
VOCAB_SUGGEST: Optional[Dict[str, int]] = None

# Paths
HERE = Path(__file__).parent
MODELS_DIR = HERE / "models"
ROOT_MODELS_DIR = HERE.parent / "models"  # Add this line
CANDIDATE_CSVS = [
    ROOT_MODELS_DIR / "catalog_enriched.csv",  # Check root/models first
    MODELS_DIR / "catalog_enriched.csv",
    HERE.parent / "data" / "smartphones-smartphones.csv",
]


def _first_existing(paths: List[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None

def _prep_catalog(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Column name harmonization
    possible_name_cols = ["product_name", "title", "name"]
    for c in possible_name_cols:
        if c in df.columns:
            df.rename(columns={c: "product_name"}, inplace=True)
            break
    
    if "product_id" not in df.columns:
        df["product_id"] = [f"P{i:06d}" for i in range(len(df))]
    
    # IMAGE URL HANDLING - CHECK FOR img_link COLUMN
    if "img_link" in df.columns:
        df["image_url"] = df["img_link"].fillna("").astype(str)
    elif "image_url" not in df.columns:
        # Check for other common image column names
        possible_img_cols = ["image", "img_url", "product_image", "image_link", "img"]
        for c in possible_img_cols:
            if c in df.columns:
                df["image_url"] = df[c].fillna("").astype(str)
                break
        else:
            df["image_url"] = ""  # No image column found
    
    # Parse price
    if "price_num" not in df.columns:
        if "price" in df.columns:
            df["price_num"] = (
                df["price"]
                .astype(str)
                .str.replace(r"[^\d.]", "", regex=True)
                .replace("", "0")
                .astype(float)
            )
        else:
            df["price_num"] = 0.0
    else:
        df["price_num"] = pd.to_numeric(df["price_num"], errors="coerce").fillna(0.0)
    
    # Ratings
    if "rating" not in df.columns:
        df["rating"] = 0.0
    else:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    
    if "rating_count" not in df.columns:
        df["rating_count"] = 0
    else:
        df["rating_count"] = pd.to_numeric(df["rating_count"], errors="coerce").fillna(0).astype(int)
    
    if "category" not in df.columns:
        df["category"] = "General"
    
    # Popularity + confidence
    df["rating01"] = (df["rating"].clip(1, 5) - 1.0) / 4.0
    df["pop_score"] = df["rating01"] * (df["rating_count"] + 1).apply(lambda x: math.log(x + 1))
    denom = math.log(101)
    df["confidence"] = (df["rating_count"] + 1).apply(
        lambda x: max(0.5, min(1.0, math.log(x + 1) / denom))
    )
    
    # Text features
    df["features"] = (
        df["product_name"].fillna("") + " " + df["category"].fillna("")
    ).str.lower()
    
    keep_cols = [
        "product_id", "product_name", "category", "image_url",
        "price_num", "rating", "rating_count",
        "rating01", "pop_score", "confidence", "features"
    ]
    return df[keep_cols].drop_duplicates(subset=["product_id"]).reset_index(drop=True)


def _build_tfidf(df: pd.DataFrame):
    global TFIDF, TFIDF_MATRIX
    if TfidfVectorizer is None:
        TFIDF = None
        TFIDF_MATRIX = None
        return
    TFIDF = TfidfVectorizer(stop_words="english", max_features=2000, ngram_range=(1, 2))
    TFIDF_MATRIX = TFIDF.fit_transform(df["features"].fillna(""))

def _build_autocomplete_vocab(df: pd.DataFrame):
    global VOCAB_SUGGEST
    counts: Dict[str, int] = {}
    for name in df["product_name"].fillna("").astype(str):
        for w in name.lower().split():
            counts[w] = counts.get(w, 0) + 1
    VOCAB_SUGGEST = dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:5000])

def load_resources() -> bool:
    global CATALOG
    csv_path = _first_existing(CANDIDATE_CSVS)
    if not csv_path:
        # Fallback data
        data = [
            {"product_id":"B07JWH4J1","product_name":"OnePlus Nord CE 2 Lite 5G","category":"Electronics|Mobile","price_num":18999,"rating":4.1,"rating_count":12546},
            {"product_id":"B09G9BL5CP","product_name":"Samsung Galaxy M13","category":"Electronics|Mobile","price_num":12499,"rating":4.0,"rating_count":8734},
            {"product_id":"B0BNDHYBG7","product_name":"Redmi 12 5G","category":"Electronics|Mobile","price_num":13999,"rating":4.2,"rating_count":5623},
        ]
        CATALOG = _prep_catalog(pd.DataFrame(data))
    else:
        CATALOG = _prep_catalog(pd.read_csv(csv_path))
    
    _build_tfidf(CATALOG)
    _build_autocomplete_vocab(CATALOG)
    return CATALOG is not None and len(CATALOG) > 0
def _apply_filters(df: pd.DataFrame, min_price: Optional[float], max_price: Optional[float], category: Optional[str]) -> pd.DataFrame:
    out = df
    if min_price is not None:
        out = out[out["price_num"] >= float(min_price)]
    if max_price is not None:
        out = out[out["price_num"] <= float(max_price)]
    if category:
        out = out[out["category"].str.contains(str(category), case=False, na=False)]
    return out

def recommend(
    user_id: Optional[str] = None,
    k: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
    search_query: Optional[str] = None,  # NEW parameter
) -> List[Dict[str, Any]]:
    """
    Hybrid scoring (CF placeholder + popularity*confidence).
    Now supports searching by product name!
    """
    assert CATALOG is not None, "Call load_resources() first"
    df = CATALOG.copy()
    
    # Apply filters
    if min_price is not None:
        df = df[df["price_num"] >= float(min_price)]
    if max_price is not None:
        df = df[df["price_num"] <= float(max_price)]
    
    # NEW: Search in product name OR category
    if search_query:
        search_lower = str(search_query).lower()
        # Search in both product_name and category
        df = df[
            df["product_name"].str.lower().str.contains(search_lower, na=False) |
            df["category"].str.lower().str.contains(search_lower, na=False)
        ]
    elif category:
        # If no search query, filter by category only
        df = df[df["category"].str.contains(str(category), case=False, na=False)]
    
    if len(df) == 0:
        return []
    
    # Placeholder CF score (0); plug your CF outputs here if available
    df["cf_score"] = 0.0
    
    # Hybrid score
    df["final_score"] = 0.7 * df["cf_score"] + 0.3 * (df["pop_score"] * df["confidence"])
    df = df.sort_values(["final_score", "rating", "rating_count"], ascending=[False, False, False])
    
    cols = ["product_id", "product_name", "category", "image_url", "price_num", "rating", "rating_count", "final_score"]
    return df[cols].head(int(k)).to_dict(orient="records")


def similar(product_id: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Content-based similarity using TF-IDF cosine similarity.
    Falls back to top-popular if TF-IDF is unavailable or product not found.
    """
    assert CATALOG is not None, "Call load_resources() first"
    if TFIDF is None or TFIDF_MATRIX is None:
        # Fallback: return popular items excluding the query
        df = CATALOG[CATALOG["product_id"] != product_id].copy()
        df = df.sort_values(["pop_score", "rating_count"], ascending=False)
        cols = ["product_id", "product_name", "category", "price_num", "rating", "rating_count"]
        return df[cols].head(int(k)).to_dict(orient="records")
    
    try:
        idx = CATALOG.index[CATALOG["product_id"] == product_id].tolist()[0]
    except IndexError:
        # Unknown product_id → fallback popular
        df = CATALOG.sort_values(["pop_score", "rating_count"], ascending=False)
        cols = ["product_id", "product_name", "category", "image_url", "price_num", "rating", "rating_count"]
        return df.head(int(k)).to_dict(orient="records")
    
    sims = cosine_similarity(TFIDF_MATRIX[idx], TFIDF_MATRIX).ravel()
    CATALOG["_sim"] = sims
    df = CATALOG[CATALOG["product_id"] != product_id].sort_values("_sim", ascending=False)
    cols = ["product_id", "product_name", "category", "price_num", "rating", "rating_count"]
    out = df[cols].head(int(k)).to_dict(orient="records")
    CATALOG.drop(columns=["_sim"], inplace=True, errors="ignore")
    return out

def autocomplete(prefix: str, k: int = 5) -> List[str]:
    """
    Simple frequency-based autocomplete from product titles.
    If a trained RNN tokenizer exists in models, plug it here.
    """
    if not prefix:
        return []
    if not VOCAB_SUGGEST:
        return []
    p = prefix.lower().strip()
    words = [w for w in VOCAB_SUGGEST.keys() if w.startswith(p)]
    return words[:int(k)]
