import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from firestore_client import sync_task_to_firestore as _sync


async def sync_task(task: dict) -> None:
    """Sync a task update to Firestore for real-time client push."""
    try:
        await _sync(task)
    except Exception as e:
        logging.error(f"Firestore sync error in task-service: {e}")


async def sync_task_status_change(task_id: str, workspace_id: str, new_status: str, updated_by: str) -> None:
    """Lightweight sync for status-only changes."""
    await sync_task({
        "id": task_id,
        "workspace_id": workspace_id,
        "status": new_status,
        "reporter_id": updated_by,
        "updated_at": None,
        "assignee_ids": [],
    })
