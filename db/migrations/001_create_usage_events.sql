-- Create the usage-event table for new databases and align existing databases
-- with nullable unmatched-product logging.
CREATE TABLE IF NOT EXISTS usage_events (
    event_id SERIAL PRIMARY KEY,
    employee_id INTEGER DEFAULT 1 REFERENCES employees(employee_id),
    product_id INTEGER REFERENCES products(product_id),
    input_type TEXT NOT NULL CHECK (input_type IN ('camera', 'voice', 'browse')),
    query_text TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE usage_events
    ALTER COLUMN employee_id DROP NOT NULL,
    ALTER COLUMN employee_id SET DEFAULT 1,
    ALTER COLUMN product_id DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_usage_events_input_type ON usage_events(input_type);
CREATE INDEX IF NOT EXISTS idx_usage_events_timestamp ON usage_events(timestamp DESC);
