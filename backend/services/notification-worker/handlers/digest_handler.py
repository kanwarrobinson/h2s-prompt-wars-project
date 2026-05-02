import logging
from datetime import datetime, timedelta
from typing import Optional

from .email_handler import send_email

logger = logging.getLogger(__name__)


async def generate_digest(
    user_id: str,
    email: str,
    name: str,
    workspace_id: str,
    workspace_name: str,
    period: str = "daily",
) -> bool:
    """Generate and send a daily/weekly activity digest email."""
    # In production this would query MongoDB for the user's activity
    items = await _collect_digest_items(user_id, workspace_id, period)
    if not items:
        logger.info(f"No digest items for {user_id}, skipping")
        return True

    html = _render_digest_html(name, workspace_name, items, period)
    subject = f"[{workspace_name}] Your {'Daily' if period == 'daily' else 'Weekly'} Digest"

    return await send_email(email, name, subject, html)


async def _collect_digest_items(user_id: str, workspace_id: str, period: str) -> list[dict]:
    """Collect items for the digest. Returns list of activity items."""
    # This would query MongoDB in production
    return []


def _render_digest_html(
    name: str,
    workspace_name: str,
    items: list[dict],
    period: str,
) -> str:
    period_label = "Today" if period == "daily" else "This Week"
    items_html = "".join(
        f"""
        <li style="margin-bottom: 12px; padding: 12px; background: #f9fafb; border-radius: 6px;">
            <strong>{item.get('type', 'Activity').replace('_', ' ').title()}</strong><br>
            <span style="color: #6b7280;">{item.get('description', '')}</span>
        </li>
        """
        for item in items
    )

    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #4f46e5; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">DevCollab</h1>
            <p style="color: #c7d2fe; margin: 4px 0 0;">{workspace_name}</p>
        </div>

        <div style="background: white; padding: 24px; border: 1px solid #e5e7eb;">
            <h2 style="color: #1f2937;">Hi {name}, here's what happened {period_label}</h2>

            <h3 style="color: #4f46e5; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">
                Activity Summary
            </h3>
            <ul style="list-style: none; padding: 0;">
                {items_html if items_html else '<li style="color: #9ca3af;">No activity to show.</li>'}
            </ul>
        </div>

        <div style="background: #f9fafb; padding: 16px; text-align: center;
             border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                You're receiving this because you have digest emails enabled in DevCollab.<br>
                <a href="#" style="color: #4f46e5;">Manage notification preferences</a>
            </p>
        </div>
    </div>
    """


async def handle_digest(payload: dict) -> bool:
    """Handle a digest job from Cloud Tasks."""
    return await generate_digest(
        user_id=payload.get("user_id", ""),
        email=payload.get("email", ""),
        name=payload.get("name", ""),
        workspace_id=payload.get("workspace_id", ""),
        workspace_name=payload.get("workspace_name", "DevCollab"),
        period=payload.get("period", "daily"),
    )
