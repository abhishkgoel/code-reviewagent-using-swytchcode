"""End-to-End workflow tests for DevPilot AI Software Engineer."""
import unittest
from backend.app.agent.executor import AgentExecutor
from backend.app.models import TaskStatus, StepStatus


class TestE2EWorkflow(unittest.TestCase):
    def test_fix_workflow_with_rejection(self):
        executor = AgentExecutor()
        task = executor.process_command("Fix AICV-1432")
        self.assertEqual(task.status, TaskStatus.WAITING_FOR_APPROVAL)
        self.assertIsNotNone(task.plan)
        self.assertIsNotNone(task.diff)

        # Reject the change
        rejected_task = executor.apply_approval_decision(task.task_id, "reject", "Need further discussion")
        self.assertEqual(rejected_task.status, TaskStatus.REJECTED)
        self.assertIsNone(rejected_task.pull_request)

    def test_fix_workflow_with_approval_and_full_execution(self):
        executor = AgentExecutor()
        # 1. Start fix command
        task = executor.process_command("Fix AICV-1432")
        self.assertEqual(task.status, TaskStatus.WAITING_FOR_APPROVAL)

        # 2. Grant approval
        completed_task = executor.apply_approval_decision(task.task_id, "approve", "Approved by lead engineer")
        self.assertEqual(completed_task.status, TaskStatus.COMPLETED)

        # 3. Verify downstream artifacts
        self.assertIsNotNone(completed_task.test_results)
        self.assertTrue(completed_task.test_results["passed"])
        self.assertIsNotNone(completed_task.pull_request)
        self.assertEqual(completed_task.pull_request.number, 219)
        self.assertIsNotNone(completed_task.slack_notification)

        # 4. Check timeline steps
        for step in completed_task.timeline:
            self.assertEqual(step.status, StepStatus.COMPLETED, f"Step '{step.title}' did not complete successfully")


if __name__ == "__main__":
    unittest.main()
