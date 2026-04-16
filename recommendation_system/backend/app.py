# backend/app.py
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from serve import load_resources, recommend, similar, autocomplete

app = FastAPI(title="AI Recommendation Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    load_resources()

@app.get("/")
def health():
    return {"status": "ok", "message": "API running"}

@app.get("/recommend")
def api_recommend(
    user_id: Optional[str] = None,
    k: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
):
    items = recommend(user_id=user_id, k=k, min_price=min_price, max_price=max_price, category=category)
    return {"count": len(items), "items": items}

@app.get("/similar/{product_id}")
def api_similar(product_id: str, k: int = 5):
    items = similar(product_id, k=k)
    return {"count": len(items), "items": items}

@app.get("/autocomplete")
def api_autocomplete(q: str, k: int = 5):
    return {"query": q, "suggestions": autocomplete(q, k=k)}
