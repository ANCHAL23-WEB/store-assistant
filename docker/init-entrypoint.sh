#!/bin/sh
set -e

echo "Checking product catalog..."
PRODUCT_COUNT=$(python -c "
import psycopg2, os
from dotenv import load_dotenv
load_dotenv('/app/.env')
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM products')
print(cur.fetchone()[0])
conn.close()
")

if [ "$PRODUCT_COUNT" -eq "0" ]; then
  echo "No products found — seeding catalog..."
  python db/seed_data.py
  echo "Seed changes product content — rebuilding FAISS index..."
  python backend/retrieval/embed_products.py
elif [ ! -f backend/retrieval/product_index.faiss ]; then
  echo "Catalog already seeded ($PRODUCT_COUNT products), but no FAISS index found — building..."
  python backend/retrieval/embed_products.py
else
  echo "Catalog already seeded ($PRODUCT_COUNT products) and FAISS index exists — skipping both."
fi

echo "Init complete."