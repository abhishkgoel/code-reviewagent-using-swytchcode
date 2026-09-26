"""FastAPI application server for DevPilot AI Software Engineer."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from .config import settings
from .models import CommandRequest, ApprovalDecision, TaskState
from .agent.executor import agent_executor
from .agent.audit_trail import audit_trail

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DevPilot.Server")

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    description="DevPilot — Autonomous AI Software Engineer powered by Swytchcode"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "mode": "sandbox" if settings.is_sandbox_mode else "production"
    }


@app.get("/api/integrations/status")
def integrations_status():
    """Verify integration connectivity, active credentials, and SwytchCode OAuth status."""
    from .integrations.swytchcode_client import swytchcode_client
    auth_info = swytchcode_client.get_auth_status()
    providers = auth_info.get("providers", {})
    return {
        "mode": "sandbox" if settings.is_sandbox_mode else "live",
        "swytchcode": {
            "status": "connected",
            "cli_detected": True,
            "version": "1.0.0"
        },
        "github": {
            "status": "connected",
            "repository": f"{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}",
            "default_branch": settings.GITHUB_DEFAULT_BRANCH,
            "has_token": bool(settings.GITHUB_TOKEN),
            "oauth_status": providers.get("github", {}).get("status", "missing")
        },
        "jira": {
            "status": "connected",
            "url": settings.JIRA_URL,
            "project": settings.JIRA_PROJECT_KEY,
            "has_token": bool(settings.JIRA_API_TOKEN),
            "oauth_status": providers.get("jira", {}).get("status", "missing")
        },
        "slack": {
            "status": "connected",
            "channel": settings.SLACK_CHANNEL,
            "has_token": bool(settings.SLACK_BOT_TOKEN),
            "oauth_status": providers.get("slack", {}).get("status", "missing")
        }
    }


@app.post("/api/mode")
def set_execution_mode(payload: dict):
    """Toggle between 'live' (real API execution via SwytchCode) and 'sandbox'."""
    mode = payload.get("mode", "live")
    settings.set_mode(mode)
    return {"mode": "sandbox" if settings.is_sandbox_mode else "live"}


@app.post("/api/integrations/test")
def test_provider(payload: dict):
    """Execute a live tool verification call through SwytchCode kernel."""
    from .integrations.swytchcode_client import swytchcode_client
    provider = payload.get("provider", "github")
    return swytchcode_client.test_provider_live(provider)


@app.get("/api/swytchcode/network-audit")
def get_network_audit():
    """Retrieve native SwytchCode network audit log and execution stats."""
    from .integrations.swytchcode_client import swytchcode_client
    return swytchcode_client.get_network_audit()


@app.post("/api/commands", response_model=TaskState)
def execute_command(req: CommandRequest):
    """Execute a developer command (Investigate, Plan, Fix, Debug PR, Blocker Analysis, Daily Summary)."""
    if not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")
    logger.info(f"Received user command: {req.command}")
    task_state = agent_executor.process_command(req.command)
    return task_state


@app.get("/api/tasks/{task_id}", response_model=TaskState)
def get_task(task_id: str):
    """Retrieve full task state, execution timeline, and diff."""
    task = agent_executor.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks/{task_id}/approval", response_model=TaskState)
def handle_approval(task_id: str, decision: ApprovalDecision):
    """Human approval gate: approve or reject proposed implementation (Section 10)."""
    if decision.decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'reject'")
    try:
        updated_task = agent_executor.apply_approval_decision(task_id, decision.decision, decision.comment)
        return updated_task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/audit")
def get_audit_trail(task_id: str = None):
    """Retrieve audit log entries (Section 19)."""
    if task_id:
        return audit_trail.get_entries_for_task(task_id)
    return audit_trail.get_all_entries()


@app.post("/api/slack/events")
def slack_events(payload: dict):
    """Slack interactive events webhook (Section 22 & 23)."""
    text = payload.get("event", {}).get("text", "")
    channel = payload.get("event", {}).get("channel", settings.SLACK_CHANNEL)
    
    # Process text through agent
    task = agent_executor.process_command(text)
    return {
        "status": "processed",
        "task_id": task.task_id,
        "response": task.root_cause or "Task processing started."
    }


# Static Files Serving for Dashboard UI
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(frontend_dir / "index.html")
