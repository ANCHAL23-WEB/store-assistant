"""Semantic product-search endpoint."""

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Natural-language product query"),
    top_k: int = Query(5, ge=1, le=100, description="Maximum number of matches"),
) -> list[dict]:
    """Return products nearest to the query in the FAISS embedding index."""
    try:
        # Import here so the application can start before an index has been built.
        from retrieval.search import search_products

        return search_products(q, top_k)
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
