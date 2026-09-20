"""FAISS-backed product search for the store assistant backend."""

import json
import os
import re
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import psycopg2
from dotenv import load_dotenv
from fastembed import TextEmbedding
from psycopg2.extras import RealDictCursor

RETRIEVAL_DIR = Path(__file__).resolve().parent
BACKEND_DIR = RETRIEVAL_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
INDEX_PATH = RETRIEVAL_DIR / "product_index.faiss"
PRODUCT_IDS_PATH = RETRIEVAL_DIR / "product_ids.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Maximum acceptable L2 distance for a match to be considered relevant.
# Lower = stricter (fewer, more relevant results). Tune based on testing.
MAX_DISTANCE = 1.2

# When a query has a price constraint, we need to pull more candidates from
# FAISS before filtering by price, since the nearest semantic matches often
# aren't the cheapest ones. This is the multiplier applied to top_k.
PRICE_FILTER_CANDIDATE_MULTIPLIER = 20

# Matches phrases like "under 30000", "below 50k", "less than 20,000",
# "under ₹30000", "max 40000". Captures the numeric value (with optional
# comma separators) and an optional trailing 'k' for thousands.
_PRICE_PATTERN = re.compile(
    r"(?:under|below|less than|max|up to|within)\s*(?:rs\.?|₹|inr)?\s*"
    r"([\d,]+)\s*(k)?",
    re.IGNORECASE,
)


def _extract_max_price(query: str) -> float | None:
    """Extract a maximum price constraint from natural-language query text.

    Returns None if no price constraint is found. Handles "k" shorthand
    (e.g. "under 30k" -> 30000).
    """
    match = _PRICE_PATTERN.search(query)
    if not match:
        return None
    number_str, k_suffix = match.groups()
    try:
        value = float(number_str.replace(",", ""))
    except ValueError:
        return None
    if k_suffix:
        value *= 1000
    return value


def _load_database_url() -> str:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(BACKEND_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to backend/.env or .env.")
    return database_url


def _load_index() -> tuple[faiss.Index, list[int]]:
    """Load persisted search data or explain how to create it."""
    if not INDEX_PATH.exists() or not PRODUCT_IDS_PATH.exists():
        raise FileNotFoundError(
            "Product search index is missing. Run `python backend/retrieval/embed_products.py` first."
        )

    index = faiss.read_index(str(INDEX_PATH))
    product_ids = json.loads(PRODUCT_IDS_PATH.read_text(encoding="utf-8"))
    if index.ntotal != len(product_ids):
        raise RuntimeError("Product index and product_ids mapping do not match. Rebuild the index.")
    return index, [int(product_id) for product_id in product_ids]


# Load model and persisted artifacts once, when this module is imported.
INDEX, PRODUCT_IDS = _load_index()
MODEL = TextEmbedding(model_name=MODEL_NAME)


def _fetch_products(product_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Fetch product records in one parameterized PostgreSQL query."""
    if not product_ids:
        return {}

    query = """
        SELECT product_id, name, brand, price, specs
        FROM products
        WHERE product_id = ANY(%s)
    """
    with psycopg2.connect(_load_database_url()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (product_ids,))
            return {row["product_id"]: dict(row) for row in cursor.fetchall()}


def search_products(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Return nearest products with their squared L2 distance scores.

    Results whose distance exceeds MAX_DISTANCE are dropped, since a bad
    match (e.g. searching for something not in the catalog) is worse than
    no match at all.

    If the query contains a price constraint (e.g. "under 30000"), results
    above that price are filtered out. To do this without losing relevant
    cheaper items, a larger candidate pool is pulled from FAISS first.
    """
    if not query or not query.strip() or top_k < 1:
        return []

    max_price = _extract_max_price(query)
    candidate_k = top_k
    if max_price is not None:
        candidate_k = min(top_k * PRICE_FILTER_CANDIDATE_MULTIPLIER, INDEX.ntotal)

    requested_k = min(candidate_k, INDEX.ntotal)
    if requested_k == 0:
        return []

    query_embedding = np.array(list(MODEL.embed([query])), dtype=np.float32)
    query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)
    distances, positions = INDEX.search(query_embedding, requested_k)
    matched_ids = [PRODUCT_IDS[position] for position in positions[0] if position != -1]
    products = _fetch_products(matched_ids)

    results = []
    for distance, position in zip(distances[0], positions[0]):
        if position == -1:
            continue
        if float(distance) > MAX_DISTANCE:
            continue
        product_id = PRODUCT_IDS[position]
        product = products.get(product_id)
        if not product:
            continue
        price = float(product["price"])
        if max_price is not None and price > max_price:
            continue
        results.append({
            "product_id": product_id,
            "distance": float(distance),
            "name": product["name"],
            "brand": product["brand"],
            "price": price,
            "specs": product["specs"],
        })
        if len(results) >= top_k:
            break
    return results