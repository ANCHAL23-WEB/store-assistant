"""Price-match evaluation and logging logic."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

# Maximum discount the store is willing to apply, as a fraction of the store price.
# Keeps the feature from approving unlimited/unrealistic matches.
MAX_DISCOUNT_FRACTION = 0.15


@dataclass
class PriceMatchResult:
    """The outcome of evaluating a price-match request."""

    approved: bool
    store_price: float
    competitor_price: float
    discount_applied: float
    final_price: float
    reason: str


def evaluate_price_match(store_price: float, competitor_price: float) -> PriceMatchResult:
    """Decide whether a competitor price can be matched, and by how much.

    Rules:
    - If competitor price >= store price, there's nothing to match.
    - If matching the competitor price would require a discount bigger than
      MAX_DISCOUNT_FRACTION of the store price, approve only the maximum
      allowed discount instead of the full match.
    - Otherwise, approve matching the competitor price exactly.
    """
    if competitor_price <= 0:
        return PriceMatchResult(
            approved=False,
            store_price=store_price,
            competitor_price=competitor_price,
            discount_applied=0.0,
            final_price=store_price,
            reason="Competitor price must be greater than zero.",
        )

    if competitor_price >= store_price:
        return PriceMatchResult(
            approved=False,
            store_price=store_price,
            competitor_price=competitor_price,
            discount_applied=0.0,
            final_price=store_price,
            reason="Our price is already equal to or lower than the competitor's price.",
        )

    requested_discount = store_price - competitor_price
    max_allowed_discount = round(store_price * MAX_DISCOUNT_FRACTION, 2)

    if requested_discount <= max_allowed_discount:
        return PriceMatchResult(
            approved=True,
            store_price=store_price,
            competitor_price=competitor_price,
            discount_applied=requested_discount,
            final_price=competitor_price,
            reason="Competitor price matched in full.",
        )

    capped_final_price = round(store_price - max_allowed_discount, 2)
    return PriceMatchResult(
        approved=True,
        store_price=store_price,
        competitor_price=competitor_price,
        discount_applied=max_allowed_discount,
        final_price=capped_final_price,
        reason=(
            f"Full match would exceed our maximum allowed discount of "
            f"{MAX_DISCOUNT_FRACTION:.0%}. Applied the maximum discount instead."
        ),
    )


def log_price_match_event(
    db: Session,
    *,
    product_id: int,
    store_id: int,
    competitor_price: float,
    source: str,
    discount_applied: float,
) -> None:
    """Persist one price-match decision for later reporting."""
    db.execute(
        text("""
            INSERT INTO price_match_events
                (product_id, store_id, competitor_price, source, discount_applied)
            VALUES
                (:product_id, :store_id, :competitor_price, :source, :discount_applied)
        """),
        {
            "product_id": product_id,
            "store_id": store_id,
            "competitor_price": competitor_price,
            "source": source,
            "discount_applied": discount_applied,
        },
    )
    db.commit()


def get_price_match_history(db: Session, product_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """Return the most recent price-match events for one product."""
    rows = db.execute(
        text("""
            SELECT event_id, store_id, competitor_price, source, discount_applied, timestamp
            FROM price_match_events
            WHERE product_id = :product_id
            ORDER BY timestamp DESC, event_id DESC
            LIMIT :limit
        """),
        {"product_id": product_id, "limit": limit},
    ).all()
    return [dict(row._mapping) for row in rows]