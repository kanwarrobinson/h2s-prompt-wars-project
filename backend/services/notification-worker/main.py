import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from handlers.email_handler import handle_email_notification
from handlers.push_handler import handle_push_notification
from handlers.digest_handler import handle_digest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting notification-worker")
    firebase_project = os.environ.get("FIREBASE_PROJECT_ID", "devcollab-local")
    try:
        import firebase_admin
        from firebase_admin import credentials
        try:
            firebase_admin.get_app()
        except ValueError:
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path:
                cred = credentials.Certificate(cred_path)
            else:
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": firebase_project})
        logger.info("Firebase initialized")
    except Exception as e:
        logger.warning(f"Firebase init failed: {e}")
    yield
    logger.info("notification-worker shutdown")


app = FastAPI(title="DevCollab Notification Worker", version="1.0.0", lifespan=lifespan)


async def _verify_oidc_token(request: Request) -> None:
    """Verify OIDC token sent by Cloud Tasks in production."""
    if ENVIRONMENT == "development":
        return

    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing OIDC token")

    token = authorization.split(" ", 1)[1]
    try:
        from google.auth import transport, id_token as google_id_token
        import google.auth.transport.requests

        request_adapter = google.auth.transport.requests.Request()
        id_info = google_id_token.verify_oauth2_token(
            token,
            request_adapter,
            audience=os.environ.get("CLOUD_RUN_URL", ""),
        )
        if not id_info.get("email", "").endswith(".iam.gserviceaccount.com"):
            raise HTTPException(status_code=403, detail="Invalid service account")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OIDC verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid OIDC token")


class NotificationJob(BaseModel):
    job_type: str
    payload: dict


@app.post("/tasks/email")
async def process_email_task(request: Request, job: NotificationJob):
    await _verify_oidc_token(request)
    try:
        success = await handle_email_notification(job.payload)
        if not success:
            raise HTTPException(status_code=500, detail="Email delivery failed")
        return {"status": "sent"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/push")
async def process_push_task(request: Request, job: NotificationJob):
    await _verify_oidc_token(request)
    try:
        success = await handle_push_notification(job.payload)
        if not success:
            raise HTTPException(status_code=500, detail="Push delivery failed")
        return {"status": "sent"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Push task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/digest")
async def process_digest_task(request: Request, job: NotificationJob):
    await _verify_oidc_token(request)
    try:
        success = await handle_digest(job.payload)
        if not success:
            raise HTTPException(status_code=500, detail="Digest delivery failed")
        return {"status": "sent"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Digest task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
