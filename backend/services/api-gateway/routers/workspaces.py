import sys
import os
import re
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from auth import verify_firebase_token
from db import get_db
from redis_client import get_redis, CacheService

router = APIRouter()


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    github_org: Optional[str] = None
    sso_enabled: Optional[bool] = None


class InviteMemberRequest(BaseModel):
    email: str
    role: str = "member"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:50]


async def _get_workspace_or_404(workspace_id: str, db) -> dict:
    try:
        oid = ObjectId(workspace_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid workspace ID")
    ws = await db["workspaces"].find_one({"_id": oid})
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


async def _assert_member(ws: dict, uid: str) -> None:
    members = [m["user_id"] for m in ws.get("members", [])]
    if uid not in members:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")


async def _assert_admin(ws: dict, uid: str) -> None:
    for m in ws.get("members", []):
        if m["user_id"] == uid and m["role"] in ("admin", "owner"):
            return
    raise HTTPException(status_code=403, detail="Admin access required")


@router.get("")
async def list_workspaces(request: Request, token_data: dict = Depends(verify_firebase_token)):
    uid = token_data["uid"]
    db = await get_db()
    cursor = db["workspaces"].find({"members.user_id": uid})
    workspaces = []
    async for ws in cursor:
        workspaces.append(
            {
                "id": str(ws["_id"]),
                "name": ws["name"],
                "slug": ws["slug"],
                "description": ws.get("description"),
                "member_count": len(ws.get("members", [])),
                "created_at": ws["created_at"],
            }
        )
    return workspaces


@router.post("", status_code=201)
async def create_workspace(
    body: WorkspaceCreate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()

    slug = body.slug or _slugify(body.name)
    existing = await db["workspaces"].find_one({"slug": slug})
    if existing:
        raise HTTPException(status_code=409, detail=f"Slug '{slug}' already in use")

    now = datetime.utcnow()
    doc = {
        "name": body.name,
        "slug": slug,
        "description": body.description,
        "github_org": None,
        "sso_enabled": False,
        "members": [{"user_id": uid, "role": "owner", "joined_at": now}],
        "created_at": now,
        "updated_at": now,
    }
    result = await db["workspaces"].insert_one(doc)
    await db["users"].update_one({"firebase_uid": uid}, {"$addToSet": {"workspaces": str(result.inserted_id)}})
    doc["id"] = str(result.inserted_id)
    return doc


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    ws = await _get_workspace_or_404(workspace_id, db)
    await _assert_member(ws, uid)

    redis = await get_redis()
    cache = CacheService(redis)
    cache_key = f"workspace:{workspace_id}"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    result = {
        "id": str(ws["_id"]),
        "name": ws["name"],
        "slug": ws["slug"],
        "description": ws.get("description"),
        "github_org": ws.get("github_org"),
        "sso_enabled": ws.get("sso_enabled", False),
        "members": ws.get("members", []),
        "created_at": ws["created_at"],
        "updated_at": ws["updated_at"],
    }
    await cache.set_json(cache_key, result, ttl=120)
    return result


@router.put("/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    body: WorkspaceUpdate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    ws = await _get_workspace_or_404(workspace_id, db)
    await _assert_admin(ws, uid)

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.utcnow()
    await db["workspaces"].update_one({"_id": ws["_id"]}, {"$set": updates})

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(f"workspace:{workspace_id}")
    return {"message": "Workspace updated"}


@router.post("/{workspace_id}/members", status_code=201)
async def invite_member(
    workspace_id: str,
    body: InviteMemberRequest,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    ws = await _get_workspace_or_404(workspace_id, db)
    await _assert_admin(ws, uid)

    target_user = await db["users"].find_one({"email": body.email})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_uid = target_user["firebase_uid"]
    current_members = [m["user_id"] for m in ws.get("members", [])]
    if target_uid in current_members:
        raise HTTPException(status_code=409, detail="User already a member")

    now = datetime.utcnow()
    await db["workspaces"].update_one(
        {"_id": ws["_id"]},
        {
            "$push": {"members": {"user_id": target_uid, "role": body.role, "joined_at": now}},
            "$set": {"updated_at": now},
        },
    )
    await db["users"].update_one(
        {"firebase_uid": target_uid},
        {"$addToSet": {"workspaces": workspace_id}},
    )

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(f"workspace:{workspace_id}")
    return {"message": "Member invited", "user_id": target_uid}


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: str,
    user_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    ws = await _get_workspace_or_404(workspace_id, db)
    await _assert_admin(ws, uid)

    await db["workspaces"].update_one(
        {"_id": ws["_id"]},
        {
            "$pull": {"members": {"user_id": user_id}},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )
    await db["users"].update_one(
        {"firebase_uid": user_id},
        {"$pull": {"workspaces": workspace_id}},
    )

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(f"workspace:{workspace_id}")
    return {"message": "Member removed"}
