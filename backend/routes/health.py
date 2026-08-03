"""Basic uptime endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple status payload without querying dependencies."""
    return {"status": "ok"}
