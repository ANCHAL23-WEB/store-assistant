"""Basic uptime endpoint, plus a search-index staleness check."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db

router = APIRouter()

RETRIEVAL_DIR = Path(__file__).resolve().parent.parent / "retrieval"
INDEX_METADATA_PATH = RETRIEVAL_DIR / "index_metadata.json"


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple status payload without querying dependencies."""
    return {"status": "ok"}


@router.get("/health/index")
def index_health(db: Session = Depends(get_db)) -> dict:
    """Report whether the FAISS search index matches the current product catalog.

    Compares the product count and catalog fingerprint recorded at index-build
    time (index_metadata.json) against the live database. A mismatch means the
    catalog has changed since the index was last built and it should be rebuilt
    with `python backend/retrieval/embed_products.py`.
    """
    if not INDEX_METADATA_PATH.exists():
        return {"status": "no_metadata", "detail": "Index metadata not found. Build the index first."}

    metadata = json.loads(INDEX_METADATA_PATH.read_text(encoding="utf-8"))

    row_count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
    is_stale = row_count != metadata.get("product_count")

    return {
        "status": "stale" if is_stale else "fresh",
        "index_product_count": metadata.get("product_count"),
        "live_product_count": row_count,
        "model_name": metadata.get("model_name"),
        "catalog_fingerprint": metadata.get("catalog_fingerprint"),
    }