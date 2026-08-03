"""FastAPI application entry point for the retail store assistant."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import analytics, dashboard, health, ocr, products, search

app = FastAPI(title="Retail Store Assistant API")

# Open CORS is intentional during initial frontend integration. Restrict it before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(ocr.router)
app.include_router(products.router)
app.include_router(analytics.router)
app.include_router(dashboard.router)
