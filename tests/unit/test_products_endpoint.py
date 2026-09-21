"""Unit tests for /products endpoints - mocked DB, no live Postgres."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def no_op_product_usage_event(monkeypatch):
    """Silence usage-event logging in routes.products."""
    import routes.products as products_route

    mock_log = MagicMock()
    monkeypatch.setattr(products_route, "log_usage_event", mock_log)
    return mock_log


def _row(mapping):
    """Build a fake SQLAlchemy row with a ._mapping attribute."""
    return SimpleNamespace(_mapping=mapping)


class TestGetProductByBarcode:
    def test_found_returns_product_with_inventory(self, app_client, mock_db, no_op_product_usage_event):
        product_row = _row({
            "product_id": 1, "name": "Test Phone", "category_id": 1, "category": "Phones",
            "brand": "TestBrand", "price": 15000.0, "colors": ["black"], "specs": {},
            "image_url": "http://example.com/img.jpg", "barcode": "12345",
        })
        inventory_row = _row({
            "store_id": 1, "store_name": "Test Store", "location": "Somewhere",
            "city": "Kolkata", "stock_qty": 5, "restock_eta_days": 0,
        })
        mock_db.execute.side_effect = [
            SimpleNamespace(first=lambda: product_row),
            SimpleNamespace(all=lambda: [inventory_row]),
        ]

        response = app_client.get("/products/barcode/12345")

        assert response.status_code == 200
        body = response.json()
        assert body["product_id"] == 1
        assert body["inventory"][0]["store_name"] == "Test Store"

    def test_found_logs_camera_usage_event_with_match(self, app_client, mock_db, no_op_product_usage_event):
        product_row = _row({
            "product_id": 1, "name": "Test Phone", "category_id": 1, "category": "Phones",
            "brand": "TestBrand", "price": 15000.0, "colors": ["black"], "specs": {},
            "image_url": "", "barcode": "12345",
        })
        mock_db.execute.side_effect = [
            SimpleNamespace(first=lambda: product_row),
            SimpleNamespace(all=lambda: []),
        ]

        app_client.get("/products/barcode/12345")

        call_kwargs = no_op_product_usage_event.call_args.kwargs
        assert call_kwargs["input_type"] == "camera"
        assert call_kwargs["query_text"] == "12345"
        assert call_kwargs["matches"] == [{"product_id": 1}]

    def test_not_found_returns_404(self, app_client, mock_db, no_op_product_usage_event):
        mock_db.execute.return_value.first.return_value = None

        response = app_client.get("/products/barcode/nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "No product found for that barcode"

    def test_not_found_still_logs_camera_usage_event_with_empty_matches(self, app_client, mock_db, no_op_product_usage_event):
        mock_db.execute.return_value.first.return_value = None

        app_client.get("/products/barcode/nonexistent")

        call_kwargs = no_op_product_usage_event.call_args.kwargs
        assert call_kwargs["input_type"] == "camera"
        assert call_kwargs["matches"] == []


class TestGetProduct:
    def test_found_returns_product_with_inventory(self, app_client, mock_db):
        product_row = _row({
            "product_id": 1, "name": "Test Phone", "category_id": 1, "category": "Phones",
            "brand": "TestBrand", "price": 15000.0, "colors": ["black"], "specs": {},
            "image_url": "",
        })
        mock_db.execute.side_effect = [
            SimpleNamespace(first=lambda: product_row),
            SimpleNamespace(all=lambda: []),
        ]

        response = app_client.get("/products/1")

        assert response.status_code == 200
        assert response.json()["product_id"] == 1

    def test_not_found_returns_404(self, app_client, mock_db):
        mock_db.execute.return_value.first.return_value = None

        response = app_client.get("/products/999999999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"


class TestListProducts:
    def test_returns_list(self, app_client, mock_db):
        row = _row({
            "product_id": 1, "name": "Test Phone", "category_id": 1, "category": "Phones",
            "brand": "TestBrand", "price": 15000.0, "colors": ["black"], "specs": {},
            "image_url": "",
        })
        mock_db.execute.return_value.all.return_value = [row]

        response = app_client.get("/products")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert body[0]["name"] == "Test Phone"

    def test_passes_category_filter_to_query(self, app_client, mock_db):
        mock_db.execute.return_value.all.return_value = []

        app_client.get("/products", params={"category": "Phones"})

        called_params = mock_db.execute.call_args[0][1]
        assert called_params["category"] == "Phones"

    def test_no_category_defaults_to_none(self, app_client, mock_db):
        mock_db.execute.return_value.all.return_value = []

        app_client.get("/products")

        called_params = mock_db.execute.call_args[0][1]
        assert called_params["category"] is None

    def test_respects_limit_param(self, app_client, mock_db):
        mock_db.execute.return_value.all.return_value = []

        app_client.get("/products", params={"limit": 5})

        called_params = mock_db.execute.call_args[0][1]
        assert called_params["limit"] == 5

    def test_rejects_limit_zero(self, app_client, mock_db):
        response = app_client.get("/products", params={"limit": 0})
        assert response.status_code == 422

    def test_rejects_limit_over_100(self, app_client, mock_db):
        response = app_client.get("/products", params={"limit": 101})
        assert response.status_code == 422

    def test_rejects_empty_category_string(self, app_client, mock_db):
        response = app_client.get("/products", params={"category": ""})
        assert response.status_code == 422
