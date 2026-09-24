# Store Assistant - Semantic Retail Search & Analytics Platform
**Live Demo:** [store-assistant-plum.vercel.app](https://store-assistant-plum.vercel.app)

A full-stack retail electronics store assistant designed for non-technical users. Customers and employees can search a 5,000-product catalog using natural language, barcode scanning, or voice - even when they don't know exact product names or specs. Built as a data analyst / technical analyst portfolio project 

> **Note:** The 5,000-product catalog is synthetically generated (via Faker + a seed script) for demonstration purposes - not scraped or real store inventory.

## Features

- **Multi-modal search** - scan a barcode for exact catalog lookup, or speak/type a query for semantic search powered by sentence embeddings + FAISS
- **Feature-based search** - type loose, imprecise keywords (e.g. "5g 8gb ram" or "waterproof speaker") and get relevant matches by product specs, not just exact names, powered by sentence embeddings + FAISS
- **Price-match tool** - customers can request a competitor price match; backend validates against a 15% max discount floor and logs the decision
- **Analytics dashboard** - a Streamlit dashboard tracks searched products, search input method, search volume over time, and zero-result queries, to support real business decisions
- **Simple, low-friction UI** - large buttons and minimal text, aimed at reducing typing for in-store staff and customers (not formally usability-tested against accessibility standards)

 ## Screenshots

| Homepage | Search & Results |
|---|---|
| ![Homepage](01-homepage.jpeg) | ![Search Results](02-search-results.jpeg) |
| Scan / Voice | Analytics Dashboard |
|---|---|
| ![Scan](03-scan-voice.jpeg) | ![Dashboard](04-dashboard-top.jpeg) |

**Barcode Scan:**

![Barcode Scan](03-bar-code.jpeg)

**Dashboard (more views):**

![Dashboard Charts](04-dashboard-charts.jpeg)


## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 17


### 1. Clone and install
```bash
git clone https://github.com/ANCHAL23-WEB/store-assistant.git
cd store-assistant

# Backend
cd backend
pip install -r requirements.txt --break-system-packages

# Frontend
cd ../frontend
npm install
```

### 2. Set up the database
Create a `.env` file in both the project root and `backend/` with:


Copy the example env files and fill in your own PostgreSQL credentials:
Each `.env` needs:


### 3. Create the database

Make sure PostgreSQL is running locally, then create the database:

```bash
createdb store_assistant
```

### 4. Run the schema and migrations

```bash
psql -d store_assistant -f db/schema.sql
psql -d store_assistant -f db/migrations/001_create_price_match_events.sql
psql -d store_assistant -f db/migrations/002_add_barcode.sql
```

### 5. Seed the catalog

```bash
cd backend
python ../db/seed_data.py
```

This populates the 5,000-product synthetic catalog.

### 6. Build the search index

```bash
python retrieval/embed_products.py
```

This generates `product_index.faiss` and `product_ids.json` from the seeded catalog. Re-run this any time the catalog changes.

### 7. Run the backend

```bash
python -m uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`.

### 8. Run the frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

Frontend runs at `http://localhost:3000`.

### 9. (Optional) Run the analytics dashboard

In a new terminal:

```bash
cd dashboard
pip install -r requirements.txt --break-system-packages
python -m streamlit run app.py
```

Dashboard runs at `http://localhost:8501`.

### Alternative: run everything with Docker

Steps 3-9 can be skipped by using Docker Compose instead, which handles the database, backend, and frontend in one command:

```bash
docker compose up --build
```

Note: the containers auto-seed the catalog and build the search index on first run via an init service - no manual steps needed. Subsequent runs skip re-seeding if the catalog already exists.

To also run the analytics dashboard:

```bash
docker compose --profile full up --build
```

### Running tests

```bash
cd backend
python -m pytest ../tests/unit -v
```

Integration tests require a real local database and are not run in CI - see `tests/integration/` for local smoke tests against a live database.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15.5.9, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL 17 |
| Search | fastembed (`all-MiniLM-L6-v2`, ONNX runtime) + FAISS |
| Analytics | Streamlit + pandas |
| Barcode | @zxing/browser |
| Voice | Web Speech API |

## Architecture

Frontend never talks to the database directly - all requests go through the FastAPI backend. Search logic (embedding + FAISS lookup) is isolated in its own module so it can be swapped or upgraded independently. See `ARCHITECTURE.md` for details.

### Search index freshness

The FAISS search index is built offline (`python backend/retrieval/embed_products.py`) and stored as a binary file, so it can silently fall out of sync if the catalog changes without a rebuild. `GET /health/index` compares the live product count against the count recorded at index-build time and reports `"fresh"` or `"stale"` - rebuild the index if it reports stale.

## Search Evaluation

To validate the retrieval approach, three search methods were benchmarked against 30 manually judged test queries spanning exact-spec, paraphrased, vague/category, price-constrained, and no-result cases (see `eval/relevance_judgments.jsonl` - each query's relevant product IDs were determined by manually inspecting live search results and applying a stated relevance rule per query).

| Method | Precision@5 | Recall@5 | MRR |
|---|---|---|---|
| Keyword Search | 0.017 | 0.008 | 0.019 |
| TF-IDF | 0.033 | 0.029 | 0.029 |
| FAISS + Embeddings | **0.625** | **0.499** | **0.783** |

**Findings:** FAISS + embeddings substantially outperforms both keyword and TF-IDF search on manually judged relevance - keyword and TF-IDF methods essentially fail to surface relevant products for natural-language queries, while semantic search returns relevant results in the top 5 for the majority of queries. Notable exceptions found during judging: a few queries mixing product categories (e.g. "phone with good camera") return the wrong category entirely - tracked as a known limitation. Price constraints such as "under 30,000" are supported through post-retrieval filtering; more complex constraints and category disambiguation remain known limitations.

Run the evaluation yourself: `python -m eval.evaluate_search` (from project root).


## Performance & Scalability

Latency was benchmarked on the current 5,000-product catalog to break down where time is spent in the search pipeline.

| Catalog Size | Query Embedding | FAISS Search | DB Fetch | Total (end-to-end) |
|---|---|---|---|---|
| 5,000 | 43.52 ms | 1.18 ms | 832.01 ms | 876.71 ms |

**Findings:** DB fetch dominates latency (94.9% of total time) - each call opens a fresh psycopg2 connection with no pooling, which is the main cost, not the query itself. FAISS search is fast (1.18 ms, `IndexFlatL2` brute-force scan over 5,000 vectors). Query embedding (FastEmbed) takes 43.52 ms. At larger catalog sizes, FAISS search time would grow roughly linearly (expected for `IndexFlatL2`); DB fetch latency is a connection-pooling problem, not a query-optimization one, and would need to be addressed before this scales.

Run this benchmark yourself: `python -m eval.benchmark_performance`

## Business Insight Example

Out of 26 tracked searches, "phone" and "laptop" were the most searched terms (5 each), followed by "washing machine" (4) - indicating strong customer interest in electronics and appliances. Zero-result searches were 0% in this sample, suggesting the semantic search successfully matches customer queries to catalog items even with varied phrasing.


## Known Limitations

This is a portfolio/demo project, not a production system. Some known gaps,
called out here rather than hidden:

- **Synthetic catalog**: the 5,000-product catalog is synthetically
  generated, not real inventory data.
- **CORS**: restricted via a `CORS_ORIGINS` environment variable, locked to the deployed Vercel origin in production.
- **No authentication**: there is no user login or role-based access control
  - anyone with the API URL can call every endpoint.
- **Evaluation scale**: the search evaluation framework (Precision@5,
  Recall@5, MRR) was run on 30 manually-judged queries, not a large-scale
  benchmark - see the Search Evaluation section for the full methodology
  and numbers.
- **Free-tier hosting**: the live demo runs on Render's free tier, which can
  take up to a minute to wake up after periods of inactivity (cold start).
- **Single-region deployment**: no multi-region failover or load balancing;
  this is a single-instance demo deployment.








