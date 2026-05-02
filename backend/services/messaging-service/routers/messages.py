import sys
import os
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from auth import verify_firebase_token
from db import get_db
from pubsub_client import publish_event

router = APIRouter()


class MessageCreate(BaseModel):
    content: str
    thread_id: Optional[str] = None


class MessageEdit(BaseModel):
    content: str


class ReactionAdd(BaseModel):
    emoji: str


def _doc_to_response(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    if "channel_id" in doc:
        doc["channel_id"] = str(doc["channel_id"])
    if "thread_id" in doc and doc["thread_id"]:
        doc["thread_id"] = str(doc["thread_id"])
    return doc


@router.get("/{channel_id}")
async def list_messages(
    channel_id: str,
    request: Request,
    cursor: Optional[str] = Query(None, description="Message ID cursor for pagination"),
    limit: int = Query(50, ge=1, le=100),
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    query: dict = {"channel_id": channel_id, "thread_id": None}

    if cursor:
        try:
            cursor_oid = ObjectId(cursor)
            query["_id"] = {"$lt": cursor_oid}
        except Exception:
            pass

    messages_cursor = (
        db["messages"].find(query).sort("_id", -1).limit(limit)
    )
    messages = [_doc_to_response(doc) async for doc in messages_cursor]
    has_more = len(messages) == limit
    next_cursor = messages[-1]["id"] if has_more and messages else None

    return {
        "messages": list(reversed(messages)),
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


@router.post("/{channel_id}", status_code=201)
async def send_message(
    channel_id: str,
    body: MessageCreate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()

    channel = await db["channels"].find_one({"_id": ObjectId(channel_id) if ObjectId.is_valid(channel_id) else None})
    if channel and uid not in channel.get("members", []):
        raise HTTPException(status_code=403, detail="Not a member of this channel")

    now = datetime.utcnow()
    doc = {
        "channel_id": channel_id,
        "workspace_id": channel["workspace_id"] if channel else None,
        "author_id": uid,
        "content": body.content,
        "thread_id": body.thread_id,
        "reactions": {},
        "edited": False,
        "deleted": False,
        "reply_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["messages"].insert_one(doc)
    created = await db["messages"].find_one({"_id": result.inserted_id})
    response_doc = _doc_to_response(created)

    if body.thread_id:
        try:
            parent_oid = ObjectId(body.thread_id)
            await db["messages"].update_one(
                {"_id": parent_oid}, {"$inc": {"reply_count": 1}}
            )
        except Exception:
            pass

    await publish_event(
        "devcollab-message-events",
        "message.created",
        {**response_doc, "channel_id": channel_id},
    )
    return response_doc


@router.patch("/{channel_id}/{message_id}")
async def edit_message(
    channel_id: str,
    message_id: str,
    body: MessageEdit,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    try:
        oid = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    msg = await db["messages"].find_one({"_id": oid, "channel_id": channel_id})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg["author_id"] != uid:
        raise HTTPException(status_code=403, detail="Cannot edit another user's message")

    await db["messages"].update_one(
        {"_id": oid},
        {"$set": {"content": body.content, "edited": True, "updated_at": datetime.utcnow()}},
    )
    updated = await db["messages"].find_one({"_id": oid})
    return _doc_to_response(updated)


@router.delete("/{channel_id}/{message_id}", status_code=204)
async def delete_message(
    channel_id: str,
    message_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    try:
        oid = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    msg = await db["messages"].find_one({"_id": oid, "channel_id": channel_id})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg["author_id"] != uid:
        raise HTTPException(status_code=403, detail="Cannot delete another user's message")

    await db["messages"].update_one(
        {"_id": oid},
        {"$set": {"deleted": True, "content": "[deleted]", "updated_at": datetime.utcnow()}},
    )


@router.post("/{channel_id}/{message_id}/reactions", status_code=201)
async def add_reaction(
    channel_id: str,
    message_id: str,
    body: ReactionAdd,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()
    try:
        oid = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    msg = await db["messages"].find_one({"_id": oid, "channel_id": channel_id})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    reactions = msg.get("reactions", {})
    emoji_users = reactions.get(body.emoji, [])
    if uid in emoji_users:
        emoji_users.remove(uid)
    else:
        emoji_users.append(uid)

    reactions[body.emoji] = emoji_users
    await db["messages"].update_one(
        {"_id": oid},
        {"$set": {"reactions": reactions, "updated_at": datetime.utcnow()}},
    )
    return {"emoji": body.emoji, "users": emoji_users}


@router.get("/{channel_id}/{message_id}/thread")
async def get_thread(
    channel_id: str,
    message_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    parent = await db["messages"].find_one({"_id": oid, "channel_id": channel_id})
    if not parent:
        raise HTTPException(status_code=404, detail="Message not found")

    replies_cursor = db["messages"].find(
        {"thread_id": message_id, "deleted": {"$ne": True}}
    ).sort("created_at", 1)

    replies = [_doc_to_response(doc) async for doc in replies_cursor]
    return {"parent": _doc_to_response(parent), "replies": replies}
