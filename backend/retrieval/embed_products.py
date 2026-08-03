"""Build the product vector index used by the store assistant's text retrieval."""

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
    """Load DATABASE_URL from the project's .env, with a backend fallback."""
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(BACKEND_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to backend/.env or .env.")
    return database_url


def flatten_specs(specs: Any, prefix: str = "") -> list[str]:
    """Turn a JSON object into readable, searchable key/value text fragments."""
    if isinstance(specs, dict):
        fragments: list[str] = []
        for key, value in specs.items():
            nested_key = f"{prefix}.{key}" if prefix else str(key)
            fragments.extend(flatten_specs(value, nested_key))
        return fragments
    if isinstance(specs, list):
        return [f"{prefix}: {', '.join(map(str, specs))}"]
    return [f"{prefix}: {specs}"]


def build_product_description(product: dict[str, Any]) -> str:
    """Build the text representation used to embed one product."""
    fields = [product["name"], product["brand"]]
    if product.get("category"):
        fields.append(f"category: {product['category']}")
    fields.extend(flatten_specs(product.get("specs") or {}))
    return ", ".join(str(field) for field in fields if field)


def fetch_products(database_url: str) -> list[dict[str, Any]]:
    """Retrieve every product and its category name from PostgreSQL."""
    query = """
        SELECT p.product_id AS id, p.name, p.brand, p.specs, c.name AS category
        FROM products AS p
        JOIN categories AS c ON c.category_id = p.category_id
        ORDER BY p.product_id
    """
    with psycopg2.connect(database_url) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]


def main() -> None:
    """Embed all products and persist the FAISS index and ID mapping."""
    products = fetch_products(_load_database_url())
    if not products:
        raise RuntimeError("No products found. Add products before building the retrieval index.")

    descriptions = [build_product_description(product) for product in products]
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(descriptions, convert_to_numpy=True, show_progress_bar=True)
    embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, str(INDEX_PATH))
    PRODUCT_IDS_PATH.write_text(
        json.dumps([product["id"] for product in products]), encoding="utf-8"
    )
    print(f"Indexed {len(products)} products in {INDEX_PATH}")


if __name__ == "__main__":
    main()
