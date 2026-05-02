import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@devcollab.app")
FROM_NAME = os.environ.get("FROM_NAME", "DevCollab")


async def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    plain_content: Optional[str] = None,
) -> bool:
    """Send a transactional email via SendGrid."""
    if not SENDGRID_API_KEY:
        logger.warning(f"[Email mock] To: {to_email} | Subject: {subject}")
        return True

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        message = Mail(
            from_email=Email(FROM_EMAIL, FROM_NAME),
            to_emails=To(to_email, to_name),
            subject=subject,
            html_content=html_content,
        )
        if plain_content:
            message.add_content(Content("text/plain", plain_content))

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code >= 400:
            logger.error(f"SendGrid error {response.status_code}: {response.body}")
            return False
        return True
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False


async def handle_email_notification(payload: dict) -> bool:
    """Handle an email notification job from Cloud Tasks."""
    notification_type = payload.get("type", "general")
    recipient_email = payload.get("email")
    recipient_name = payload.get("name", "")
    workspace_name = payload.get("workspace_name", "Your Workspace")

    if not recipient_email:
        logger.error("Email notification missing recipient email")
        return False

    templates = {
        "task_assigned": {
            "subject": f"[{workspace_name}] You've been assigned a task",
            "html": _task_assigned_template(payload),
        },
        "mention": {
            "subject": f"[{workspace_name}] You were mentioned",
            "html": _mention_template(payload),
        },
        "sprint_started": {
            "subject": f"[{workspace_name}] Sprint started",
            "html": _sprint_template(payload, "started"),
        },
        "sprint_completed": {
            "subject": f"[{workspace_name}] Sprint completed",
            "html": _sprint_template(payload, "completed"),
        },
        "general": {
            "subject": payload.get("subject", f"[{workspace_name}] Notification"),
            "html": payload.get("html_content", "<p>You have a new notification.</p>"),
        },
    }

    template = templates.get(notification_type, templates["general"])
    return await send_email(
        recipient_email,
        recipient_name,
        template["subject"],
        template["html"],
    )


def _task_assigned_template(payload: dict) -> str:
    task_title = payload.get("task_title", "Untitled task")
    assigned_by = payload.get("assigned_by", "Someone")
    task_url = payload.get("task_url", "#")
    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #4f46e5;">Task Assigned to You</h2>
        <p>{assigned_by} has assigned you a task:</p>
        <div style="background: #f9fafb; border-left: 4px solid #4f46e5; padding: 16px; margin: 16px 0;">
            <strong>{task_title}</strong>
        </div>
        <a href="{task_url}" style="background: #4f46e5; color: white; padding: 10px 20px;
           text-decoration: none; border-radius: 6px; display: inline-block;">
            View Task
        </a>
    </div>
    """


def _mention_template(payload: dict) -> str:
    mentioned_by = payload.get("mentioned_by", "Someone")
    context = payload.get("context", "")
    url = payload.get("url", "#")
    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #4f46e5;">You Were Mentioned</h2>
        <p>{mentioned_by} mentioned you:</p>
        <blockquote style="border-left: 4px solid #e5e7eb; padding: 12px; color: #6b7280;">
            {context}
        </blockquote>
        <a href="{url}" style="background: #4f46e5; color: white; padding: 10px 20px;
           text-decoration: none; border-radius: 6px; display: inline-block;">
            View Context
        </a>
    </div>
    """


def _sprint_template(payload: dict, action: str) -> str:
    sprint_name = payload.get("sprint_name", "Sprint")
    project_name = payload.get("project_name", "Project")
    url = payload.get("url", "#")
    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #4f46e5;">Sprint {action.capitalize()}</h2>
        <p>The sprint <strong>{sprint_name}</strong> in project <strong>{project_name}</strong>
           has been {action}.</p>
        <a href="{url}" style="background: #4f46e5; color: white; padding: 10px 20px;
           text-decoration: none; border-radius: 6px; display: inline-block;">
            View Sprint
        </a>
    </div>
    """
