# app/routes/search.py
from fastapi import APIRouter, Query
from typing import List, Optional
from app.services.search_service import search_documents

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
def search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, gt=0, le=50, description="Max number of results to return")
):
    """
    Perform full-text search across documents.

    - **q**: The search query string
    - **limit**: Maximum number of search results
    """
    try:
        results = search_documents(query=q, limit=limit)
        return {"query": q, "results": results}
    except Exception as e:
        return {"error": str(e)}
