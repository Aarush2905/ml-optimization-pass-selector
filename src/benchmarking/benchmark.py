"""
Benchmarking Engine
Measures execution time with warm-up and outlier reduction,
calculates executable file size in bytes, and tracks IR size metrics.
"""

import os
import time
import subprocess
import statistics
from typing import Dict, List, Optional, Any


class BenchmarkEngine:
    """Rigorous performance measurement engine for compiled binaries."""

    def __init__(self, runs: int = 7, warmup_runs: int = 1, timeout_sec: int = 15):
        self.runs = runs
        self.warmup_runs = warmup_runs
        self.timeout_sec = timeout_sec

    def measure_binary_size(self, binary_path: str) -> int:
        """Returns the file size of the executable in bytes."""
        if not os.path.exists(binary_path):
            return 0
        return os.path.getsize(binary_path)

    def measure_ir_metrics(self, ir_path: str) -> Dict[str, int]:
        """Counts text lines and non-comment instructions in an LLVM IR file."""
        if not os.path.exists(ir_path):
            return {"ir_lines": 0, "ir_instructions": 0}

        lines_count = 0
        inst_count = 0
        with open(ir_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                lines_count += 1
                stripped = line.strip()
                if stripped and not stripped.startswith(";") and not stripped.startswith("define") and not stripped.startswith("!") and stripped != "}":
                    inst_count += 1

        return {"ir_lines": lines_count, "ir_instructions": inst_count}

    def measure_execution_time(self, binary_path: str, stdin_data: str = "") -> Dict[str, Any]:
        """
        Executes the binary across multiple iterations and computes timing statistics.
        Returns time in milliseconds (ms).
        """
        if not os.path.exists(binary_path):
            return {
                "success": False,
                "error": f"Binary not found: {binary_path}",
                "median_ms": 0.0,
                "mean_ms": 0.0,
                "min_ms": 0.0,
                "std_ms": 0.0,
                "samples_ms": []
            }

        # Warm-up runs
        for _ in range(self.warmup_runs):
            try:
                subprocess.run(
                    [binary_path],
                    input=stdin_data,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_sec
                )
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Warmup execution failed: {e}",
                    "median_ms": 0.0,
                    "mean_ms": 0.0,
                    "min_ms": 0.0,
                    "std_ms": 0.0,
                    "samples_ms": []
                }

        # Measurement runs
        times_ms: List[float] = []
        for _ in range(self.runs):
            try:
                start_ns = time.perf_counter_ns()
                res = subprocess.run(
                    [binary_path],
                    input=stdin_data,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_sec
                )
                end_ns = time.perf_counter_ns()

                if res.returncode != 0 and res.returncode < 0:
                    return {
                        "success": False,
                        "error": f"Process exited with fatal signal {res.returncode}",
                        "median_ms": 0.0,
                        "mean_ms": 0.0,
                        "min_ms": 0.0,
                        "std_ms": 0.0,
                        "samples_ms": []
                    }

                elapsed_ms = (end_ns - start_ns) / 1_000_000.0
                times_ms.append(elapsed_ms)
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": "Execution timed out during measurement",
                    "median_ms": 0.0,
                    "mean_ms": 0.0,
                    "min_ms": 0.0,
                    "std_ms": 0.0,
                    "samples_ms": []
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Measurement failed: {e}",
                    "median_ms": 0.0,
                    "mean_ms": 0.0,
                    "min_ms": 0.0,
                    "std_ms": 0.0,
                    "samples_ms": []
                }

        median_ms = statistics.median(times_ms)
        mean_ms = statistics.mean(times_ms)
        min_ms = min(times_ms)
        std_ms = statistics.stdev(times_ms) if len(times_ms) > 1 else 0.0

        return {
            "success": True,
            "error": None,
            "median_ms": round(median_ms, 4),
            "mean_ms": round(mean_ms, 4),
            "min_ms": round(min_ms, 4),
            "std_ms": round(std_ms, 4),
            "samples_ms": [round(t, 4) for t in times_ms]
        }
