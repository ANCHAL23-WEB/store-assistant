# CODING RULES

## Naming
- React components: PascalCase (e.g. ProductCard.tsx)
- Functions/variables: camelCase
- DB tables/columns: snake_case (e.g. usage_events, price_match_events)
- Files: page.tsx for Next.js pages (never page.tsk or other typos — confirm extension)

## Folder Structure
- Frontend pages: /app/<route>/page.tsx
- Frontend components: /app/components/
- Backend routes: backend/routes/
- Backend logic (search, price-match): backend/retrieval/, backend/services/
- DB migrations: numbered files e.g. 002_add_barcode.sql

## Rules
- No partial file edits from AI — always full file replacement to avoid copy-paste bugs
- No silent catch blocks — always setStatus("error") or equivalent so failures show in UI
- One file, one destination path per step — never generate multiple files at once
- Reuse existing components/utilities before creating new ones
- Keep frontend/backend/DB/AI logic strictly separated (see ARCHITECTURE.md)
- Never run Turbopack for this project's frontend — caused persistent, hard-to-debug dev-server errors. Stick to next@15.5.9 stable.
- Always run npm/python commands from the correct folder (frontend/ or backend/) — confirm with current directory before running.

## API Response Format
- JSON only
- Errors return { "error": "message" } with appropriate HTTP status code

## Styling
- Tailwind CSS only, no separate CSS files
- Large icons, minimal text, few buttons ("grandmother-friendly" design)

## Analytics/Charts
- Use Python (Streamlit/matplotlib) for all dashboards — not Tableau. Simple charts preferred over polished/complex visuals.