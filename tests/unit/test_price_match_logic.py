"""Unit tests for evaluate_price_match — pure logic, no DB, no mocking."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from price_match import MAX_DISCOUNT_FRACTION, evaluate_price_match


class TestEvaluatePriceMatch:
    def test_competitor_price_zero_rejected(self):
        result = evaluate_price_match(store_price=1000.0, competitor_price=0)
        assert result.approved is False
        assert result.final_price == 1000.0

    def test_competitor_price_negative_rejected(self):
        result = evaluate_price_match(store_price=1000.0, competitor_price=-50.0)
        assert result.approved is False

    def test_competitor_price_equal_to_store_price_rejected(self):
        result = evaluate_price_match(store_price=1000.0, competitor_price=1000.0)
        assert result.approved is False
        assert result.discount_applied == 0.0

    def test_competitor_price_higher_than_store_price_rejected(self):
        result = evaluate_price_match(store_price=1000.0, competitor_price=1200.0)
        assert result.approved is False
        assert result.final_price == 1000.0

    def test_small_discount_matched_in_full(self):
        # 5% discount, well within the 15% cap.
        result = evaluate_price_match(store_price=1000.0, competitor_price=950.0)
        assert result.approved is True
        assert result.final_price == 950.0
        assert result.discount_applied == 50.0

    def test_discount_exactly_at_cap_matched_in_full(self):
        # Exactly 15% off - boundary case, should match in full (uses <=).
        result = evaluate_price_match(store_price=1000.0, competitor_price=850.0)
        assert result.approved is True
        assert result.final_price == 850.0
        assert result.discount_applied == 150.0

    def test_discount_beyond_cap_is_capped(self):
        # Competitor wants 40% off - only 15% allowed, so final price is capped.
        result = evaluate_price_match(store_price=1000.0, competitor_price=600.0)
        assert result.approved is True
        assert result.discount_applied == 150.0
        assert result.final_price == 850.0
        assert result.competitor_price == 600.0  # original request preserved

    def test_capped_discount_uses_max_discount_fraction_constant(self):
        store_price = 2000.0
        expected_discount = round(store_price * MAX_DISCOUNT_FRACTION, 2)
        result = evaluate_price_match(store_price=store_price, competitor_price=1.0)
        assert result.discount_applied == expected_discount
        assert result.final_price == round(store_price - expected_discount, 2)

    def test_result_reason_present_for_all_outcomes(self):
        for store_price, competitor_price in [
            (1000.0, 0), (1000.0, -1.0), (1000.0, 1000.0),
            (1000.0, 950.0), (1000.0, 600.0),
        ]:
            result = evaluate_price_match(store_price, competitor_price)
            assert isinstance(result.reason, str) and len(result.reason) > 0
