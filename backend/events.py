"""Helpers for recording product-search usage events."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def log_usage_event(
    db: Session,
    *,
    input_type: str,
    query_text: str,
    matches: Sequence[dict[str, Any]],
) -> None:
    """Persist one search event, associating it with the highest-ranked match."""
    product_id = matches[0].get("product_id") if matches else None
    db.execute(
        text("""
            INSERT INTO usage_events (product_id, input_type, query_text)
            VALUES (:product_id, :input_type, :query_text)
        """),
        {
            "product_id": product_id,
            "input_type": input_type,
            "query_text": query_text,
        },
    )
    db.commit()
