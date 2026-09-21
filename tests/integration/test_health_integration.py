"""Integration smoke tests - hit real endpoints against a live Postgres DB."""

import pytest

pytestmark = pytest.mark.integration


class TestHealthIntegration:
    def test_health_returns_200(self, integration_client):
        response = integration_client.get("/health")
        assert response.status_code == 200

    def test_index_health_returns_status_field(self, integration_client):
        response = integration_client.get("/health/index")
        assert response.status_code == 200
        assert "status" in response.json()


class TestProductsIntegration:
    def test_list_products_returns_from_real_db(self, integration_client):
        response = integration_client.get("/products", params={"limit": 5})
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) <= 5


class TestSearchIntegration:
    def test_search_returns_real_results(self, integration_client):
        response = integration_client.get("/search", params={"q": "phone", "top_k": 5})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
