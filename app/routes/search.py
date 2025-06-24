# routes/search.py
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

# Define Search Item schema
class SearchResultItem(BaseModel):
    type: str
    name: str
    path: str

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    results: List[SearchResultItem]

# For demo, simple in-memory data (replace with real DB search)
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

@router.post("/search", response_model=SearchResponse)
def search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    query = request.query.strip().lower()
    if not query:
        return {"results": []}
    
    # Simple case-insensitive substring match
    matched = [item for item in SEARCH_INDEX if query in item["name"].lower()]
    
    # Limit results to top 10
    results = matched[:10]
    return {"results": results}

