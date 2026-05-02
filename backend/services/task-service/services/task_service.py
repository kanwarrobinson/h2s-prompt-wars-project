import sys
import os
from datetime import datetime
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from pubsub_client import publish_task_event
from firestore_client import sync_task_to_firestore
from gcs_client import get_signed_url


def _doc_to_response(doc: dict) -> dict:
    """Convert MongoDB document to API response dict."""
    doc = dict(doc)
    if "_id" in doc:
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


async def get_tasks_for_workspace(
    db: AsyncIOMotorDatabase,
    workspace_id: str,
    sprint_id: Optional[str] = None,
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    query: dict = {"workspace_id": workspace_id}
    if sprint_id:
        query["sprint_id"] = sprint_id
    if status:
        query["status"] = status
    if assignee_id:
        query["assignee_ids"] = assignee_id
    if priority:
        query["priority"] = priority

    cursor = db["tasks"].find(query).sort("updated_at", -1).limit(limit)
    return [_doc_to_response(doc) async for doc in cursor]


async def create_task(db: AsyncIOMotorDatabase, task_data: dict, reporter_id: str) -> dict:
    now = datetime.utcnow()
    doc = {
        **task_data,
        "reporter_id": reporter_id,
        "comments": [],
        "attachments": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db["tasks"].insert_one(doc)
    created = await db["tasks"].find_one({"_id": result.inserted_id})
    response_doc = _doc_to_response(created)
    await publish_task_event("task.created", response_doc)
    return response_doc


async def update_task(db: AsyncIOMotorDatabase, task_id: str, workspace_id: str, updates: dict) -> Optional[dict]:
    try:
        oid = ObjectId(task_id)
    except Exception:
        return None

    updates["updated_at"] = datetime.utcnow()
    result = await db["tasks"].update_one(
        {"_id": oid, "workspace_id": workspace_id}, {"$set": updates}
    )
    if result.matched_count == 0:
        return None

    updated = await db["tasks"].find_one({"_id": oid})
    response_doc = _doc_to_response(updated)
    await sync_task_to_firestore(updated)
    await publish_task_event("task.updated", response_doc)
    return response_doc


async def delete_task(db: AsyncIOMotorDatabase, task_id: str, workspace_id: str) -> bool:
    try:
        oid = ObjectId(task_id)
    except Exception:
        return False

    result = await db["tasks"].delete_one({"_id": oid, "workspace_id": workspace_id})
    if result.deleted_count > 0:
        await publish_task_event("task.deleted", {"id": task_id, "workspace_id": workspace_id})
        return True
    return False
