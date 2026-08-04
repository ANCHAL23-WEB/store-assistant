"""Product catalogue endpoints backed by PostgreSQL."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db

router = APIRouter()


def _product_row(product: Any) -> dict[str, Any]:
    """Convert a SQLAlchemy row to a JSON-compatible product dictionary."""
    return dict(product._mapping)


@router.get("/products/barcode/{barcode}")
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Look up one product by its scanned barcode, including inventory."""
    product_query = text("""
        SELECT p.product_id, p.name, p.category_id, c.name AS category, p.brand,
               p.price, p.colors, p.specs, p.image_url, p.barcode
        FROM products AS p
        JOIN categories AS c ON c.category_id = p.category_id
        WHERE p.barcode = :barcode
    """)
    product = db.execute(product_query, {"barcode": barcode}).first()
    if product is None:
        raise HTTPException(status_code=404, detail="No product found for that barcode")

    inventory_query = text("""
        SELECT i.store_id, s.name AS store_name, s.location, s.city,
               i.stock_qty, i.restock_eta_days
        FROM inventory AS i
        JOIN stores AS s ON s.store_id = i.store_id
        WHERE i.product_id = :product_id
        ORDER BY s.name
    """)
    result = _product_row(product)
    result["inventory"] = [
        dict(row._mapping)
        for row in db.execute(inventory_query, {"product_id": result["product_id"]}).all()
    ]
    return result


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Fetch one product and its inventory records across all stores."""
    product_query = text("""
        SELECT p.product_id, p.name, p.category_id, c.name AS category, p.brand,
               p.price, p.colors, p.specs, p.image_url
        FROM products AS p
        JOIN categories AS c ON c.category_id = p.category_id
        WHERE p.product_id = :product_id
    """)
    product = db.execute(product_query, {"product_id": product_id}).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    inventory_query = text("""
        SELECT i.store_id, s.name AS store_name, s.location, s.city,
               i.stock_qty, i.restock_eta_days
        FROM inventory AS i
        JOIN stores AS s ON s.store_id = i.store_id
        WHERE i.product_id = :product_id
        ORDER BY s.name
    """)
    result = _product_row(product)
    result["inventory"] = [
        dict(row._mapping)
        for row in db.execute(inventory_query, {"product_id": product_id}).all()
    ]
    return result


@router.get("/products")
def list_products(
    category: str | None = Query(None, min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List catalogue products, optionally filtered by a category name."""
    query = text("""
        SELECT p.product_id, p.name, p.category_id, c.name AS category, p.brand,
               p.price, p.colors, p.specs, p.image_url
        FROM products AS p
        JOIN categories AS c ON c.category_id = p.category_id
        WHERE (:category IS NULL OR LOWER(c.name) = LOWER(:category))
        ORDER BY p.product_id
        LIMIT :limit
    """)
    rows = db.execute(query, {"category": category, "limit": limit}).all()
    return [_product_row(row) for row in rows]