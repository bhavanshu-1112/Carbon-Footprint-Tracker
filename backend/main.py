"""FastAPI application entry point for the Carbon Footprint Awareness Platform.

Configures middleware (CORS, security headers), manages the JSON-file
database lifecycle, and exposes REST endpoints for calculating, logging,
and managing carbon footprint records.
"""

import asyncio
import json
import logging
import os
import shutil
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from backend.calculator import calculate_footprint
from backend.gemini_service import close_async_client
from backend.schemas import CalculationRequest, CalculationResponse

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
SEED_DB_PATH = BASE_DIR / "database.json"

if os.environ.get("VERCEL"):
    DB_PATH = Path("/tmp/database.json")
    if not DB_PATH.exists() and SEED_DB_PATH.exists():
        try:
            shutil.copy(SEED_DB_PATH, DB_PATH)
        except OSError as exc:
            logger.warning("Failed to seed database to /tmp: %s", exc)
else:
    DB_PATH = SEED_DB_PATH

db_cache: dict | None = None
db_lock = asyncio.Lock()


def _read_db_file() -> dict:
    """Read and parse the JSON database from disk.

    Returns:
        Parsed database dictionary with ``emission_factors`` and ``logs`` keys.
        Returns a safe default if the file does not exist.
    """
    if not DB_PATH.exists():
        return {"emission_factors": {}, "logs": []}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_db_file_str(json_str: str) -> None:
    """Write a pre-serialized JSON string to the database file.

    Args:
        json_str: The JSON-encoded database content to persist.
    """
    with open(DB_PATH, "w", encoding="utf-8") as f:
        f.write(json_str)


async def load_db() -> dict:
    """Load the database with double-checked locking for async safety.

    Uses an in-memory cache to avoid redundant disk reads.  The cache is
    populated on first access and protected by an async lock to prevent
    race conditions during concurrent startup requests.

    Returns:
        The current database dictionary.
    """
    global db_cache
    if db_cache is not None:
        return db_cache
    async with db_lock:
        if db_cache is not None:
            return db_cache
        db_cache = await asyncio.to_thread(_read_db_file)
        return db_cache


async def save_db(data: dict) -> None:
    """Persist the database dictionary to disk and update the cache.

    Args:
        data: The full database dictionary to serialize and write.
    """
    global db_cache
    async with db_lock:
        db_cache = data
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        await asyncio.to_thread(_write_db_file_str, json_str)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — preloads DB and cleans up connections."""
    await load_db()
    yield
    # Clean up HTTPX async client connection pool on shutdown
    await close_async_client()


# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="Carbon Footprint Awareness Platform API",
    description="A secure and high-efficiency API to calculate, track, and offset carbon emissions.",
    version="1.0.0",
    lifespan=lifespan,
)


# Custom Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inject hardened security headers into every HTTP response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 http://localhost:5500 http://127.0.0.1:5500;"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Permissions-Policy"] = (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
    )
    return response


# Hardened CORS configuration
allowed_origins: list[str] = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins.extend(
        [org.strip() for org in allowed_origins_env.split(",") if org.strip()]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@app.get("/api/constants")
async def get_constants() -> dict:
    """Retrieve all current emission factors from the database."""
    db = await load_db()
    return db.get("emission_factors", {})


@app.post("/api/calculate", response_model=CalculationResponse, status_code=status.HTTP_201_CREATED)
async def calculate_and_log(payload: CalculationRequest) -> CalculationResponse:
    """Calculate carbon footprint, compare offsets, and save the transaction log.

    Utilizes Pydantic for validation and processes inputs asynchronously.
    """
    db = await load_db()
    factors = db.get("emission_factors", {})
    if not factors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Emission factors are missing in the database constants.",
        )

    # Perform calculation (async helper)
    result = await calculate_footprint(payload, factors)

    # Append result to DB logs
    db.setdefault("logs", []).append(result.model_dump())
    await save_db(db)

    return result


@app.get("/api/history", response_model=List[CalculationResponse])
async def get_history() -> list:
    """Retrieve all calculations saved in history."""
    db = await load_db()
    return db.get("logs", [])


@app.delete("/api/history/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log_entry(log_id: str) -> Response:
    """Delete a specific log entry from calculation history."""
    db = await load_db()
    logs = db.get("logs", [])

    # Filter out target log
    updated_logs = [log for log in logs if log.get("id") != log_id]

    if len(updated_logs) == len(logs):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculation with id {log_id} not found in history.",
        )

    db["logs"] = updated_logs
    await save_db(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/api/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_all_history() -> Response:
    """Clear all records from history."""
    db = await load_db()
    db["logs"] = []
    await save_db(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
