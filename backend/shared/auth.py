from fastapi import HTTPException, Request
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

_firebase_initialized = False


def init_firebase(project_id: str) -> None:
    global _firebase_initialized
    if not _firebase_initialized:
        try:
            firebase_admin.get_app()
        except ValueError:
            import os
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path:
                cred = credentials.Certificate(cred_path)
            else:
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        _firebase_initialized = True


async def verify_firebase_token(request: Request) -> dict:
    """Dependency: verify Firebase ID token from Authorization header."""
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        decoded = firebase_auth.verify_id_token(token)
        request.state.user_id = decoded["uid"]
        request.state.email = decoded.get("email", "")
        return decoded
    except firebase_admin.auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request) -> dict:
    """Get user info set by auth dependency."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "uid": request.state.user_id,
        "email": getattr(request.state, "email", ""),
    }
