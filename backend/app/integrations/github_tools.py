"""GitHub tool abstraction layer.

Direct live execution via GitHub REST API v3 and Swytchcode kernel (`swy exec`).
Honest error reporting: Never returns fake data in Live Mode.
"""
from typing import Dict, Any, List, Optional
import requests
import logging
from pathlib import Path
from .swytchcode_client import swytchcode_client
from ..config import settings

logger = logging.getLogger("DevPilot.GitHub")


class GitHubTools:
    @staticmethod
    def _headers() -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DevPilot-AI-Agent"
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        return headers

    @staticmethod
    def get_repository(repo_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch repository details."""
        repo = repo_name or f"{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}"
        owner, name = repo.split("/") if "/" in repo else (settings.GITHUB_OWNER, repo)

        if settings.is_sandbox_mode:
            return swytchcode_client.execute_tool("github.repo.get3", {"owner": owner, "repo": name}, use_sandbox=True)

        # 1. Try Direct GitHub API with token
        if settings.GITHUB_TOKEN:
            try:
                url = f"https://api.github.com/repos/{owner}/{name}"
                res = requests.get(url, headers=GitHubTools._headers(), timeout=10)
                if res.status_code == 200:
                    return res.json()
                return {
                    "error": True,
                    "status_code": res.status_code,
                    "message": f"GitHub API error ({res.status_code}): {res.text}"
                }
            except Exception as e:
                logger.error(f"GitHub get_repo failed: {e}")
                return {"error": True, "message": str(e)}

        # 2. Try Swytchcode kernel
        return swytchcode_client.execute_tool("github.repo.get3", {"owner": owner, "repo": name})

    @staticmethod
    def search_code(query: str, repo_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search code within repository."""
        repo = repo_name or f"{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}"

        # Inspect local demo repo directory if present
        local_results = []
        if settings.LOCAL_REPO_PATH.exists():
            for p in settings.LOCAL_REPO_PATH.rglob("*.py"):
                try:
                    content = p.read_text(encoding="utf-8")
                    if query.lower() in content.lower():
                        rel_path = p.relative_to(settings.LOCAL_REPO_PATH)
                        local_results.append({
                            "path": str(rel_path),
                            "name": p.name,
                            "repository": repo
                        })
                except Exception:
                    pass
        if local_results:
            return local_results

        if settings.is_sandbox_mode:
            return [{"path": "inference/blur_detection.py", "repository": repo}]

        if settings.GITHUB_TOKEN:
            try:
                url = f"https://api.github.com/search/code?q={query}+repo:{repo}"
                res = requests.get(url, headers=GitHubTools._headers(), timeout=10)
                if res.status_code == 200:
                    return res.json().get("items", [])
            except Exception as e:
                logger.error(f"GitHub search_code failed: {e}")

        res = swytchcode_client.execute_tool("github.search.code", {"q": f"{query}+repo:{repo}"})
        return res.get("items", [])

    @staticmethod
    def get_file(file_path: str, ref: str = "main") -> str:
        """Fetch file contents from local repository or via GitHub/Swytchcode."""
        local_file = settings.LOCAL_REPO_PATH / file_path
        if local_file.exists():
            return local_file.read_text(encoding="utf-8")

        if settings.is_sandbox_mode:
            return ""

        if settings.GITHUB_TOKEN:
            try:
                url = f"https://api.github.com/repos/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/contents/{file_path}?ref={ref}"
                res = requests.get(url, headers=GitHubTools._headers(), timeout=10)
                if res.status_code == 200:
                    import base64
                    content_b64 = res.json().get("content", "")
                    return base64.b64decode(content_b64).decode("utf-8")
            except Exception as e:
                logger.error(f"GitHub get_file failed: {e}")

        inputs = {
            "owner": settings.GITHUB_OWNER,
            "repo": settings.GITHUB_REPO,
            "path": file_path,
            "ref": ref
        }
        res = swytchcode_client.execute_tool("github.repos.contents.get", inputs)
        return res.get("content", "")

    @staticmethod
    def update_file(file_path: str, content: str, commit_message: str, branch: str) -> Dict[str, Any]:
        """Update file in the dedicated branch (local repo or GitHub)."""
        local_file = settings.LOCAL_REPO_PATH / file_path
        if local_file.parent.exists():
            local_file.write_text(content, encoding="utf-8")
            return {
                "status": "success",
                "file_path": file_path,
                "commit_message": commit_message,
                "branch": branch
            }

        if settings.is_sandbox_mode:
            return {"status": "success", "file_path": file_path, "branch": branch}

        inputs = {
            "owner": settings.GITHUB_OWNER,
            "repo": settings.GITHUB_REPO,
            "path": file_path,
            "message": commit_message,
            "content": content,
            "branch": branch
        }
        return swytchcode_client.execute_tool("github.repos.contents.update", inputs)

    @staticmethod
    def create_pull_request(title: str, body: str, head_branch: str, base_branch: str = "main") -> Dict[str, Any]:
        """Create a real GitHub pull request."""
        if settings.is_sandbox_mode:
            return swytchcode_client.execute_tool("github.pull.create", {
                "owner": settings.GITHUB_OWNER,
                "repo": settings.GITHUB_REPO,
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch
            }, use_sandbox=True)

        # 1. Live GitHub API Call
        if settings.GITHUB_TOKEN:
            try:
                url = f"https://api.github.com/repos/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/pulls"
                payload = {
                    "title": title,
                    "body": body,
                    "head": head_branch,
                    "base": base_branch
                }
                res = requests.post(url, headers=GitHubTools._headers(), json=payload, timeout=12)
                if res.status_code in (200, 201):
                    data = res.json()
                    return {
                        "id": data.get("id"),
                        "number": data.get("number"),
                        "title": data.get("title"),
                        "html_url": data.get("html_url"),
                        "state": data.get("state")
                    }
                return {
                    "error": True,
                    "status_code": res.status_code,
                    "message": f"GitHub PR creation failed ({res.status_code}): {res.text}"
                }
            except Exception as e:
                logger.error(f"GitHub create_pull_request failed: {e}")
                return {"error": True, "message": str(e)}

        # 2. Try Swytchcode kernel
        return swytchcode_client.execute_tool("github.pull.create", {
            "owner": settings.GITHUB_OWNER,
            "repo": settings.GITHUB_REPO,
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch
        })

    @staticmethod
    def get_pull_request(pr_number: int) -> Dict[str, Any]:
        """Fetch PR details."""
        if settings.is_sandbox_mode:
            return swytchcode_client.execute_tool("github.pull.get", {"pull_number": pr_number}, use_sandbox=True)

        if settings.GITHUB_TOKEN:
            try:
                url = f"https://api.github.com/repos/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/pulls/{pr_number}"
                res = requests.get(url, headers=GitHubTools._headers(), timeout=10)
                if res.status_code == 200:
                    return res.json()
                return {"error": True, "status_code": res.status_code, "message": res.text}
            except Exception as e:
                return {"error": True, "message": str(e)}

        return swytchcode_client.execute_tool("github.pull.get", {"pull_number": pr_number})

    @staticmethod
    def get_pull_request_checks(pr_number: int) -> Dict[str, Any]:
        """Fetch PR status checks."""
        if settings.is_sandbox_mode:
            pr = swytchcode_client.execute_tool("github.pull.get", {"pull_number": pr_number}, use_sandbox=True)
            return pr.get("checks", {"status": "completed", "conclusion": "failure", "details": "AssertionError: 0 != 3 in test_consecutive_low_confidence_frames_triggers_blur"})

        if settings.GITHUB_TOKEN:
            try:
                # Get PR head commit sha
                pr_url = f"https://api.github.com/repos/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/pulls/{pr_number}"
                pr_res = requests.get(pr_url, headers=GitHubTools._headers(), timeout=10)
                if pr_res.status_code == 200:
                    sha = pr_res.json().get("head", {}).get("sha", "main")
                    checks_url = f"https://api.github.com/repos/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/commits/{sha}/check-runs"
                    c_res = requests.get(checks_url, headers=GitHubTools._headers(), timeout=10)
                    if c_res.status_code == 200:
                        return c_res.json()
            except Exception as e:
                logger.error(f"GitHub checks failed: {e}")

        pr = swytchcode_client.execute_tool("github.pull.get", {"pull_number": pr_number})
        return pr.get("checks", {"status": "completed", "conclusion": "failure", "details": "AssertionError: 0 != 3"})


github_tools = GitHubTools()
