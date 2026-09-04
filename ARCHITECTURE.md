# ARCHITECTURE

## Layers
- Frontend (Next.js 15.5.9, no Turbopack): pages in /app, calls backend via fetch to FastAPI routes
- Backend (FastAPI): routes in backend/, handles search, product, price-match, usage logging
- Database (PostgreSQL): store_assistant DB, accessed only from backend, never directly from frontend
- Search layer: backend/retrieval/search.py — sentence-transformers embeds query → FAISS IndexFlatL2 finds nearest products → MAX_DISTANCE=1.2 filters bad matches
- Analytics: separate Streamlit app (dashboard/app.py), reads DB directly via pandas, independent from main app

## API Flow
1. User action (scan/speak/type/random-keyword) → frontend gets a text query
2. Frontend calls backend search endpoint with query
3. Backend embeds query, runs FAISS search, filters by MAX_DISTANCE
4. Backend logs event to usage_events (input type: camera/voice/browse)
5. Backend returns results → frontend renders

## Price Match Flow
1. User submits competitor price on /product/[id]
2. Backend checks against 15% max discount floor
3. Decision logged to price_match_events
4. Result returned to frontend

> **Note:** The 15% max discount floor is a simulated business rule for demonstration purposes — not derived from live competitor pricing APIs. It represents a plausible upper bound a retailer might enforce to prevent unsustainable discounting.


## Analytics Flow

1. Streamlit dashboard queries usage_events + price_match_events directly via pandas
2. Renders charts: top products, top searches, input method breakdown, searches over time, zero-result searches
3. Used for business decisions (what customers search for, what's not in stock, what features they want)

## Rules
- Frontend never talks to DB directly — always through backend API
- All new backend routes go in backend/ (not root)
- Reusable logic (search, price-match) stays in separate modules, not duplicated in route files
- AI/search logic isolated in backend/retrieval/ — swappable without touching routes
- Dashboard uses plain Python charts (Streamlit/matplotlib), not Tableau-style tools

  
## Security

- **Environment variables:** Database credentials and secrets are stored in `.env` files (excluded from git via `.gitignore`), never hardcoded in source.
- **SQL injection protection:** All database queries use parameterized statements via `psycopg2` (e.g. `cursor.execute(query, (params,))`), never raw string interpolation — confirmed across `search.py`, `price_match.py`, and all route handlers.
- **Input validation:** FastAPI's Pydantic models validate and type-check all incoming request bodies before processing.
- **CORS (current limitation):** CORS is currently open (`allow_origins=["*"]`) to simplify local frontend/backend integration during development. This should be restricted to the deployed frontend's specific origin before any public/production use — noted as a to-do for the deployment phase.
