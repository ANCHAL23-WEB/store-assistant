"""Unit tests for the /price-match endpoints ? mocked DB, no live Postgres."""

from types import SimpleNamespace


class TestCheckPriceMatchEndpoint:
    def test_product_not_found_returns_404(self, app_client, mock_db):
        mock_db.execute.return_value.first.return_value = None

        response = app_client.post("/price-match", json={
            "product_id": 999999999,
            "store_id": 1,
            "competitor_price": 100.0,
            "source": "test",
        })

        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"

    def test_store_not_found_returns_404(self, app_client, mock_db):
        # First execute() call -> product lookup (found).
        # Second execute() call -> store lookup (not found).
        mock_db.execute.side_effect = [
            SimpleNamespace(first=lambda: SimpleNamespace(price=1000.0)),
            SimpleNamespace(first=lambda: None),
        ]

        response = app_client.post("/price-match", json={
            "product_id": 1,
            "store_id": 999999999,
            "competitor_price": 100.0,
            "source": "test",
        })

        assert response.status_code == 404
        assert response.json()["detail"] == "Store not found"

    def test_valid_request_returns_evaluated_result(self, app_client, mock_db):
        mock_db.execute.side_effect = [
            SimpleNamespace(first=lambda: SimpleNamespace(price=1000.0)),
            SimpleNamespace(first=lambda: SimpleNamespace(store_id=1)),
            None,  # the INSERT in log_price_match_event
        ]

        response = app_client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": 950.0,
            "source": "test",
        })

        assert response.status_code == 200
        body = response.json()
        assert body["approved"] is True
        assert body["final_price"] == 950.0
        assert body["store_price"] == 1000.0

    def test_valid_request_logs_event_and_commits(self, app_client, mock_db):
        mock_db.execute.side_effect = [
            SimpleNamespace(first=lambda: SimpleNamespace(price=1000.0)),
            SimpleNamespace(first=lambda: SimpleNamespace(store_id=1)),
            None,
        ]

        app_client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": 950.0,
            "source": "test",
        })

        # log_price_match_event should have called execute() 3 times total
        # (product lookup, store lookup, INSERT) and committed once.
        assert mock_db.execute.call_count == 3
        assert mock_db.commit.call_count == 1

    def test_negative_competitor_price_rejected_before_hitting_db(self, app_client, mock_db):
        response = app_client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": -50.0,
            "source": "test",
        })

        assert response.status_code == 422
        mock_db.execute.assert_not_called()

    def test_zero_competitor_price_rejected(self, app_client, mock_db):
        response = app_client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": 0,
            "source": "test",
        })

        assert response.status_code == 422

    def test_missing_source_rejected(self, app_client, mock_db):
        response = app_client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": 100.0,
        })

        assert response.status_code == 422

    def test_empty_source_rejected(self, app_client, mock_db):
        response = app_client.post("/price-match", json={
            "product_id": 1,
            "store_id": 1,
            "competitor_price": 100.0,
            "source": "",
        })

        assert response.status_code == 422


class TestPriceMatchHistoryEndpoint:
    def test_returns_list_from_db(self, app_client, mock_db):
        fake_row = SimpleNamespace(_mapping={
            "event_id": 1, "store_id": 1, "competitor_price": 900.0,
            "source": "test", "discount_applied": 100.0, "timestamp": "2026-01-01",
        })
        mock_db.execute.return_value.all.return_value = [fake_row]

        response = app_client.get("/price-match/history/1")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert body[0]["event_id"] == 1

    def test_empty_history_returns_empty_list(self, app_client, mock_db):
        mock_db.execute.return_value.all.return_value = []

        response = app_client.get("/price-match/history/1")

        assert response.status_code == 200
        assert response.json() == []

    def test_respects_limit_param(self, app_client, mock_db):
        mock_db.execute.return_value.all.return_value = []

        app_client.get("/price-match/history/1", params={"limit": 5})

        called_params = mock_db.execute.call_args[0][1]
        assert called_params["limit"] == 5

    def test_rejects_limit_zero(self, app_client, mock_db):
        response = app_client.get("/price-match/history/1", params={"limit": 0})
        assert response.status_code == 422

    def test_rejects_limit_over_100(self, app_client, mock_db):
        response = app_client.get("/price-match/history/1", params={"limit": 101})
        assert response.status_code == 422
