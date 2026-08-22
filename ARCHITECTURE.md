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