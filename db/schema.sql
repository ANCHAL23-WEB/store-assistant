-- Retail Store Assistant database schema (PostgreSQL)

CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    parent_category_id INTEGER REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    brand TEXT NOT NULL,
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    colors TEXT[] NOT NULL DEFAULT '{}',
    specs JSONB NOT NULL DEFAULT '{}'::jsonb,
    image_url TEXT,
    barcode TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS stores (
    store_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    city TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    store_id INTEGER NOT NULL REFERENCES stores(store_id),
    stock_qty INTEGER NOT NULL CHECK (stock_qty >= 0),
    restock_eta_days INTEGER CHECK (restock_eta_days >= 0),
    PRIMARY KEY (product_id, store_id)
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    store_id INTEGER NOT NULL REFERENCES stores(store_id),
    role TEXT NOT NULL CHECK (role IN ('staff', 'admin'))
);

CREATE TABLE IF NOT EXISTS usage_events (
    event_id SERIAL PRIMARY KEY,
    employee_id INTEGER DEFAULT 1 REFERENCES employees(employee_id),
    product_id INTEGER REFERENCES products(product_id),
    input_type TEXT NOT NULL CHECK (input_type IN ('camera', 'voice', 'browse')),
    query_text TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS price_match_events (
    event_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    store_id INTEGER NOT NULL REFERENCES stores(store_id),
    competitor_price NUMERIC(12, 2) NOT NULL CHECK (competitor_price >= 0),
    source TEXT NOT NULL,
    discount_applied NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (discount_applied >= 0),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Helpful indexes for common assistant lookups.
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_inventory_store_id ON inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_employee_id ON usage_events(employee_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_input_type ON usage_events(input_type);
CREATE INDEX IF NOT EXISTS idx_usage_events_timestamp ON usage_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_price_match_events_product_id ON price_match_events(product_id);
