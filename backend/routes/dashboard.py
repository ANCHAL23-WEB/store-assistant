"""Dashboard-ready analytics summaries."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from analytics_engine import (
    get_input_type_breakdown,
    get_searches_over_time,
    get_top_products,
    get_zero_result_searches,
)
from db import get_db

router = APIRouter()


@router.get("/dashboard/top-products")
def top_products(
    limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)
) -> list[dict]:
    """Return the most-searched products."""
    return get_top_products(db, limit)


@router.get("/dashboard/input-breakdown")
def input_breakdown(db: Session = Depends(get_db)) -> list[dict]:
    """Return the counts of browser, camera, and voice searches."""
    return get_input_type_breakdown(db)


@router.get("/dashboard/searches-over-time")
def searches_over_time(
    days: int = Query(7, ge=1, le=365), db: Session = Depends(get_db)
) -> list[dict]:
    """Return daily search counts for the requested period."""
    return get_searches_over_time(db, days)


@router.get("/dashboard/zero-results")
def zero_results(
    limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)
) -> list[dict]:
    """Return recent queries without a matched product."""
    return get_zero_result_searches(db, limit)
