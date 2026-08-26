# Store Assistant — AI-Powered Retail Search & Analytics

A full-stack retail electronics store assistant designed for non-technical users. Customers and employees can search a 5,000-product catalog using natural language, barcode scanning, or voice — even when they don't know exact product names or specs. Built as a data analyst / technical analyst portfolio project 

> **Note:** The 5,000-product catalog is synthetically generated (via Faker + a seed script) for demonstration purposes — not scraped or real store inventory.

## Features

- **Multi-modal search** — scan a barcode, speak a query, or type — all routes to the same intelligent search engine
- **Feature-based search** — type loose, imprecise keywords (e.g. "5g 8gb ram" or "waterproof speaker") and get relevant matches by product specs, not just exact names, powered by sentence embeddings + FAISS
- **Price-match tool** — customers can request a competitor price match; backend validates against a 15% max discount floor and logs the decision
- **Analytics dashboard** — a Streamlit dashboard tracks top searched/purchased products, input method usage (scan/speak/type), and zero-result searches, to support real business decisions
- **Grandmother-friendly UI** — large buttons, minimal text, built for non-technical users

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15.5.9, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL 17 |
| Search | sentence-transformers (`all-MiniLM-L6-v2`) + FAISS |
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
