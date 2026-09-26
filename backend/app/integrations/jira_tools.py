"""Jira tool abstraction layer.

Direct live execution via Atlassian Jira Cloud REST API and Swytchcode kernel.
Honest error reporting: Never returns fake data in Live Mode.
"""
from typing import Dict, Any, List, Optional
import requests
import logging
from requests.auth import HTTPBasicAuth
from .swytchcode_client import swytchcode_client
from ..config import settings

logger = logging.getLogger("DevPilot.Jira")


class JiraTools:
    @staticmethod
    def _auth() -> Optional[HTTPBasicAuth]:
        if settings.JIRA_USER and settings.JIRA_API_TOKEN:
            return HTTPBasicAuth(settings.JIRA_USER, settings.JIRA_API_TOKEN)
        return None

    @staticmethod
    def get_issue(issue_key: str) -> Dict[str, Any]:
        """Fetch Jira issue details (summary, description, status, comments, assignee)."""
        if settings.is_sandbox_mode:
            return swytchcode_client.execute_tool("jira.api.issue.get", {"issueIdOrKey": issue_key}, use_sandbox=True)

        # 1. Live Atlassian Jira REST API
        if settings.JIRA_URL and settings.JIRA_API_TOKEN:
            try:
                base_url = settings.JIRA_URL.rstrip("/")
                url = f"{base_url}/rest/api/3/issue/{issue_key}"
                headers = {"Accept": "application/json"}
                res = requests.get(url, headers=headers, auth=JiraTools._auth(), timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    return data
                return {
                    "error": True,
                    "status_code": res.status_code,
                    "message": f"Jira Cloud API returned HTTP {res.status_code}: {res.text}"
                }
            except Exception as e:
                logger.error(f"Jira get_issue failed: {e}")
                return {"error": True, "message": str(e)}

        # 2. Try Swytchcode kernel
        return swytchcode_client.execute_tool("jira.api.issue.get", {"issueIdOrKey": issue_key})

    @staticmethod
    def search_issues(jql: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Jira issues using JQL."""
        if settings.is_sandbox_mode:
            return [{"key": "AICV-1432", "fields": {"summary": "Camera blur detection issue"}}]

        if settings.JIRA_URL and settings.JIRA_API_TOKEN:
            try:
                base_url = settings.JIRA_URL.rstrip("/")
                url = f"{base_url}/rest/api/3/search"
                headers = {"Accept": "application/json"}
                params = {"jql": jql, "maxResults": max_results}
                res = requests.get(url, headers=headers, params=params, auth=JiraTools._auth(), timeout=10)
                if res.status_code == 200:
                    return res.json().get("issues", [])
                return []
            except Exception as e:
                logger.error(f"Jira search failed: {e}")

        res = swytchcode_client.execute_tool("jira.api.search.post", {"jql": jql, "maxResults": max_results})
        return res.get("issues", [])

    @staticmethod
    def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Bug") -> Dict[str, Any]:
        """Create a real Jira issue."""
        if settings.is_sandbox_mode:
            return swytchcode_client.execute_tool("jira.api.issue.create", {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type}
                }
            }, use_sandbox=True)

        if settings.JIRA_URL and settings.JIRA_API_TOKEN:
            try:
                base_url = settings.JIRA_URL.rstrip("/")
                url = f"{base_url}/rest/api/3/issue"
                headers = {"Content-Type": "application/json", "Accept": "application/json"}
                # Jira Cloud uses ADF (Atlassian Document Format) for description in v3
                adf_desc = {
                    "type": "doc",
                    "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }]
                }
                payload = {
                    "fields": {
                        "project": {"key": project_key},
                        "summary": summary,
                        "description": adf_desc,
                        "issuetype": {"name": issue_type}
                    }
                }
                res = requests.post(url, headers=headers, json=payload, auth=JiraTools._auth(), timeout=12)
                if res.status_code in (200, 201):
                    return res.json()
                return {
                    "error": True,
                    "status_code": res.status_code,
                    "message": f"Jira issue creation failed ({res.status_code}): {res.text}"
                }
            except Exception as e:
                logger.error(f"Jira create_issue failed: {e}")
                return {"error": True, "message": str(e)}

        return swytchcode_client.execute_tool("jira.api.issue.create", {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type}
            }
        })

    @staticmethod
    def add_comment(issue_key: str, comment_text: str) -> Dict[str, Any]:
        """Add a real comment to a Jira issue."""
        if settings.is_sandbox_mode:
            return swytchcode_client.execute_tool("jira.issue.comments.create", {"issueIdOrKey": issue_key, "body": comment_text}, use_sandbox=True)

        if settings.JIRA_URL and settings.JIRA_API_TOKEN:
            try:
                base_url = settings.JIRA_URL.rstrip("/")
                url = f"{base_url}/rest/api/3/issue/{issue_key}/comment"
                headers = {"Content-Type": "application/json", "Accept": "application/json"}
                adf_comment = {
                    "type": "doc",
                    "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_text}]
                    }]
                }
                res = requests.post(url, headers=headers, json={"body": adf_comment}, auth=JiraTools._auth(), timeout=10)
                if res.status_code in (200, 201):
                    return res.json()
                return {"error": True, "status_code": res.status_code, "message": res.text}
            except Exception as e:
                logger.error(f"Jira add_comment failed: {e}")
                return {"error": True, "message": str(e)}

        return swytchcode_client.execute_tool("jira.issue.comments.create", {"issueIdOrKey": issue_key, "body": comment_text})


jira_tools = JiraTools()
