"""Slack tool abstraction layer.

Direct live execution via Slack Web API and Swytchcode kernel.
Honest error reporting: Never returns fake data in Live Mode.
"""
from typing import Dict, Any, List, Optional
import requests
import logging
from .swytchcode_client import swytchcode_client
from ..config import settings

logger = logging.getLogger("DevPilot.Slack")


class SlackTools:
    @staticmethod
    def _headers() -> Dict[str, str]:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if settings.SLACK_BOT_TOKEN:
            headers["Authorization"] = f"Bearer {settings.SLACK_BOT_TOKEN}"
        return headers

    @staticmethod
    def send_message(channel: Optional[str] = None, text: str = "", blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send a real message to a Slack channel."""
        target_channel = channel or settings.SLACK_CHANNEL

        if settings.is_sandbox_mode:
            return swytchcode_client.execute_tool("slack.chat.postmessage.create", {
                "channel": target_channel,
                "text": text
            }, use_sandbox=True)

        # 1. Live Slack Web API
        if settings.SLACK_BOT_TOKEN:
            try:
                url = "https://slack.com/api/chat.postMessage"
                payload = {
                    "channel": target_channel,
                    "text": text
                }
                if blocks:
                    payload["blocks"] = blocks
                res = requests.post(url, headers=SlackTools._headers(), json=payload, timeout=10)
                data = res.json()
                if data.get("ok"):
                    return data
                return {
                    "error": True,
                    "ok": False,
                    "message": f"Slack API error: {data.get('error')}",
                    "details": data
                }
            except Exception as e:
                logger.error(f"Slack send_message failed: {e}")
                return {"error": True, "ok": False, "message": str(e)}

        # 2. Try Swytchcode kernel
        return swytchcode_client.execute_tool("slack.chat.postmessage.create", {
            "channel": target_channel,
            "text": text
        })

    @staticmethod
    def send_thread_message(thread_ts: str, text: str, channel: Optional[str] = None) -> Dict[str, Any]:
        """Send a real reply to an existing Slack thread."""
        target_channel = channel or settings.SLACK_CHANNEL

        if settings.is_sandbox_mode:
            return {"ok": True, "channel": target_channel, "ts": thread_ts}

        if settings.SLACK_BOT_TOKEN:
            try:
                url = "https://slack.com/api/chat.postMessage"
                payload = {
                    "channel": target_channel,
                    "thread_ts": thread_ts,
                    "text": text
                }
                res = requests.post(url, headers=SlackTools._headers(), json=payload, timeout=10)
                return res.json()
            except Exception as e:
                return {"error": True, "message": str(e)}

        return swytchcode_client.execute_tool("slack.chat.postmessage.create", {
            "channel": target_channel,
            "thread_ts": thread_ts,
            "text": text
        })

    @staticmethod
    def search_messages(query: str) -> List[Dict[str, Any]]:
        """Search Slack workspace messages."""
        if settings.is_sandbox_mode:
            return [{
                "text": "AICV-1432 is blocked because we had false positives firing in test environment. Needs consecutive frame state tracking.",
                "user": "alex_cv_lead",
                "ts": "1727321000.000100"
            }]

        if settings.SLACK_BOT_TOKEN:
            try:
                # Use conversations.history or search.messages
                url = "https://slack.com/api/search.messages"
                params = {"query": query}
                res = requests.get(url, headers=SlackTools._headers(), params=params, timeout=10)
                data = res.json()
                if data.get("ok"):
                    return data.get("messages", {}).get("matches", [])
            except Exception as e:
                logger.error(f"Slack search failed: {e}")

        res = swytchcode_client.execute_tool("slack.search.message.list", {"query": query})
        return res.get("messages", {}).get("matches", [])


slack_tools = SlackTools()
