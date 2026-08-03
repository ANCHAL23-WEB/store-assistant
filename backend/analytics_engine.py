"""Pandas-based summaries of product-search usage events."""

from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_top_products(db: Session, limit: int = 10) -> list[dict[str, Any]]:
    """Return the most-searched products, including their catalogue details."""
    events = pd.read_sql(
        text("""
            SELECT e.product_id, p.name, p.brand
            FROM usage_events AS e
            JOIN products AS p ON p.product_id = e.product_id
            WHERE e.product_id IS NOT NULL
        """),
        db.connection(),
    )
    if events.empty:
        return []

    summary = (
        events.groupby(["product_id", "name", "brand"], as_index=False)
        .size()
        .rename(columns={"size": "search_count"})
        .sort_values(["search_count", "product_id"], ascending=[False, True])
        .head(limit)
    )
    return [
        {
            "product_id": int(row.product_id),
            "name": row.name,
            "brand": row.brand,
            "search_count": int(row.search_count),
        }
        for row in summary.itertuples(index=False)
    ]


def get_input_type_breakdown(db: Session) -> list[dict[str, Any]]:
    """Return a pandas-generated count for each search input method."""
    events = pd.read_sql(
        text("SELECT input_type FROM usage_events"),
        db.connection(),
    )
    if events.empty:
        return []

    summary = (
        events.groupby("input_type", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("input_type")
    )
    return [
        {"input_type": row.input_type, "count": int(row.count)}
        for row in summary.itertuples(index=False)
    ]


def get_searches_over_time(db: Session, days: int = 7) -> list[dict[str, Any]]:
    """Return a daily pandas count series, including dates with no searches."""
    events = pd.read_sql(
        text("""
            SELECT timestamp
            FROM usage_events
            WHERE timestamp >= CURRENT_DATE - (:days - 1) * INTERVAL '1 day'
        """),
        db.connection(),
        params={"days": days},
    )

    dates = pd.date_range(end=pd.Timestamp.now(tz="UTC").normalize(), periods=days, freq="D")
    if events.empty:
        daily_counts = pd.Series(0, index=dates, dtype="int64")
    else:
        event_dates = pd.to_datetime(events["timestamp"], utc=True).dt.normalize()
        daily_counts = event_dates.value_counts().reindex(dates, fill_value=0).sort_index()

    return [
        {"date": date.strftime("%Y-%m-%d"), "count": int(count)}
        for date, count in daily_counts.items()
    ]


def get_zero_result_searches(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    """Return recent events whose query did not result in a product match."""
    events = pd.read_sql(
        text("""
            SELECT query_text, input_type, timestamp
            FROM usage_events
            WHERE product_id IS NULL
            ORDER BY timestamp DESC, event_id DESC
            LIMIT :limit
        """),
        db.connection(),
        params={"limit": limit},
    )
    if events.empty:
        return []

    events["timestamp"] = pd.to_datetime(events["timestamp"], utc=True).map(
        lambda value: value.isoformat()
    )
    return events[["query_text", "input_type", "timestamp"]].to_dict(orient="records")
