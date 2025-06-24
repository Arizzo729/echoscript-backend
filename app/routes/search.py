from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db

router = APIRouter(
    prefix="/api",
    tags=["Search"],
    responses={404: {"description": "Not found"}}
)

# === Schema Definitions ===
class SearchResultItem(BaseModel):
    type: str
    name: str
    path: str

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    results: List[SearchResultItem]

# === Demo Search Index (Replace with DB/AI in production) ===
SEARCH_INDEX = [
    {"type": "Page", "name": "Dashboard", "path": "/dashboard"},
    {"type": "Page", "name": "Upload Audio", "path": "/upload"},
    {"type": "Page", "name": "Upload Video", "path": "/video"},
    {"type": "Page", "name": "Buy Minutes", "path": "/purchase/minutes"},
    {"type": "Tool", "name": "Echo Assistant", "path": "/assistant"},
    {"type": "Page", "name": "Settings", "path": "/settings"},
    {"type": "Page", "name": "Account", "path": "/account"},
    {"type": "Page", "name": "Transcripts", "path": "/transcripts"},
    {"type": "Page", "name": "Summary Generator", "path": "/summary"},
    {"type": "Page", "name": "History", "path": "/history"},
    {"type": "Page", "name": "Contact Us", "path": "/contact"},
]

# === Search Route ===
@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, db: Session = Depends(get_db)):
    query = request.query.strip().lower()
    if not query:
        return {"results": []}

    # Enhanced fuzzy match scoring (basic demo version)
    def score(item):
        name = item["name"].lower()
        if query == name:
            return 3  # exact
        elif query in name:
            return 2  # partial
        elif name.startswith(query):
            return 1  # prefix
        return 0

    ranked = sorted([item for item in SEARCH_INDEX if score(item) > 0], key=score, reverse=True)
    results = ranked[:10]

    return {"results": results}
