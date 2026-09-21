"""Unit tests for the /search endpoint - mocked search_products, no real FAISS/DB."""


class TestSearchEndpointValidation:
    def test_rejects_empty_query(self, app_client, fake_search_module, no_op_usage_event):
        response = app_client.get("/search", params={"q": "", "top_k": 5})
        assert response.status_code == 422

    def test_rejects_missing_query(self, app_client, fake_search_module, no_op_usage_event):
        response = app_client.get("/search", params={"top_k": 5})
        assert response.status_code == 422

    def test_rejects_top_k_zero(self, app_client, fake_search_module, no_op_usage_event):
        response = app_client.get("/search", params={"q": "phone", "top_k": 0})
        assert response.status_code == 422

    def test_rejects_top_k_over_100(self, app_client, fake_search_module, no_op_usage_event):
        response = app_client.get("/search", params={"q": "phone", "top_k": 101})
        assert response.status_code == 422

    def test_rejects_invalid_input_type(self, app_client, fake_search_module, no_op_usage_event):
        response = app_client.get("/search", params={"q": "phone", "input_type": "telepathy"})
        assert response.status_code == 422

    def test_defaults_input_type_to_browse(self, app_client, fake_search_module, no_op_usage_event):
        fake_search_module.search_products.return_value = []

        app_client.get("/search", params={"q": "phone", "top_k": 5})

        call_kwargs = no_op_usage_event.call_args.kwargs
        assert call_kwargs["input_type"] == "browse"


class TestSearchEndpointBehavior:
    def test_returns_list_from_search_products(self, app_client, fake_search_module, no_op_usage_event):
        fake_search_module.search_products.return_value = [
            {"product_id": 1, "distance": 0.3, "name": "Test Phone", "brand": "TestBrand",
             "price": 15000.0, "specs": {}},
        ]

        response = app_client.get("/search", params={"q": "phone", "top_k": 5})

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert body[0]["name"] == "Test Phone"

    def test_calls_search_products_with_query_and_top_k(self, app_client, fake_search_module, no_op_usage_event):
        fake_search_module.search_products.return_value = []

        app_client.get("/search", params={"q": "laptop", "top_k": 3})

        fake_search_module.search_products.assert_called_once_with("laptop", 3)

    def test_logs_usage_event_with_voice_input_type(self, app_client, fake_search_module, no_op_usage_event):
        fake_search_module.search_products.return_value = []

        app_client.get("/search", params={"q": "phone", "input_type": "voice"})

        call_kwargs = no_op_usage_event.call_args.kwargs
        assert call_kwargs["input_type"] == "voice"
        assert call_kwargs["query_text"] == "phone"

    def test_logs_usage_event_with_camera_input_type(self, app_client, fake_search_module, no_op_usage_event):
        fake_search_module.search_products.return_value = []

        app_client.get("/search", params={"q": "phone", "input_type": "camera"})

        call_kwargs = no_op_usage_event.call_args.kwargs
        assert call_kwargs["input_type"] == "camera"

    def test_missing_index_returns_503(self, app_client, fake_search_module, no_op_usage_event):
        fake_search_module.search_products.side_effect = FileNotFoundError(
            "Product search index is missing. Run the embed_products script first."
        )

        response = app_client.get("/search", params={"q": "phone", "top_k": 5})

        assert response.status_code == 503

    def test_missing_index_still_logs_usage_event_with_empty_matches(self, app_client, fake_search_module, no_op_usage_event):
        fake_search_module.search_products.side_effect = FileNotFoundError("index missing")

        app_client.get("/search", params={"q": "phone", "top_k": 5})

        call_kwargs = no_op_usage_event.call_args.kwargs
        assert call_kwargs["matches"] == []
