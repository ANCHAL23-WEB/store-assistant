# FEATURE LOG

## Format
Date | Change | Type (added/removed/refactor/dependency/architecture)

## Log
2026-08 | Home screen (Scan/Speak/Type buttons) | added
2026-08 | Barcode scan via @zxing/browser + manual fallback | added
2026-08 | Voice search via Web Speech API | added
2026-08 | Text search with auto-trigger on ?q= param | added
2026-08 | Feature-based/random-keyword search (via flatten_specs + FAISS) | added
2026-08 | Product detail page (features, stock, delivery) | added
2026-08 | Price-match endpoint (15% max discount floor) | added
2026-08 | Usage logging by input type | added
2026-08 | Streamlit analytics dashboard (top products, searches, input method breakdown) | added
2026-08 | barcode column | added (migration 002_add_barcode.sql)
2026-08 | MAX_DISTANCE=1.2 threshold tuning | refactor (search relevance fix)
2026-08 | Downgraded Next.js 16 (Turbopack) → Next.js 15.5.9 + React 19 | refactor (fixed persistent dev-server crashes)
2026-08 | Removed stray package-lock.json from Downloads (outside project) | refactor (root cause of routing bugs)
2026-08 | Category images via Unsplash (17 categories) | added

## Dropped
- Hindi/English toggle
- Multi-business branding