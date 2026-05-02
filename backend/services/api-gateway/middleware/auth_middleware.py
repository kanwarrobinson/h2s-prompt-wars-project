import sys
import os

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from auth import verify_firebase_token
import firebase_admin.auth as fb_auth

EXCLUDED_PATHS = {"/health", "/ready", "/api/docs", "/api/redoc", "/openapi.json"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return JSONResponse({"detail": "Missing bearer token"}, status_code=401)

        token = authorization.split(" ", 1)[1]
        try:
            decoded = fb_auth.verify_id_token(token)
            request.state.user_id = decoded["uid"]
            request.state.email = decoded.get("email", "")
        except fb_auth.ExpiredIdTokenError:
            return JSONResponse({"detail": "Token expired"}, status_code=401)
        except Exception:
            return JSONResponse({"detail": "Invalid token"}, status_code=401)

        return await call_next(request)
