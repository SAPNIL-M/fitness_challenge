import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import init_db

load_dotenv()

PORT: int = int(os.getenv("PORT", "8000"))

ALLOWED_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
]

# ─── Routers ────────────────────────────────────────────────
# Uncomment each import as we create the files
# from routers import users, activities
# ────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages application startup and shutdown lifecycle.

    Startup:
        - Initializes the SQLite database and creates tables
          if they do not already exist.

    Shutdown:
        - Placeholder for any future cleanup tasks
          (closing connection pools, flushing caches, etc.)
    """
    init_db()
    print("✓ Database initialized")
    yield
    print("✓ Application shut down cleanly")


app = FastAPI(
    title="Fitness Challenge API",
    description=(
        "A gamified fitness tracking API that normalizes diverse "
        "physical activities into a unified points system, enabling "
        "fair competition across a global leaderboard."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ─── Middleware ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────────────────


# ─── Routers ────────────────────────────────────────────────
# Uncomment each line as we create the files
# app.include_router(users.router,      prefix="/api/users",      tags=["Users"])
# app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])
# ────────────────────────────────────────────────────────────


# ─── Global Exception Handler ───────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for any unhandled exceptions.

    Prevents raw stack traces from leaking to the client.
    Returns a clean, consistent JSON error response instead.
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again.",
        },
    )

# ────────────────────────────────────────────────────────────


# ─── Core Endpoints ─────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Used to verify the API is reachable and running.
    In production this would also check database connectivity.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
    }

# ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
    )