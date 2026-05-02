import sys
import os
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from auth import verify_firebase_token
from db import get_db
from redis_client import get_redis, CacheService

from models.sprint import SprintCreate, SprintUpdate, SprintStatus

router = APIRouter()


def _sprint_cache_key(workspace_id: str, project_id: str) -> str:
    return f"sprints:{workspace_id}:{project_id}"


def _doc_to_response(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for key in ("workspace_id", "project_id"):
        if key in doc and doc[key]:
            doc[key] = str(doc[key])
    return doc


@router.get("/{workspace_id}/{project_id}")
async def list_sprints(
    workspace_id: str,
    project_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    redis = await get_redis()
    cache = CacheService(redis)
    cache_key = _sprint_cache_key(workspace_id, project_id)
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    db = await get_db()
    cursor = db["sprints"].find(
        {"workspace_id": workspace_id, "project_id": project_id}
    ).sort("created_at", -1)

    sprints = []
    async for doc in cursor:
        sp = _doc_to_response(doc)
        task_count = await db["tasks"].count_documents({"sprint_id": sp["id"]})
        completed = await db["tasks"].count_documents({"sprint_id": sp["id"], "status": "done"})
        sp["task_count"] = task_count
        sp["completed_task_count"] = completed
        sprints.append(sp)

    await cache.set_json(cache_key, sprints, ttl=120)
    return sprints


@router.post("/{workspace_id}/{project_id}", status_code=201)
async def create_sprint(
    workspace_id: str,
    project_id: str,
    body: SprintCreate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    now = datetime.utcnow()
    doc = {
        **body.model_dump(),
        "workspace_id": workspace_id,
        "project_id": project_id,
        "status": SprintStatus.planned.value,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["sprints"].insert_one(doc)
    created = await db["sprints"].find_one({"_id": result.inserted_id})

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(_sprint_cache_key(workspace_id, project_id))
    return _doc_to_response(created)


@router.patch("/{workspace_id}/{project_id}/{sprint_id}")
async def update_sprint(
    workspace_id: str,
    project_id: str,
    sprint_id: str,
    body: SprintUpdate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(sprint_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid sprint ID")

    existing = await db["sprints"].find_one(
        {"_id": oid, "workspace_id": workspace_id, "project_id": project_id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Sprint not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.utcnow()
    await db["sprints"].update_one({"_id": oid}, {"$set": updates})
    updated = await db["sprints"].find_one({"_id": oid})

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(_sprint_cache_key(workspace_id, project_id))
    return _doc_to_response(updated)


@router.post("/{workspace_id}/{project_id}/{sprint_id}/start")
async def start_sprint(
    workspace_id: str,
    project_id: str,
    sprint_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(sprint_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid sprint ID")

    existing = await db["sprints"].find_one(
        {"_id": oid, "workspace_id": workspace_id, "project_id": project_id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if existing["status"] != SprintStatus.planned.value:
        raise HTTPException(status_code=409, detail="Only planned sprints can be started")

    active_count = await db["sprints"].count_documents(
        {"workspace_id": workspace_id, "project_id": project_id, "status": SprintStatus.active.value}
    )
    if active_count > 0:
        raise HTTPException(status_code=409, detail="A sprint is already active in this project")

    now = datetime.utcnow()
    updates: dict = {"status": SprintStatus.active.value, "updated_at": now}
    if not existing.get("start_date"):
        updates["start_date"] = now

    await db["sprints"].update_one({"_id": oid}, {"$set": updates})
    updated = await db["sprints"].find_one({"_id": oid})

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(_sprint_cache_key(workspace_id, project_id))
    return _doc_to_response(updated)


@router.post("/{workspace_id}/{project_id}/{sprint_id}/complete")
async def complete_sprint(
    workspace_id: str,
    project_id: str,
    sprint_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(sprint_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid sprint ID")

    existing = await db["sprints"].find_one(
        {"_id": oid, "workspace_id": workspace_id, "project_id": project_id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if existing["status"] != SprintStatus.active.value:
        raise HTTPException(status_code=409, detail="Only active sprints can be completed")

    now = datetime.utcnow()
    updates: dict = {"status": SprintStatus.completed.value, "updated_at": now}
    if not existing.get("end_date"):
        updates["end_date"] = now

    # Move incomplete tasks to backlog
    await db["tasks"].update_many(
        {"sprint_id": sprint_id, "status": {"$ne": "done"}},
        {"$set": {"sprint_id": None, "status": "backlog", "updated_at": now}},
    )

    await db["sprints"].update_one({"_id": oid}, {"$set": updates})
    updated = await db["sprints"].find_one({"_id": oid})

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(_sprint_cache_key(workspace_id, project_id))
    return _doc_to_response(updated)
