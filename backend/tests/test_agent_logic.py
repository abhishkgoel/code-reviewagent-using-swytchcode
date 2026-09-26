"""Unit tests for DevPilot agent logic and state machine."""
import unittest
from backend.app.agent.executor import AgentExecutor
from backend.app.models import TaskStatus, StepStatus


class TestAgentLogic(unittest.TestCase):
    def setUp(self):
        self.executor = AgentExecutor()

    def test_investigate_command(self):
        task = self.executor.process_command("Investigate AICV-1432 and tell me what is causing the issue.")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.jira_issue, "AICV-1432")
        self.assertIsNotNone(task.root_cause)
        self.assertIn("consecutive", task.root_cause.lower())
        self.assertEqual(len(task.timeline), 4)
        for item in task.timeline:
            self.assertEqual(item.status, StepStatus.COMPLETED)

    def test_plan_command(self):
        task = self.executor.process_command("Create an implementation plan for AICV-1432.")
        self.assertEqual(task.status, TaskStatus.PLAN_READY)
        self.assertIsNotNone(task.plan)
        self.assertGreater(len(task.plan.steps), 0)
        self.assertIn("inference/blur_detection.py", task.plan.affected_files)

    def test_pr_debugging_command(self):
        task = self.executor.process_command("Why is PR #218 failing?")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.root_cause)
        self.assertIn("218", task.root_cause)
        self.assertIn("AssertionError", task.root_cause)

    def test_blocker_analysis_command(self):
        task = self.executor.process_command("Why is AICV-1432 blocked?")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.root_cause)
        self.assertIn("Blocker Analysis", task.root_cause)
        self.assertIn("Jira", task.root_cause)
        self.assertIn("Slack", task.root_cause)

    def test_daily_summary_command(self):
        task = self.executor.process_command("Give me today's engineering summary.")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.root_cause)
        self.assertIn("Daily Engineering Summary", task.root_cause)


if __name__ == "__main__":
    unittest.main()
