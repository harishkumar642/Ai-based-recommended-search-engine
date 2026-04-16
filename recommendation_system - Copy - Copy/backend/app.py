from typing import Optional, Literal
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from serve import load_resources, recommend as svc_recommend, similar as svc_similar, autocomplete as svc_autocomplete

app = FastAPI(title="AI Recommendation Engine API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup():
    load_resources()

@app.get("/")
def health():
    return {"status": "ok", "message": "API is running"}

@app.get("/recommend")
def recommend(
    user_id: Optional[str] = None,
    k: int = Query(10, ge=1, le=50),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    category: Optional[str] = None,
    search_query: Optional[str] = None,  # NEW parameter
    page: int = Query(1, ge=1),
    sort_by: Optional[Literal["score", "price_asc", "price_desc", "rating", "popularity"]] = "score"
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price cannot exceed max_price")

    items = svc_recommend(
        user_id=user_id,
        k=1000,
        min_price=min_price,
        max_price=max_price,
        category=category,
        search_query=search_query  # Pass search separately
    )

    if sort_by == "price_asc":
        items = sorted(items, key=lambda x: x.get("price_num", 0))
    elif sort_by == "price_desc":
        items = sorted(items, key=lambda x: x.get("price_num", 0), reverse=True)
    elif sort_by == "rating":
        items = sorted(items, key=lambda x: (x.get("rating", 0), x.get("rating_count", 0)), reverse=True)
    elif sort_by == "popularity":
        items = sorted(items, key=lambda x: (x.get("rating_count", 0), x.get("rating", 0)), reverse=True)
    else:
        items = sorted(items, key=lambda x: x.get("final_score", 0), reverse=True)

    page_size = k
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    return {
        "total": len(items),
        "page": page,
        "page_size": page_size,
        "items": page_items
    }


@app.get("/similar/{product_id}")
def similar(product_id: str, k: int = Query(6, ge=1, le=20)):
    items = svc_similar(product_id, k=k)
    return {"count": len(items), "items": items}

@app.get("/autocomplete")
def autocomplete(q: str = Query(..., min_length=1), k: int = Query(8, ge=1, le=20)):
    suggestions = svc_autocomplete(q, k=k)
    return {"query": q, "suggestions": suggestions}
