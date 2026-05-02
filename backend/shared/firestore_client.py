import logging
import uuid
from typing import Any, Optional
from .config import settings

_db: Any = None


def get_firestore() -> Any:
    global _db
    if _db is None:
        try:
            from google.cloud import firestore
            _db = firestore.AsyncClient(project=settings.firebase_project_id)
        except Exception as e:
            logging.warning(f"Firestore not available: {e}")
            _db = None
    return _db


async def sync_task_to_firestore(task: dict) -> None:
    """Mirror task state changes to Firestore for real-time client push."""
    db = get_firestore()
    if not db:
        return
    try:
        workspace_id = str(task.get("workspace_id", ""))
        task_id = str(task.get("_id", task.get("id", "")))
        doc_ref = (
            db.collection("workspaces")
            .document(workspace_id)
            .collection("task_updates")
            .document(task_id)
        )
        await doc_ref.set(
            {
                "status": task.get("status"),
                "assignee_ids": [str(a) for a in task.get("assignee_ids", [])],
                "updated_at": task.get("updated_at"),
                "updated_by": str(task.get("reporter_id", "")),
            },
            merge=True,
        )
    except Exception as e:
        logging.error(f"Firestore sync error: {e}")


async def write_notification(workspace_id: str, user_id: str, notif: dict) -> None:
    """Write notification to Firestore for real-time delivery."""
    db = get_firestore()
    if not db:
        return
    try:
        notif_id = str(uuid.uuid4())
        doc_ref = (
            db.collection("workspaces")
            .document(workspace_id)
            .collection("notifications")
            .document(user_id)
            .collection("items")
            .document(notif_id)
        )
        await doc_ref.set({**notif, "read": False})
    except Exception as e:
        logging.error(f"Firestore notification error: {e}")
