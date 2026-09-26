"""Swytchcode execution client and integration adapter.

Executes external actions against GitHub, Jira, and Slack via Swytchcode CLI (`swy exec`).
Features full error normalization, sandbox fallbacks, credential redaction, and audit logging.
"""
import subprocess
import json
import logging
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger("DevPilot.Swytchcode")


class SwytchcodeClient:
    def __init__(self):
        self.cli_path = settings.SWYTCHCODE_CLI_PATH
        self.cwd = str(settings.SWYTCHCODE_WORKSPACE_DIR)

    def _sanitize(self, data: Any) -> Any:
        """Recursively redact sensitive tokens or secrets."""
        sensitive_keys = {"token", "key", "secret", "password", "authorization", "bearer"}
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                if any(sk in k.lower() for sk in sensitive_keys):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = self._sanitize(v)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize(item) for item in data]
        return data

    def get_auth_status(self) -> Dict[str, Any]:
        """Check connected accounts using swy auth status."""
        try:
            res = subprocess.run(
                [self.cli_path, "auth", "connect"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=10
            )
            raw = (res.stdout + "\n" + res.stderr).strip()
            connected = {}
            for line in raw.splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[0] in ("github", "jira", "slack"):
                    connected[parts[0]] = {
                        "type": parts[1] if len(parts) > 1 else "oauth2",
                        "status": parts[2] if len(parts) > 2 else "missing",
                        "account": parts[4] if len(parts) > 4 else "-"
                    }
            return {"raw": raw, "providers": connected}
        except Exception as e:
            return {"error": str(e), "providers": {}}

    def get_network_audit(self) -> Dict[str, Any]:
        """Fetch Swytchcode native network audit log and execution stats."""
        try:
            net_res = subprocess.run(
                [self.cli_path, "audit", "network"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=10
            )
            stats_res = subprocess.run(
                [self.cli_path, "audit", "stats"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "network_activity": net_res.stdout.strip() or "No recent outbound network activity recorded in local kernel log.",
                "execution_stats": stats_res.stdout.strip() or "No execution stats available."
            }
        except Exception as e:
            return {"error": str(e), "network_activity": "", "execution_stats": ""}

    def test_provider_live(self, provider: str) -> Dict[str, Any]:
        """Run a live tool execution through Swytchcode kernel for verification."""
        tool_map = {
            "github": ("github.repo.get3", {"owner": settings.GITHUB_OWNER, "repo": settings.GITHUB_REPO}),
            "jira": ("jira.api.issue.get", {"issueIdOrKey": f"{settings.JIRA_PROJECT_KEY}-1"}),
            "slack": ("slack.chat.postmessage.create", {"channel": settings.SLACK_CHANNEL, "text": "DevPilot live connection test via Swytchcode"})
        }
        if provider not in tool_map:
            return {"error": f"Unknown provider: {provider}"}
        
        tool_id, inputs = tool_map[provider]
        try:
            body_json = json.dumps(inputs)
            cmd = [self.cli_path, "exec", tool_id, "--body", body_json, "--json"]
            res = subprocess.run(cmd, cwd=self.cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10)
            parsed = {}
            if res.stdout.strip():
                try:
                    parsed = json.loads(res.stdout)
                except Exception:
                    pass
            return {
                "provider": provider,
                "tool_id": tool_id,
                "cmd": f"swy exec {tool_id} --body '{body_json}' --json",
                "returncode": res.returncode,
                "response": parsed or res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "success": res.returncode == 0
            }
        except Exception as e:
            return {"provider": provider, "error": str(e), "success": False}

    def execute_tool(self, canonical_id: str, inputs: Dict[str, Any], use_sandbox: bool = False) -> Dict[str, Any]:
        """Execute a tool via Swytchcode kernel (`swy exec`)."""
        if use_sandbox or settings.is_sandbox_mode:
            logger.info(f"[Swytchcode-Sandbox] Executing mock for {canonical_id}")
            return self._execute_sandbox(canonical_id, inputs)

        try:
            # Build CLI command: swy exec canonical_id --body '...' --json
            body_json = json.dumps(inputs)
            cmd = [
                self.cli_path,
                "exec",
                canonical_id,
                "--body",
                body_json,
                "--json"
            ]

            logger.info(f"Running swy exec for {canonical_id} with inputs: {self._sanitize(inputs)}")
            result = subprocess.run(
                cmd,
                cwd=self.cwd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"status": "success", "raw": result.stdout}
            else:
                stderr = result.stderr.strip()
                error_msg = self.normalize_error(canonical_id, stderr or result.stdout)
                logger.warning(f"Swytchcode tool execution failed for {canonical_id}: {error_msg}")
                # In live mode, if external call fails, return the error or fallback
                return {
                    "error": True,
                    "message": error_msg,
                    "raw_stderr": stderr,
                    "canonical_id": canonical_id,
                    "status_code": result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "error": True,
                "message": f"Operation timed out while executing {canonical_id} via Swytchcode.",
                "category": "timeout"
            }
        except Exception as e:
            logger.error(f"Unexpected error executing {canonical_id}: {e}")
            return {"error": True, "message": str(e)}

    def normalize_error(self, tool_id: str, raw_error: str) -> str:
        """Convert low-level API/HTTP errors into clear developer-facing messages (Spec Section 26)."""
        raw_lower = raw_error.lower()
        if "403" in raw_lower or "permission" in raw_lower or "denied" in raw_lower:
            return (
                f"Permission denied while calling {tool_id}. "
                "Please verify that the configured integration has sufficient read/write permissions."
            )
        elif "401" in raw_lower or "unauthorized" in raw_lower or "token" in raw_lower:
            return (
                f"Authentication failed for {tool_id}. "
                "Please verify that your API credentials/tokens in Swytchcode or .env are valid."
            )
        elif "404" in raw_lower or "not found" in raw_lower:
            return f"Resource not found when querying {tool_id}. Please ensure the ID or path exists."
        elif "429" in raw_lower or "rate" in raw_lower:
            return f"Rate limit reached for {tool_id}. Please back off and retry shortly."
        return raw_error

    def _execute_sandbox(self, canonical_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Realistic sandbox mock data matching the exact spec for AICV-1432, PR #218, etc."""
        # 1. Jira tools
        if "jira.api.issue.get" in canonical_id or "jira.get_issue" in canonical_id:
            issue_key = inputs.get("issueIdOrKey", inputs.get("key", "AICV-1432"))
            return {
                "key": issue_key,
                "id": "10042",
                "fields": {
                    "summary": "Camera blur detection triggers prematurely on transient low-confidence frames",
                    "description": (
                        "Issue Summary:\n"
                        "In our real-time video inference service, camera blur events are triggering when single "
                        "isolated frames experience low detection confidence. The intended specification requires "
                        "that low confidence must persist for multiple consecutive frames (consecutive_frame_threshold=3) "
                        "before flagging blur. Currently, CameraBlurDetector does not track consecutive state correctly.\n\n"
                        "Expected Behavior:\n"
                        "- Require 3 consecutive frames with low confidence before triggering blur.\n"
                        "- Maintain Laplacian variance fallback.\n"
                        "- Add regression unit tests."
                    ),
                    "status": {"name": "Open", "id": "1"},
                    "priority": {"name": "High"},
                    "assignee": {"displayName": "DevPilot AI"},
                    "labels": ["computer-vision", "blur-detection", "regression"],
                    "created": "2026-09-25T14:30:00Z"
                }
            }

        elif "jira.api.issue.create" in canonical_id or "jira.create_issue" in canonical_id:
            return {
                "id": "10043",
                "key": "AICV-1433",
                "self": f"{settings.JIRA_URL}/browse/AICV-1433",
                "status": "Created"
            }

        elif "jira.issue.comments.create" in canonical_id or "jira.add_comment" in canonical_id:
            return {
                "id": "comment-5501",
                "body": inputs.get("body", "Updated by DevPilot"),
                "status": "Comment added successfully"
            }

        # 2. GitHub tools
        elif "github.repo.get" in canonical_id or "github.get_repository" in canonical_id:
            return {
                "name": "ai-inference-service",
                "full_name": f"{settings.GITHUB_OWNER}/ai-inference-service",
                "default_branch": "main",
                "language": "Python",
                "stars": 42
            }

        elif "github.pull.get" in canonical_id or "github.get_pull_request" in canonical_id:
            pr_num = inputs.get("pull_number", 218)
            return {
                "number": pr_num,
                "title": "refactor: optimize blur variance matrix calculation",
                "state": "open",
                "head": {"ref": "feat/blur-matrix-opt"},
                "base": {"ref": "main"},
                "changed_files": [
                    "inference/blur_detection.py",
                    "tests/test_blur_detection.py"
                ],
                "checks": {
                    "status": "completed",
                    "conclusion": "failure",
                    "details": "AssertionError: 0 != 3 in test_consecutive_low_confidence_frames_triggers_blur"
                }
            }

        elif "github.pull.create" in canonical_id or "github.create_pull_request" in canonical_id:
            return {
                "id": 9871,
                "number": 219,
                "title": inputs.get("title", "fix(blur-detection): enforce consecutive frame threshold"),
                "body": inputs.get("body", "Automated fix by DevPilot AI Software Engineer"),
                "html_url": f"https://github.com/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/pull/219",
                "state": "open"
            }

        # 3. Slack tools
        elif "slack.chat.postmessage" in canonical_id or "slack.send_message" in canonical_id:
            return {
                "ok": True,
                "channel": inputs.get("channel", settings.SLACK_CHANNEL),
                "ts": "1727339000.123456",
                "message": {"text": inputs.get("text", "DevPilot notification")}
            }

        elif "slack.search.message" in canonical_id or "slack.search_messages" in canonical_id:
            return {
                "ok": True,
                "messages": {
                    "matches": [
                        {
                            "text": "AICV-1432 is blocked because we had false positives firing in test environment. Needs consecutive frame state tracking.",
                            "user": "alex_cv_lead",
                            "ts": "1727321000.000100"
                        }
                    ]
                }
            }

        return {"status": "success", "canonical_id": canonical_id, "mock": True}


# Global instance
swytchcode_client = SwytchcodeClient()
