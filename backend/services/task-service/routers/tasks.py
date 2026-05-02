import sys
import os
from datetime import datetime
from typing import Optional

import structlog
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from auth import verify_firebase_token
from db import get_db
from redis_client import get_redis, CacheService
from gcs_client import upload_file, get_signed_url
from pubsub_client import publish_task_event
from firestore_client import sync_task_to_firestore

from models.task import TaskCreate, TaskUpdate, TaskResponse, TaskComment, TaskAttachment

router = APIRouter()
logger = structlog.get_logger()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _task_cache_key(workspace_id: str, filters: str = "") -> str:
    return f"tasks:{workspace_id}:{filters}"


def _single_task_cache_key(task_id: str) -> str:
    return f"task:{task_id}"


def _doc_to_response(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for key in ("workspace_id", "project_id", "sprint_id", "reporter_id"):
        if key in doc and doc[key]:
            doc[key] = str(doc[key])
    doc["assignee_ids"] = [str(a) for a in doc.get("assignee_ids", [])]
    for comment in doc.get("comments", []):
        if "_id" in comment:
            comment["id"] = str(comment.pop("_id"))
    for attach in doc.get("attachments", []):
        if "_id" in attach:
            attach["id"] = str(attach.pop("_id"))
        if attach.get("gcs_path"):
            attach["signed_url"] = get_signed_url(attach["gcs_path"])
    return doc


@router.get("/{workspace_id}")
async def list_tasks(
    workspace_id: str,
    request: Request,
    sprint_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    token_data: dict = Depends(verify_firebase_token),
):
    filters_key = f"{sprint_id}:{status}:{assignee_id}:{priority}"
    cache_key = _task_cache_key(workspace_id, filters_key)

    redis = await get_redis()
    cache = CacheService(redis)
    cached = await cache.get_json(cache_key)
    if cached:
        logger.debug("tasks cache hit", workspace_id=workspace_id)
        return cached

    db = await get_db()
    query: dict = {"workspace_id": workspace_id}
    if sprint_id:
        query["sprint_id"] = sprint_id
    if status:
        query["status"] = status
    if assignee_id:
        query["assignee_ids"] = assignee_id
    if priority:
        query["priority"] = priority

    cursor = db["tasks"].find(query).sort("updated_at", -1).limit(200)
    tasks = []
    async for doc in cursor:
        tasks.append(_doc_to_response(doc))

    await cache.set_json(cache_key, tasks, ttl=60)
    return tasks


@router.post("/{workspace_id}", status_code=201)
async def create_task(
    workspace_id: str,
    body: TaskCreate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    now = datetime.utcnow()

    doc = {
        **body.model_dump(),
        "workspace_id": workspace_id,
        "reporter_id": uid,
        "comments": [],
        "attachments": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db["tasks"].insert_one(doc)
    created = await db["tasks"].find_one({"_id": result.inserted_id})
    response_doc = _doc_to_response(created)

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(*[k async for k in redis.scan_iter(f"tasks:{workspace_id}:*")])

    await publish_task_event("task.created", response_doc)
    return response_doc


@router.get("/{workspace_id}/{task_id}")
async def get_task(
    workspace_id: str,
    task_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    cache_key = _single_task_cache_key(task_id)
    redis = await get_redis()
    cache = CacheService(redis)
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    db = await get_db()
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    doc = await db["tasks"].find_one({"_id": oid, "workspace_id": workspace_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")

    response_doc = _doc_to_response(doc)
    await cache.set_json(cache_key, response_doc, ttl=120)
    return response_doc


@router.patch("/{workspace_id}/{task_id}")
async def update_task(
    workspace_id: str,
    task_id: str,
    body: TaskUpdate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    existing = await db["tasks"].find_one({"_id": oid, "workspace_id": workspace_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.utcnow()

    await db["tasks"].update_one({"_id": oid}, {"$set": updates})
    updated = await db["tasks"].find_one({"_id": oid})
    response_doc = _doc_to_response(updated)

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(_single_task_cache_key(task_id))
    keys_to_delete = [k async for k in redis.scan_iter(f"tasks:{workspace_id}:*")]
    if keys_to_delete:
        await cache.delete(*keys_to_delete)

    await sync_task_to_firestore(updated)
    await publish_task_event("task.updated", response_doc)
    return response_doc


@router.delete("/{workspace_id}/{task_id}", status_code=204)
async def delete_task(
    workspace_id: str,
    task_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    result = await db["tasks"].delete_one({"_id": oid, "workspace_id": workspace_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(_single_task_cache_key(task_id))
    keys_to_delete = [k async for k in redis.scan_iter(f"tasks:{workspace_id}:*")]
    if keys_to_delete:
        await cache.delete(*keys_to_delete)

    await publish_task_event("task.deleted", {"id": task_id, "workspace_id": workspace_id})


class CommentCreate(BaseModel):
    content: str


@router.post("/{workspace_id}/{task_id}/comments", status_code=201)
async def add_comment(
    workspace_id: str,
    task_id: str,
    body: CommentCreate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    now = datetime.utcnow()
    comment = {
        "_id": ObjectId(),
        "author_id": uid,
        "content": body.content,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["tasks"].update_one(
        {"_id": oid, "workspace_id": workspace_id},
        {"$push": {"comments": comment}, "$set": {"updated_at": now}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(_single_task_cache_key(task_id))

    return {"id": str(comment["_id"]), "author_id": uid, "content": body.content, "created_at": now}


@router.post("/{workspace_id}/{task_id}/attachments", status_code=201)
async def add_attachment(
    workspace_id: str,
    task_id: str,
    request: Request,
    file: UploadFile = File(...),
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]

    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit")

    allowed_types = {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "application/zip",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Unsupported file type")

    file_bytes = await file.read()
    gcs_path = await upload_file(file_bytes, file.filename, file.content_type)
    if not gcs_path:
        raise HTTPException(status_code=500, detail="File upload failed")

    db = await get_db()
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    now = datetime.utcnow()
    attachment = {
        "_id": ObjectId(),
        "filename": file.filename,
        "content_type": file.content_type,
        "gcs_path": gcs_path,
        "uploaded_by": uid,
        "uploaded_at": now,
        "size_bytes": len(file_bytes),
    }
    result = await db["tasks"].update_one(
        {"_id": oid, "workspace_id": workspace_id},
        {"$push": {"attachments": attachment}, "$set": {"updated_at": now}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(_single_task_cache_key(task_id))

    return {
        "id": str(attachment["_id"]),
        "filename": file.filename,
        "gcs_path": gcs_path,
        "signed_url": get_signed_url(gcs_path),
        "uploaded_at": now,
    }
