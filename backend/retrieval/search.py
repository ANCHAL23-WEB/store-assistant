"""FAISS-backed product search for the store assistant backend."""

import json
import os
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer

RETRIEVAL_DIR = Path(__file__).resolve().parent
BACKEND_DIR = RETRIEVAL_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
INDEX_PATH = RETRIEVAL_DIR / "product_index.faiss"
PRODUCT_IDS_PATH = RETRIEVAL_DIR / "product_ids.json"
MODEL_NAME = "all-MiniLM-L6-v2"


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
MODEL = SentenceTransformer(MODEL_NAME)


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
    """Return nearest products with their squared L2 distance scores."""
    if not query or not query.strip() or top_k < 1:
        return []

    requested_k = min(top_k, INDEX.ntotal)
    if requested_k == 0:
        return []

    query_embedding = MODEL.encode([query], convert_to_numpy=True)
    query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)
    distances, positions = INDEX.search(query_embedding, requested_k)
    matched_ids = [PRODUCT_IDS[position] for position in positions[0] if position != -1]
    products = _fetch_products(matched_ids)

    results = []
    for distance, position in zip(distances[0], positions[0]):
        if position == -1:
            continue
        product_id = PRODUCT_IDS[position]
        product = products.get(product_id)
        if product:
            results.append({
                "product_id": product_id,
                "distance": float(distance),
                "name": product["name"],
                "brand": product["brand"],
                "price": float(product["price"]),
                "specs": product["specs"],
            })
    return results
