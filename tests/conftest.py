"""Shared fixtures for the store-assistant test suite.

Sets DATABASE_URL to a dummy value before backend.db is ever imported, so
unit tests never need a real database - db.get_db is overridden per-test
with a mock session instead.
"""

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_dummy")

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture
def mock_db():
    """Stand-in for a SQLAlchemy Session.

    Configure per test, e.g.:
        mock_db.execute.return_value.first.return_value = SimpleNamespace(price=999.0)
        mock_db.execute.return_value.all.return_value = [row1, row2]
    """
    return MagicMock()


@pytest.fixture
def app_client(mock_db):
    """TestClient with get_db overridden to yield mock_db, not a real connection."""
    from fastapi.testclient import TestClient
    from db import get_db
    from main import app

    def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def fake_search_module(monkeypatch):
    """Stub retrieval.search in sys.modules so /search tests never touch the
    real FAISS index or download the embedding model.

    Set fake_search_module.search_products = MagicMock(return_value=[...])
    per test.
    """
    fake_module = types.ModuleType("retrieval.search")
    fake_module.search_products = MagicMock(return_value=[])
    monkeypatch.setitem(sys.modules, "retrieval.search", fake_module)

    fake_package = types.ModuleType("retrieval")
    fake_package.search = fake_module
    monkeypatch.setitem(sys.modules, "retrieval", fake_package)

    yield fake_module


@pytest.fixture
def no_op_usage_event(monkeypatch):
    """Silence usage-event logging so /search unit tests don't hit the DB."""
    import routes.search as search_route

    mock_log = MagicMock()
    monkeypatch.setattr(search_route, "log_usage_event", mock_log)
    return mock_log
