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

router = APIRouter()


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class NotificationPrefsUpdate(BaseModel):
    email_digest: Optional[str] = None
    push_enabled: Optional[bool] = None
    mention_only: Optional[bool] = None


@router.get("/search")
async def search_users(
    q: str = Query(..., min_length=1),
    request: Request = None,
    token_data: dict = Depends(verify_firebase_token),
):
    """Search users by email or display name."""
    db = await get_db()
    cursor = db["users"].find(
        {
            "$or": [
                {"email": {"$regex": q, "$options": "i"}},
                {"display_name": {"$regex": q, "$options": "i"}},
            ]
        },
        {"firebase_uid": 1, "email": 1, "display_name": 1, "avatar_url": 1},
    ).limit(20)

    users = []
    async for user in cursor:
        users.append(
            {
                "id": str(user["_id"]),
                "firebase_uid": user["firebase_uid"],
                "email": user["email"],
                "display_name": user["display_name"],
                "avatar_url": user.get("avatar_url"),
            }
        )
    return users


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    db = await get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = await db["users"].find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user["_id"]),
        "firebase_uid": user["firebase_uid"],
        "email": user["email"],
        "display_name": user["display_name"],
        "avatar_url": user.get("avatar_url"),
        "created_at": user["created_at"],
    }


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    body: UserProfileUpdate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()

    user = await db["users"].find_one({"firebase_uid": uid})
    if not user or str(user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's profile")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.utcnow()
    await db["users"].update_one({"_id": user["_id"]}, {"$set": updates})
    return {"message": "Profile updated"}


@router.put("/{user_id}/notifications")
async def update_notification_prefs(
    user_id: str,
    body: NotificationPrefsUpdate,
    request: Request,
    token_data: dict = Depends(verify_firebase_token),
):
    uid = token_data["uid"]
    db = await get_db()

    user = await db["users"].find_one({"firebase_uid": uid})
    if not user or str(user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's preferences")

    prefs_updates = {
        f"notification_prefs.{k}": v
        for k, v in body.model_dump().items()
        if v is not None
    }
    prefs_updates["updated_at"] = datetime.utcnow()
    await db["users"].update_one({"_id": user["_id"]}, {"$set": prefs_updates})
    return {"message": "Notification preferences updated"}
