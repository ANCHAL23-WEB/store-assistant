"""Basic uptime endpoint, plus a search-index staleness check."""

import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db

router = APIRouter()

RETRIEVAL_DIR = Path(__file__).resolve().parent.parent / "retrieval"
INDEX_METADATA_PATH = RETRIEVAL_DIR / "index_metadata.json"


def _compute_fingerprint(product_ids: list[int]) -> str:
    """Deterministic hash of the sorted product ID set - mirrors embed_products.py."""
    sorted_ids = sorted(product_ids)
    payload = ",".join(str(pid) for pid in sorted_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple status payload without querying dependencies."""
    return {"status": "ok"}


@router.get("/health/index")
def index_health(db: Session = Depends(get_db)) -> dict:
    """Report whether the FAISS search index matches the current product catalog.

    Compares the catalog fingerprint recorded at index-build time
    (index_metadata.json) against a live fingerprint computed from the
    current product ID set. This catches products being added or removed
    even when the total count coincidentally stays the same (e.g. one
    product removed and a different one added).

    Note: the fingerprint is over product IDs only, not full row content -
    it will not detect a price or spec change to an existing product ID.
    Catching that would require hashing full product content, which this
    does not currently do.

    A mismatch means the catalog has changed since the index was last built
    and it should be rebuilt with `python backend/retrieval/embed_products.py`.
    """
    if not INDEX_METADATA_PATH.exists():
        return {"status": "no_metadata", "detail": "Index metadata not found. Build the index first."}

    metadata = json.loads(INDEX_METADATA_PATH.read_text(encoding="utf-8"))

    rows = db.execute(text("SELECT product_id FROM products")).all()
    live_product_ids = [row[0] for row in rows]
    live_fingerprint = _compute_fingerprint(live_product_ids)

    stored_fingerprint = metadata.get("catalog_fingerprint")
    is_stale = live_fingerprint != stored_fingerprint

    return {
        "status": "stale" if is_stale else "fresh",
        "index_product_count": metadata.get("product_count"),
        "live_product_count": len(live_product_ids),
        "model_name": metadata.get("model_name"),
        "index_fingerprint": stored_fingerprint,
        "live_fingerprint": live_fingerprint,
    }
