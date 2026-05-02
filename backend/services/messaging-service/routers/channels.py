import sys
import os
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from auth import verify_firebase_token
from db import get_db

router = APIRouter()


class ChannelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class AddMemberRequest(BaseModel):
    user_id: str


class DMRequest(BaseModel):
    workspace_id: str
    target_user_id: str


def _doc_to_response(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("/{workspace_id}")
async def list_channels(
    workspace_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    cursor = db["channels"].find(
        {"workspace_id": workspace_id, "members": uid, "is_archived": {"$ne": True}}
    ).sort("name", 1)

    channels = []
    async for doc in cursor:
        channels.append(_doc_to_response(doc))
    return channels


@router.post("/{workspace_id}", status_code=201)
async def create_channel(
    workspace_id: str,
    body: ChannelCreate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()

    existing = await db["channels"].find_one(
        {"workspace_id": workspace_id, "name": body.name, "type": "channel"}
    )
    if existing:
        raise HTTPException(status_code=409, detail="Channel with this name already exists")

    now = datetime.utcnow()
    doc = {
        "workspace_id": workspace_id,
        "name": body.name,
        "description": body.description,
        "is_private": body.is_private,
        "type": "channel",
        "members": [uid],
        "created_by": uid,
        "is_archived": False,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["channels"].insert_one(doc)
    created = await db["channels"].find_one({"_id": result.inserted_id})
    return _doc_to_response(created)


@router.get("/{workspace_id}/{channel_id}")
async def get_channel(
    workspace_id: str,
    channel_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    try:
        oid = ObjectId(channel_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid channel ID")

    channel = await db["channels"].find_one({"_id": oid, "workspace_id": workspace_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    if uid not in channel.get("members", []) and channel.get("is_private"):
        raise HTTPException(status_code=403, detail="Not a member of this channel")

    return _doc_to_response(channel)


@router.post("/{workspace_id}/{channel_id}/members", status_code=201)
async def add_member(
    workspace_id: str,
    channel_id: str,
    body: AddMemberRequest,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    try:
        oid = ObjectId(channel_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid channel ID")

    channel = await db["channels"].find_one({"_id": oid, "workspace_id": workspace_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    if body.user_id in channel.get("members", []):
        raise HTTPException(status_code=409, detail="User is already a member")

    await db["channels"].update_one(
        {"_id": oid},
        {"$push": {"members": body.user_id}, "$set": {"updated_at": datetime.utcnow()}},
    )
    return {"message": "Member added"}


@router.delete("/{workspace_id}/{channel_id}/members/{user_id}")
async def remove_member(
    workspace_id: str,
    channel_id: str,
    user_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    try:
        oid = ObjectId(channel_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid channel ID")

    channel = await db["channels"].find_one({"_id": oid, "workspace_id": workspace_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    if uid != user_id and uid not in channel.get("admins", []):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    await db["channels"].update_one(
        {"_id": oid},
        {"$pull": {"members": user_id}, "$set": {"updated_at": datetime.utcnow()}},
    )
    return {"message": "Member removed"}


@router.post("/dm", status_code=201)
async def create_or_get_dm(
    body: DMRequest,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()

    participants = sorted([uid, body.target_user_id])
    existing = await db["channels"].find_one(
        {
            "workspace_id": body.workspace_id,
            "type": "dm",
            "members": {"$all": participants, "$size": 2},
        }
    )
    if existing:
        return _doc_to_response(existing)

    now = datetime.utcnow()
    doc = {
        "workspace_id": body.workspace_id,
        "type": "dm",
        "name": f"dm-{'-'.join(participants)}",
        "members": participants,
        "is_private": True,
        "is_archived": False,
        "created_by": uid,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["channels"].insert_one(doc)
    created = await db["channels"].find_one({"_id": result.inserted_id})
    return _doc_to_response(created)
