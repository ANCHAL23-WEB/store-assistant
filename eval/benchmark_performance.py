"""
Performance benchmark: measures latency breakdown (embedding, FAISS search,
DB fetch) and memory usage at the current product catalog scale.

Usage:
    cd store-assistant
    python -m eval.benchmark_performance
"""

import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from retrieval.search import INDEX, MODEL, PRODUCT_IDS, _load_database_url, _fetch_products

SAMPLE_QUERIES = [
    "phone with good camera",
    "waterproof bluetooth speaker",
    "laptop 16gb ram",
    "washing machine front load",
    "wireless earbuds noise cancelling",
]


def embed_query(query: str) -> np.ndarray:
    """Embed one query using FastEmbed, returning a (1, dim) float32 array."""
    embedding = np.array(list(MODEL.embed([query])), dtype=np.float32)
    return np.ascontiguousarray(embedding, dtype=np.float32)


def benchmark_embedding(query: str, n_runs: int = 10) -> float:
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        embed_query(query)
        times.append(time.perf_counter() - start)
    return float(np.mean(times)) * 1000  # ms


def benchmark_faiss_search(query_embedding, top_k: int = 5, n_runs: int = 10) -> float:
    query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        INDEX.search(query_embedding, top_k)
        times.append(time.perf_counter() - start)
    return float(np.mean(times)) * 1000  # ms


def benchmark_db_fetch(product_ids: list[int], n_runs: int = 10) -> float:
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        _fetch_products(product_ids)
        times.append(time.perf_counter() - start)
    return float(np.mean(times)) * 1000  # ms


def get_catalog_size() -> int:
    with psycopg2.connect(_load_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM products")
            return cur.fetchone()[0]


def main():
    catalog_size = get_catalog_size()
    print(f"Current catalog size: {catalog_size} products")
    print(f"FAISS index size: {INDEX.ntotal} vectors\n")

    tracemalloc.start()

    embedding_times = []
    faiss_times = []
    db_times = []

    for query in SAMPLE_QUERIES:
        emb_time = benchmark_embedding(query)
        embedding_times.append(emb_time)

        query_embedding = embed_query(query)
        faiss_time = benchmark_faiss_search(query_embedding)
        faiss_times.append(faiss_time)

        # sample product ids for DB fetch benchmark
        sample_ids = PRODUCT_IDS[:5]
        db_time = benchmark_db_fetch(sample_ids)
        db_times.append(db_time)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    avg_embedding = np.mean(embedding_times)
    avg_faiss = np.mean(faiss_times)
    avg_db = np.mean(db_times)
    total = avg_embedding + avg_faiss + avg_db

    print(f"{'Stage':<25}{'Avg Time (ms)':<15}{'% of Total'}")
    print("-" * 55)
    print(f"{'Query Embedding':<25}{avg_embedding:<15.2f}{avg_embedding/total*100:.1f}%")
    print(f"{'FAISS Search':<25}{avg_faiss:<15.2f}{avg_faiss/total*100:.1f}%")
    print(f"{'DB Fetch (5 products)':<25}{avg_db:<15.2f}{avg_db/total*100:.1f}%")
    print("-" * 55)
    print(f"{'TOTAL (end-to-end)':<25}{total:<15.2f}100.0%")
    print(f"\nPeak memory during benchmark: {peak / 1024 / 1024:.2f} MB")
    print(f"\nCatalog size for this run: {catalog_size} products")


if __name__ == "__main__":
    main()
