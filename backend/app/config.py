"""Configuration settings for DevPilot AI Software Engineer."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load local .env if present
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings:
    # Service
    SERVICE_NAME: str = "DevPilot"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Swytchcode
    SWYTCHCODE_API_KEY: str = os.getenv("SWYTCHCODE_API_KEY", "")
    SWYTCHCODE_CLI_PATH: str = os.getenv("SWYTCHCODE_CLI_PATH", "swy")
    SWYTCHCODE_WORKSPACE_DIR: Path = Path(os.getenv("SWYTCHCODE_WORKSPACE_DIR", str(Path(__file__).resolve().parent.parent.parent)))

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_OWNER: str = os.getenv("GITHUB_OWNER", "acme-corp")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "ai-inference-service")
    GITHUB_DEFAULT_BRANCH: str = os.getenv("GITHUB_DEFAULT_BRANCH", "main")

    # Jira
    JIRA_URL: str = os.getenv("JIRA_URL", "https://acme-corp.atlassian.net")
    JIRA_USER: str = os.getenv("JIRA_USER", "developer@acme.corp")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "AICV")

    # Slack
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#dev-alerts")

    # Target repository local path for automated verification and editing
    LOCAL_REPO_PATH: Path = SWYTCHCODE_WORKSPACE_DIR / "ai-inference-service"

    # Execution Mode: "live" (calls real SwytchCode / APIs) or "sandbox"
    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "auto")

    @property
    def is_sandbox_mode(self) -> bool:
        if self.EXECUTION_MODE == "sandbox":
            return True
        if self.EXECUTION_MODE == "live":
            return False
        # Auto-detect: if external tokens or connected accounts exist, default to live
        return not bool(self.SWYTCHCODE_API_KEY or self.GITHUB_TOKEN or self.JIRA_API_TOKEN or self.SLACK_BOT_TOKEN)

    def set_mode(self, mode: str):
        if mode in ("live", "sandbox", "auto"):
            self.EXECUTION_MODE = mode


settings = Settings()
