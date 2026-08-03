"""Usage-event analytics endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db

router = APIRouter()


@router.get("/analytics/events")
def list_usage_events(
    limit: int | None = Query(None, ge=1, le=1000),
    input_type: Literal["camera", "voice", "browse"] | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return recent search events, optionally filtered by their input type."""
    query_sql = """
        SELECT event_id, employee_id, product_id, input_type, query_text, timestamp
        FROM usage_events
        WHERE (:input_type IS NULL OR input_type = :input_type)
        ORDER BY timestamp DESC, event_id DESC
    """
    parameters = {"input_type": input_type}
    if limit is not None:
        query_sql += " LIMIT :limit"
        parameters["limit"] = limit

    rows = db.execute(text(query_sql), parameters).all()
    return [dict(row._mapping) for row in rows]
