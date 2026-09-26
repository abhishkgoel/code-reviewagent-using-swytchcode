"""Tests for Swytchcode tool wrappers and error handling."""
import unittest
from backend.app.integrations.swytchcode_client import swytchcode_client
from backend.app.integrations.jira_tools import jira_tools
from backend.app.integrations.github_tools import github_tools
from backend.app.integrations.slack_tools import slack_tools


class TestIntegrations(unittest.TestCase):
    def test_jira_get_issue(self):
        issue = jira_tools.get_issue("AICV-1432")
        self.assertEqual(issue["key"], "AICV-1432")
        self.assertIn("summary", issue["fields"])

    def test_github_repo_get(self):
        repo = github_tools.get_repository()
        self.assertIn("ai-inference-service", repo["name"])

    def test_slack_send_message(self):
        res = slack_tools.send_message(text="Testing DevPilot Slack integration")
        self.assertTrue(res["ok"])

    def test_error_normalization(self):
        err_403 = swytchcode_client.normalize_error("github.pull.create", "HTTP 403 Forbidden: Resource protected")
        self.assertIn("Permission denied", err_403)
        self.assertIn("permissions", err_403.lower())

        err_401 = swytchcode_client.normalize_error("jira.api.issue.get", "HTTP 401 Unauthorized")
        self.assertIn("Authentication failed", err_401)

    def test_credential_redaction(self):
        data = {
            "token": "ghp_secret_12345",
            "safe_field": "hello world",
            "nested": {
                "api_key": "sk-secret-999",
                "name": "DevPilot"
            }
        }
        sanitized = swytchcode_client._sanitize(data)
        self.assertEqual(sanitized["token"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(sanitized["safe_field"], "hello world")


if __name__ == "__main__":
    unittest.main()
