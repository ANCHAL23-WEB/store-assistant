"""Price-match evaluation endpoints."""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db
from price_match import evaluate_price_match, get_price_match_history, log_price_match_event

router = APIRouter()


@router.post("/price-match")
def check_price_match(
    product_id: int = Body(..., embed=True),
    store_id: int = Body(..., embed=True),
    competitor_price: float = Body(..., embed=True, gt=0),
    source: str = Body(..., embed=True, min_length=1),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate a competitor price against a product's store price and log the decision."""
    product = db.execute(
        text("SELECT price FROM products WHERE product_id = :product_id"),
        {"product_id": product_id},
    ).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    store = db.execute(
        text("SELECT store_id FROM stores WHERE store_id = :store_id"),
        {"store_id": store_id},
    ).first()
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")

    result = evaluate_price_match(store_price=float(product.price), competitor_price=competitor_price)

    log_price_match_event(
        db,
        product_id=product_id,
        store_id=store_id,
        competitor_price=competitor_price,
        source=source,
        discount_applied=result.discount_applied,
    )

    return {
        "approved": result.approved,
        "store_price": result.store_price,
        "competitor_price": result.competitor_price,
        "discount_applied": result.discount_applied,
        "final_price": result.final_price,
        "reason": result.reason,
    }


@router.get("/price-match/history/{product_id}")
def price_match_history(
    product_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return recent price-match decisions for one product."""
    return get_price_match_history(db, product_id, limit)