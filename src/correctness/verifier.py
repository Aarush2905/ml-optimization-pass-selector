"""
Correctness Verifier Module
Verifies that an optimized binary preserves exact functional behavior
against a trusted unoptimized (O0) reference execution.
"""

import os
import subprocess
from typing import Dict, Optional, Tuple, Any


class CorrectnessVerifier:
    """Checks program equivalence via execution output and return code comparison."""

    def __init__(self, timeout_sec: int = 10):
        self.timeout_sec = timeout_sec

    def run_binary(self, binary_path: str, stdin_data: str = "") -> Dict[str, Any]:
        """
        Executes a binary and captures exit code, stdout, and stderr.
        """
        if not os.path.exists(binary_path):
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Binary not found: {binary_path}",
                "error": "not_found"
            }

        try:
            res = subprocess.run(
                [binary_path],
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=self.timeout_sec
            )
            return {
                "success": True,
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "error": None
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout_sec}s",
                "error": "timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "error": "exception"
            }

    def verify(
        self,
        reference_binary: str,
        test_binary: str,
        stdin_data: str = ""
    ) -> Tuple[bool, str]:
        """
        Runs both binaries and asserts that exit code and stdout match exactly.
        """
        ref_res = self.run_binary(reference_binary, stdin_data)
        if not ref_res["success"]:
            return False, f"Reference binary failed: {ref_res['stderr']}"

        test_res = self.run_binary(test_binary, stdin_data)
        if not test_res["success"]:
            return False, f"Optimized binary failed: {test_res['stderr']}"

        if ref_res["exit_code"] != test_res["exit_code"]:
            return False, (
                f"Exit code mismatch: reference returned {ref_res['exit_code']}, "
                f"optimized returned {test_res['exit_code']}"
            )

        if ref_res["stdout"] != test_res["stdout"]:
            return False, (
                f"Stdout mismatch: expected '{ref_res['stdout']}', "
                f"got '{test_res['stdout']}'"
            )

        return True, "Outputs match exactly"
