# PROJECT CONTEXT

## Stack
- Frontend: Next.js 15.5.9, React 19, TypeScript, Tailwind CSS (Turbopack disabled — caused persistent dev-server bugs)
- Backend: FastAPI (Python)
- DB: PostgreSQL 17 (store_assistant)
- Search: sentence-transformers (all-MiniLM-L6-v2) + FAISS (IndexFlatL2)
- OCR: pytesseract + Pillow
- Analytics: Streamlit (dashboard/app.py) — Python charts only, no Tableau
- Barcode: @zxing/browser
- Voice: browser Web Speech API (Chrome only)

## App Flow
Home (3 buttons: Scan / Speak / Type)
- /scan → barcode via @zxing/browser + manual fallback
- /speak → Web Speech API → redirects to /search?q=
- /search → reads ?q= param, auto-search, "not available" on zero results
- /product/[id] → features, per-store stock, delivery est, price-match form

## Search
- Feature-based/random-keyword search works via flatten_specs() feeding specs into FAISS embeddings
- Users/employees can type loose keywords (e.g. "5g 8gb ram", "waterproof speaker") and get matches by spec, not just name
- MAX_DISTANCE = 1.2 relevance threshold

## Database
- 5,000 synthetic electronics products, 17 categories
- 5 Indian store locations
- 20 employees
- Tables incl. usage_events, price_match_events
- barcode column added via migration 002_add_barcode.sql

## Env files
- .env in project root (seed_data.py)
- .env in backend/ (FastAPI)
- DATABASE_URL=postgresql://postgres:CHIA23@localhost:5432/store_assistant

## Completed Features
- Scan/Speak/Type search flows
- Product detail page
- Price-match logic (15% max discount floor, logs to price_match_events)
- Usage logging by input type
- Streamlit analytics dashboard (top products, top searches, input method breakdown)
- Feature-based/random-keyword search
- Category images via Unsplash (CATEGORY_IMAGES dict in seed_data.py)

## Dropped from scope (per feedback)
- Hindi/English toggle
- Multi-business branding

## Status
Feedback round complete. Finalizing: README, git commits.