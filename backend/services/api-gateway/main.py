import sys
import os
import logging
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from config import settings
from db import get_db, close_db, init_indexes
from redis_client import get_redis, close_redis
from auth import init_firebase

from routers import auth, workspaces, users
from middleware.rate_limiter import RateLimiterMiddleware

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.environment == "development"
        else structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting api-gateway", environment=settings.environment)
    try:
        init_firebase(settings.firebase_project_id)
        logger.info("Firebase initialized")
    except Exception as e:
        logger.warning("Firebase init failed", error=str(e))

    try:
        db = await get_db()
        await init_indexes(db)
        logger.info("MongoDB connected and indexes created")
    except Exception as e:
        logger.warning("MongoDB connection failed at startup", error=str(e))

    try:
        await get_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning("Redis connection failed at startup", error=str(e))

    yield

    # Shutdown
    await close_db()
    await close_redis()
    logger.info("api-gateway shutdown complete")


app = FastAPI(
    title="DevCollab API Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.environment == "development" else None,
    redoc_url="/api/redoc" if settings.environment == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimiterMiddleware)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    request.state.request_id = request_id

    if settings.environment == "production":
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            span.set_attribute("request_id", request_id)
        except Exception:
            pass

    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request completed",
        status_code=response.status_code,
    )
    return response


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    checks: dict = {}
    overall = True

    try:
        db = await get_db()
        await db.command("ping")
        checks["mongodb"] = "ok"
    except Exception as e:
        checks["mongodb"] = f"error: {e}"
        overall = False

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        overall = False

    status_code = 200 if overall else 503
    return JSONResponse(
        content={"status": "ready" if overall else "not_ready", "checks": checks},
        status_code=status_code,
    )
