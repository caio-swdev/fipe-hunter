"""
FIPE Hunter - Main Application Entry Point

FastAPI application for automated vehicle opportunity finder.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.middleware.session_middleware import SessionMiddleware
from app.limiter import limiter
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="FIPE Hunter API",
    description="Automated vehicle opportunity finder for Brazilian marketplaces",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(SessionMiddleware)

_cors_origins = ["http://localhost:3000", "http://localhost:3001"]
_frontend_url = os.getenv("FRONTEND_URL")
if _frontend_url:
    _cors_origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/api", tags=["root"])
def api_root():
    """API root endpoint."""
    return {
        "message": "FIPE Hunter API",
        "docs": "/docs",
        "health": "/health"
    }


from fipe_infra.database.models import Base
from fipe_infra.database.session import engine, DATABASE_URL

if "sqlite" in DATABASE_URL:

    Base.metadata.create_all(bind=engine)


from app.routes import listing_routes
from app.routes import dashboard_routes
from app.routes import fipe_routes
from app.routes import search_routes
from app.routes import proxy_routes
from app.routes import favorites_routes
from app.routes import admin_routes
from app.routes import auth_routes
from app.routes import scrape_routes

app.include_router(listing_routes.router, prefix="/api")
app.include_router(dashboard_routes.router, prefix="/api")
app.include_router(fipe_routes.router, prefix="/api/v1")
app.include_router(search_routes.router, prefix="/api")
app.include_router(proxy_routes.router, prefix="/api")
app.include_router(favorites_routes.router, prefix="/api")
app.include_router(auth_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(scrape_routes.router, prefix="/api")


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

_DIST = Path("/app/apps/vite-app/dist")
if _DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa(full_path: str = ""):
        return FileResponse(str(_DIST / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
