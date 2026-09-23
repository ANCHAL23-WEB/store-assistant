"""FastAPI application entry point for the retail store assistant."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import analytics, dashboard, health, price_match, products, search

app = FastAPI(title="Retail Store Assistant API")

# CORS origins: defaults to the deployed Vercel frontend; override via CORS_ORIGINS env var (comma-separated) for local/dev.
_cors_origins = os.getenv("CORS_ORIGINS", "https://store-assistant-plum.vercel.app").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(products.router)
app.include_router(analytics.router)
app.include_router(dashboard.router)
app.include_router(price_match.router)

