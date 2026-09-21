import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"


def _real_database_url():
    # The root conftest sets a dummy DATABASE_URL (via setdefault) so unit
    # tests never need a real DB. Integration tests need the real one, so
    # reload .env with override=True to replace the dummy.
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    load_dotenv(BACKEND_DIR / ".env", override=True)
    return os.getenv("DATABASE_URL")


@pytest.fixture(scope="session")
def integration_client():
    """Real TestClient against a live Postgres DB - no mocking.

    Skips the whole test if no real DATABASE_URL is configured (e.g. in CI
    before docker-compose is wired up, or on a machine with no local Postgres).
    """
    database_url = _real_database_url()
    if not database_url or "test_dummy" in database_url:
        pytest.skip("No real DATABASE_URL configured - skipping integration tests.")

    from fastapi.testclient import TestClient
    from main import app

    return TestClient(app)
