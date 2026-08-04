-- Add a barcode column for scan-based product lookup, and backfill existing
-- products with a synthetic but stable, unique barcode.

ALTER TABLE products ADD COLUMN IF NOT EXISTS barcode TEXT;

-- Backfill: build a 13-digit EAN-like code from the product_id so existing
-- rows all get a stable, unique value before the UNIQUE constraint is added.
UPDATE products
SET barcode = '890' || LPAD(product_id::text, 10, '0')
WHERE barcode IS NULL;

ALTER TABLE products ALTER COLUMN barcode SET NOT NULL;
ALTER TABLE products ADD CONSTRAINT products_barcode_unique UNIQUE (barcode);

CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
