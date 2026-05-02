import sys
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from auth import verify_firebase_token, get_current_user
from db import get_db
from redis_client import get_redis, CacheService

router = APIRouter()


class LoginRequest(BaseModel):
    firebase_token: str


class UserProfileResponse(BaseModel):
    id: str
    firebase_uid: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    workspaces: list[str] = []
    notification_prefs: dict = {}
    created_at: datetime
    updated_at: datetime


@router.post("/login")
async def login(request: Request, body: LoginRequest):
    """Verify Firebase token, create/update user in MongoDB, return profile."""
    import firebase_admin.auth as fb_auth

    try:
        decoded = fb_auth.verify_id_token(body.firebase_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    uid = decoded["uid"]
    email = decoded.get("email", "")
    name = decoded.get("name", email.split("@")[0] if email else "Unknown")
    picture = decoded.get("picture", None)

    db = await get_db()
    now = datetime.utcnow()

    existing = await db["users"].find_one({"firebase_uid": uid})
    if existing:
        await db["users"].update_one(
            {"firebase_uid": uid},
            {"$set": {"email": email, "avatar_url": picture, "updated_at": now}},
        )
        user = await db["users"].find_one({"firebase_uid": uid})
    else:
        user_doc = {
            "firebase_uid": uid,
            "email": email,
            "display_name": name,
            "avatar_url": picture,
            "workspaces": [],
            "notification_prefs": {
                "email_digest": "daily",
                "push_enabled": True,
                "mention_only": False,
            },
            "created_at": now,
            "updated_at": now,
        }
        result = await db["users"].insert_one(user_doc)
        user = await db["users"].find_one({"_id": result.inserted_id})

    redis = await get_redis()
    cache = CacheService(redis)
    await cache.set_json(f"user_session:{uid}", {"uid": uid, "email": email}, ttl=3600)

    return {
        "id": str(user["_id"]),
        "firebase_uid": user["firebase_uid"],
        "email": user["email"],
        "display_name": user["display_name"],
        "avatar_url": user.get("avatar_url"),
        "workspaces": user.get("workspaces", []),
        "notification_prefs": user.get("notification_prefs", {}),
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


@router.post("/logout")
async def logout(request: Request, token_data: dict = Depends(verify_firebase_token)):
    """Invalidate session in Redis."""
    uid = token_data["uid"]
    redis = await get_redis()
    cache = CacheService(redis)
    await cache.delete(f"user_session:{uid}")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(request: Request, token_data: dict = Depends(verify_firebase_token)):
    """Return current user profile."""
    uid = token_data["uid"]
    db = await get_db()
    user = await db["users"].find_one({"firebase_uid": uid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user["_id"]),
        "firebase_uid": user["firebase_uid"],
        "email": user["email"],
        "display_name": user["display_name"],
        "avatar_url": user.get("avatar_url"),
        "workspaces": user.get("workspaces", []),
        "notification_prefs": user.get("notification_prefs", {}),
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }
