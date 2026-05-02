import sys
import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from config import settings
from db import get_db, close_db, init_indexes
from redis_client import get_redis, close_redis
from auth import init_firebase

from routers import tasks, sprints, projects

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
    logger.info("Starting task-service", environment=settings.environment)

    try:
        init_firebase(settings.firebase_project_id)
    except Exception as e:
        logger.warning("Firebase init failed", error=str(e))

    try:
        db = await get_db()
        await init_indexes(db)
        logger.info("MongoDB connected")
    except Exception as e:
        logger.warning("MongoDB connection failed", error=str(e))

    try:
        await get_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning("Redis connection failed", error=str(e))

    yield

    await close_db()
    await close_redis()
    logger.info("task-service shutdown complete")


app = FastAPI(
    title="DevCollab Task Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.environment == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(sprints.router, prefix="/api/v1/sprints", tags=["sprints"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])


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
