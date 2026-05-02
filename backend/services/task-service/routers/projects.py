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

from models.project import ProjectCreate, ProjectUpdate

router = APIRouter()


def _doc_to_response(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("/{workspace_id}")
async def list_projects(
    workspace_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    redis = await get_redis()
    cache = CacheService(redis)
    cache_key = f"projects:{workspace_id}"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    db = await get_db()
    cursor = db["projects"].find({"workspace_id": workspace_id, "active": True}).sort("name", 1)
    projects = []
    async for doc in cursor:
        proj = _doc_to_response(doc)
        proj["sprint_count"] = await db["sprints"].count_documents({"project_id": proj["id"]})
        proj["task_count"] = await db["tasks"].count_documents({"project_id": proj["id"]})
        projects.append(proj)

    await cache.set_json(cache_key, projects, ttl=120)
    return projects


@router.post("/{workspace_id}", status_code=201)
async def create_project(
    workspace_id: str,
    body: ProjectCreate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    now = datetime.utcnow()
    doc = {
        **body.model_dump(),
        "workspace_id": workspace_id,
        "active": True,
        "created_by": uid,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["projects"].insert_one(doc)
    created = await db["projects"].find_one({"_id": result.inserted_id})

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(f"projects:{workspace_id}")
    return _doc_to_response(created)


@router.get("/{workspace_id}/{project_id}")
async def get_project(
    workspace_id: str,
    project_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    doc = await db["projects"].find_one({"_id": oid, "workspace_id": workspace_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    proj = _doc_to_response(doc)
    proj["sprint_count"] = await db["sprints"].count_documents({"project_id": project_id})
    proj["task_count"] = await db["tasks"].count_documents({"project_id": project_id})
    return proj


@router.put("/{workspace_id}/{project_id}")
async def update_project(
    workspace_id: str,
    project_id: str,
    body: ProjectUpdate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    existing = await db["projects"].find_one({"_id": oid, "workspace_id": workspace_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.utcnow()
    await db["projects"].update_one({"_id": oid}, {"$set": updates})
    updated = await db["projects"].find_one({"_id": oid})

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(f"projects:{workspace_id}")
    return _doc_to_response(updated)


@router.delete("/{workspace_id}/{project_id}", status_code=204)
async def delete_project(
    workspace_id: str,
    project_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    result = await db["projects"].update_one(
        {"_id": oid, "workspace_id": workspace_id},
        {"$set": {"active": False, "updated_at": datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(f"projects:{workspace_id}")
