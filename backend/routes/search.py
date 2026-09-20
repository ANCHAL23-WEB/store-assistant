"""Semantic product-search endpoint."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db
from events import log_usage_event

router = APIRouter()


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Natural-language product query"),
    top_k: int = Query(5, ge=1, le=100, description="Maximum number of matches"),
    input_type: Literal["browse", "voice", "camera"] = Query(
        "browse", description="How the query was entered: browse (typed), voice, or camera"
    ),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return products nearest to the query in the FAISS embedding index."""
    try:
        # Import here so the application can start before an index has been built.
        from retrieval.search import search_products

        results = search_products(q, top_k)
        log_usage_event(db, input_type=input_type, query_text=q, matches=results)
        return results
    except FileNotFoundError as error:
        log_usage_event(db, input_type=input_type, query_text=q, matches=[])
        raise HTTPException(status_code=503, detail=str(error)) from error