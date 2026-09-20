"""
Search evaluation: compares keyword search, TF-IDF, and FAISS+embeddings
on a manually judged relevance set. Computes Precision@5, Recall@5, MRR, and
latency for each method.

Usage:
    cd backend
    python -m eval.evaluate_search

Requires: DATABASE_URL in .env (project root or backend/), scikit-learn installed
(pip install scikit-learn --break-system-packages)

Relevance labels: eval/relevance_judgments.jsonl — each line is
{"query_id": int, "query": str, "relevant_product_ids": [int, ...]},
manually judged by inspecting live search results (see eval/METHODOLOGY.md).
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Make backend/retrieval importable
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from retrieval.embed_products import build_product_description, fetch_products, _load_database_url
from retrieval.search import search_products as faiss_search

EVAL_DIR = Path(__file__).resolve().parent
JUDGMENTS_PATH = EVAL_DIR / "relevance_judgments.jsonl"
TOP_K = 5


def load_queries() -> list[dict[str, Any]]:
    """Load manually judged queries. Each has 'query' and 'relevant_product_ids'."""
    queries = []
    with open(JUDGMENTS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    return queries


def load_products() -> list[dict[str, Any]]:
    """Fetch all products with id and description text (for keyword/TF-IDF search)."""
    products = fetch_products(_load_database_url())
    for p in products:
        p["description"] = build_product_description(p).lower()
    return products


def keyword_search(query: str, products: list[dict], top_k: int = TOP_K) -> list[int]:
    """Simple keyword search: rank by number of query tokens found in description."""
    tokens = query.lower().split()
    scored = []
    for p in products:
        score = sum(1 for t in tokens if t in p["description"])
        if score > 0:
            scored.append((score, p["id"]))
    scored.sort(key=lambda x: -x[0])
    return [pid for _, pid in scored[:top_k]]


def tfidf_search_factory(products: list[dict]):
    """Precompute TF-IDF matrix once; return a search function."""
    descriptions = [p["description"] for p in products]
    ids = [p["id"] for p in products]
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(descriptions)

    def _search(query: str, top_k: int = TOP_K) -> list[int]:
        query_vec = vectorizer.transform([query.lower()])
        sims = cosine_similarity(query_vec, matrix).flatten()
        top_indices = np.argsort(-sims)[:top_k]
        return [ids[i] for i in top_indices if sims[i] > 0]

    return _search


def precision_at_k(retrieved: list[int], relevant: set[int], k: int) -> float:
    if not retrieved:
        return 0.0
    top = retrieved[:k]
    hits = sum(1 for pid in top if pid in relevant)
    return hits / len(top)


def recall_at_k(retrieved: list[int], relevant: set[int], k: int) -> float:
    if not relevant:
        return 0.0
    top = retrieved[:k]
    hits = sum(1 for pid in top if pid in relevant)
    return hits / len(relevant)


def reciprocal_rank(retrieved: list[int], relevant: set[int]) -> float:
    for rank, pid in enumerate(retrieved, start=1):
        if pid in relevant:
            return 1.0 / rank
    return 0.0


def evaluate_method(name: str, search_fn, queries: list[dict]) -> dict:
    precisions, recalls, rrs, latencies = [], [], [], []
    skipped = 0

    for q in queries:
        relevant = set(q["relevant_product_ids"])
        if not relevant:
            # No relevant products exist for this query (genuine no-result case).
            # Skip from precision/recall/MRR averaging but still counted below.
            skipped += 1
            continue

        start = time.perf_counter()
        retrieved = search_fn(q["query"])
        elapsed = time.perf_counter() - start

        precisions.append(precision_at_k(retrieved, relevant, TOP_K))
        recalls.append(recall_at_k(retrieved, relevant, TOP_K))
        rrs.append(reciprocal_rank(retrieved, relevant))
        latencies.append(elapsed)

    return {
        "method": name,
        "precision@5": round(np.mean(precisions), 3) if precisions else 0.0,
        "recall@5": round(np.mean(recalls), 3) if recalls else 0.0,
        "mrr": round(np.mean(rrs), 3) if rrs else 0.0,
        "avg_latency_ms": round(np.mean(latencies) * 1000, 1) if latencies else 0.0,
        "queries_evaluated": len(precisions),
        "queries_skipped_no_relevant": skipped,
    }


def main():
    print("Loading products from database...")
    products = load_products()
    print(f"Loaded {len(products)} products.")

    queries = load_queries()
    print(f"Loaded {len(queries)} manually judged queries.")

    print("Building TF-IDF index...")
    tfidf_fn = tfidf_search_factory(products)

    def keyword_fn(q):
        return keyword_search(q, products)

    def faiss_fn(q):
        results = faiss_search(q, top_k=TOP_K)
        return [r["product_id"] for r in results]

    print("\nEvaluating methods (this may take a minute for FAISS/embeddings)...\n")
    results = [
        evaluate_method("Keyword Search", keyword_fn, queries),
        evaluate_method("TF-IDF", tfidf_fn, queries),
        evaluate_method("FAISS + Embeddings", faiss_fn, queries),
    ]

    # Print results table
    print(f"{'Method':<22}{'Precision@5':<14}{'Recall@5':<12}{'MRR':<8}{'Latency(ms)':<14}{'N':<5}")
    print("-" * 75)
    for r in results:
        print(f"{r['method']:<22}{r['precision@5']:<14}{r['recall@5']:<12}{r['mrr']:<8}"
              f"{r['avg_latency_ms']:<14}{r['queries_evaluated']:<5}")

    # Save results as JSON for README table generation
    output_path = EVAL_DIR / "results.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()