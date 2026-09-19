# Store Assistant — Semantic Retail Search & Analytics Platform
**Live Demo:** [store-assistant-plum.vercel.app](https://store-assistant-plum.vercel.app)

A full-stack retail electronics store assistant designed for non-technical users. Customers and employees can search a 5,000-product catalog using natural language, barcode scanning, or voice — even when they don't know exact product names or specs. Built as a data analyst / technical analyst portfolio project 

> **Note:** The 5,000-product catalog is synthetically generated (via Faker + a seed script) for demonstration purposes — not scraped or real store inventory.

## Features

- **Multi-modal search** — scan a barcode, speak a query, or type — all routes to the same intelligent search engine
- **Feature-based search** — type loose, imprecise keywords (e.g. "5g 8gb ram" or "waterproof speaker") and get relevant matches by product specs, not just exact names, powered by sentence embeddings + FAISS
- **Price-match tool** — customers can request a competitor price match; backend validates against a 15% max discount floor and logs the decision
- **Analytics dashboard** — a Streamlit dashboard tracks top searched/purchased products, input method usage (scan/speak/type), and zero-result searches, to support real business decisions
- **Grandmother-friendly UI** — large buttons, minimal text, built for non-technical users

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


### Business Insight Example

Out of 26 tracked searches, "phone" and "laptop" were the most searched terms (5 each), followed by "washing machine" (4) — indicating strong customer interest in electronics and appliances. Zero-result searches were 0% in this sample, suggesting the semantic search successfully matches customer queries to catalog items even with varied phrasing.


## Search Evaluation

To validate the retrieval approach, three search methods were benchmarked against 40 labeled test queries (relevance defined by rule-based keyword matching against product specs — see `eval/test_queries.json` for methodology).

| Method | Precision@5 | Recall@5 | MRR | Avg Latency |
|---|---|---|---|---|
| Keyword Search | 0.96 | 0.031 | 0.975 | 3.1 ms |
| TF-IDF | 0.90 | 0.029 | 0.90 | 1.3 ms |
| FAISS + Embeddings | 0.85 | 0.024 | 0.87 | 55.4 ms |

**Note:** Keyword and TF-IDF score higher here because the ground-truth labels were themselves keyword-based, which favors exact-match methods. In practice, FAISS + embeddings is more robust to loose or imprecise phrasing (e.g. "phone with good camera" vs. exact spec terms), which keyword/TF-IDF methods cannot handle — a strength this keyword-based evaluation doesn't fully capture. Low recall across all methods reflects a large candidate pool per query relative to top-5 retrieval depth.

Run the evaluation yourself: `python -m eval.evaluate_search` (from project root).


## Performance & Scalability

Latency was benchmarked at increasing catalog sizes to test how each stage of the search pipeline scales.

| Catalog Size | Query Embedding | FAISS Search | DB Fetch | Total (end-to-end) |
|---|---|---|---|---|
| 5,000 | 13.16 ms | 0.70 ms | 47.70 ms | 61.57 ms |
| 10,000 | 10.92 ms | 0.66 ms | 38.46 ms | 50.04 ms |
| 50,000 | 27.37 ms | 13.46 ms | 69.65 ms | 110.47 ms |

**Findings:** DB fetch dominates latency at smaller scales (up to 77%), while FAISS search time grows roughly linearly with catalog size (expected for `IndexFlatL2`, which does a brute-force scan). Even at 50,000 products — 10x the current catalog — end-to-end search stays under 120ms, well within acceptable UX limits for a search-as-you-type experience.

Run this benchmark yourself: `python -m eval.benchmark_performance`

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15.5.9, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL 17 |
| Search | fastembed (`all-MiniLM-L6-v2`, ONNX runtime) + FAISS |
| OCR | pytesseract + Pillow |
| Analytics | Streamlit + pandas |
| Barcode | @zxing/browser |
| Voice | Web Speech API |

## Architecture

Frontend never talks to the database directly — all requests go through the FastAPI backend. Search logic (embedding + FAISS lookup) is isolated in its own module so it can be swapped or upgraded independently. See `ARCHITECTURE.md` for details.

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 17
- Tesseract OCR (for image-based search)

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
