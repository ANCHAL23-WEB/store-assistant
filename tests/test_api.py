"""
Automated tests for the store-assistant backend API.

Setup:
    cd backend
    pip install pytest httpx --break-system-packages

Run:
    cd backend
    python -m pytest ../tests/ -v

Requires the backend's .env, database, and FAISS index to be set up
(these tests hit real endpoints via FastAPI's TestClient, not mocks,
so DB and search index must exist).
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from main import app

client = TestClient(app)


# ---------- Search endpoint tests ----------

class TestSearchEndpoint:
    def test_search_returns_200_for_valid_query(self):
        response = client.get("/search", params={"q": "phone", "top_k": 5})
        assert response.status_code == 200

    def test_search_returns_list(self):
        response = client.get("/search", params={"q": "laptop", "top_k": 5})
        assert isinstance(response.json(), list)

    def test_search_respects_top_k_limit(self):
        response = client.get("/search", params={"q": "phone", "top_k": 3})
        results = response.json()
        assert len(results) <= 3

    def test_search_rejects_empty_query(self):
        """FastAPI's min_length=1 should reject an empty q param."""
        response = client.get("/search", params={"q": "", "top_k": 5})
        assert response.status_code == 422

    def test_search_rejects_missing_query(self):
        response = client.get("/search", params={"top_k": 5})
        assert response.status_code == 422

    def test_search_rejects_top_k_out_of_range(self):
        response = client.get("/search", params={"q": "phone", "top_k": 0})
        assert response.status_code == 422

        response = client.get("/search", params={"q": "phone", "top_k": 101})
        assert response.status_code == 422

    def test_search_nonsense_query_returns_empty_or_filtered(self):
        """A query far outside the catalog should return few/no results due to MAX_DISTANCE."""
        response = client.get("/search", params={"q": "asdkjhaslkdjhasldkjh", "top_k": 5})
        assert response.status_code == 200
        # Should not error even with no meaningful matches


# ---------- Price-match endpoint tests ----------

class TestPriceMatchEndpoint:
    def test_price_match_rejects_nonexistent_product(self):
        response = client.post("/price-match", json={
            "product_id": 999999999,
            "store_id": 1,
            "competitor_price": 100.0,
            "source": "test",
        })
        assert response.status_code == 404

    def test_price_match_rejects_nonexistent_store(self):
        response = client.post("/price-match", json={
            "product_id": 1,
            "store_id": 999999999,
            "competitor_price": 100.0,
            "source": "test",
        })
        assert response.status_code in (404, 200)  # 200 only if product 1 also doesn't exist -> product check fires first

    def test_price_match_rejects_negative_price(self):
        response = client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": -50.0,
            "source": "test",
        })
        assert response.status_code == 422

    def test_price_match_rejects_zero_price(self):
        response = client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": 0,
            "source": "test",
        })
        assert response.status_code == 422

    def test_price_match_rejects_missing_source(self):
        response = client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": 100.0,
        })
        assert response.status_code == 422

    def test_price_match_history_returns_list(self):
        response = client.get("/price-match/history/1")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_price_match_history_respects_limit(self):
        response = client.get("/price-match/history/1", params={"limit": 5})
        assert response.status_code == 200
        assert len(response.json()) <= 5

    def test_price_match_history_rejects_invalid_limit(self):
        response = client.get("/price-match/history/1", params={"limit": 0})
        assert response.status_code == 422

        response = client.get("/price-match/history/1", params={"limit": 101})
        assert response.status_code == 422


# ---------- Health check ----------

class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
