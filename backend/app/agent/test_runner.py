"""Test execution engine for DevPilot.

Mandatory Spec Requirements (Section 12 & 18):
- Run relevant unit/regression tests after modifications.
- NEVER claim tests passed unless actually executed with a 0 exit code.
- Capture stdout, stderr, run time, and test failure summaries.
"""
import subprocess
import os
from typing import Dict, Any
from pathlib import Path
from ..config import settings


class TestRunner:
    @staticmethod
    def run_tests(test_target: str = "tests") -> Dict[str, Any]:
        """Execute automated tests in the target repository directory."""
        repo_path = settings.LOCAL_REPO_PATH
        if not repo_path.exists():
            return {
                "success": False,
                "exit_code": 1,
                "output": f"Repository directory not found at {repo_path}",
                "tests_run": 0,
                "passed": False
            }

        # Prepare environment with repo on PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_path)

        cmd = ["python3", "-m", "unittest", "discover", "-s", "tests"]
        try:
            res = subprocess.run(
                cmd,
                cwd=str(repo_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )

            passed = (res.returncode == 0)
            combined_output = (res.stdout + "\n" + res.stderr).strip()

            return {
                "success": passed,
                "exit_code": res.returncode,
                "output": combined_output,
                "cmd": " ".join(cmd),
                "passed": passed
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": 124,
                "output": "Test execution timed out after 30 seconds.",
                "passed": False
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": 1,
                "output": f"Failed to invoke test runner: {str(e)}",
                "passed": False
            }


test_runner = TestRunner()
