from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tide.api.routes import dashboard, health, metrics, sources, watchlist

app = FastAPI(title="TIDE API", version="0.1.0")

# SvelteKit dev server runs on :5173. SSR fetches go server-to-server, but enable CORS
# so client-side fetches (timeframe tabs, history endpoints) work in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(dashboard.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
