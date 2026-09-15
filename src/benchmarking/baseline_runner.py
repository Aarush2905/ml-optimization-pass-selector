"""
Baseline Runner Module
Generates and benchmarks standard LLVM optimization levels: O0, O2, and O3.
Verifies correctness against O0 reference and exports results.
"""

import os
import csv
import json
import tempfile
from typing import Dict, List, Any, Optional

from src.llvm.compiler import LLVMCompiler
from src.llvm.pass_runner import PassRunner
from src.benchmarking.benchmark import BenchmarkEngine
from src.correctness.verifier import CorrectnessVerifier


class BaselineRunner:
    """Evaluates programs under fixed LLVM baselines (O0, O2, O3)."""

    def __init__(self, work_dir: Optional[str] = None):
        self.compiler = LLVMCompiler()
        self.pass_runner = PassRunner()
        self.benchmark = BenchmarkEngine(runs=7, warmup_runs=1)
        self.verifier = CorrectnessVerifier()
        self.work_dir = work_dir or tempfile.mkdtemp(prefix="llvm_baseline_")
        os.makedirs(self.work_dir, exist_ok=True)

    def evaluate_program(self, c_source_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Takes a C program and produces O0, O2, and O3 baselines.
        Returns a dictionary mapping baseline name ('O0', 'O2', 'O3') to metrics.
        """
        prog_name = os.path.splitext(os.path.basename(c_source_path))[0]
        prog_dir = os.path.join(self.work_dir, prog_name)
        os.makedirs(prog_dir, exist_ok=True)

        unopt_ir = os.path.join(prog_dir, f"{prog_name}_unopt.ll")
        ok, msg = self.compiler.c_to_ir(c_source_path, unopt_ir)
        if not ok:
            raise RuntimeError(f"Failed to generate unoptimized IR for {c_source_path}: {msg}")

        results: Dict[str, Dict[str, Any]] = {}
        ref_binary = os.path.join(prog_dir, f"{prog_name}_O0.out")

        # 1. Evaluate O0
        ok, msg = self.compiler.ir_to_executable(unopt_ir, ref_binary)
        if not ok:
            raise RuntimeError(f"Failed to compile O0 binary: {msg}")

        o0_time = self.benchmark.measure_execution_time(ref_binary)
        o0_size = self.benchmark.measure_binary_size(ref_binary)
        o0_ir_metrics = self.benchmark.measure_ir_metrics(unopt_ir)

        results["O0"] = {
            "program": prog_name,
            "optimization": "O0",
            "execution_time_ms": o0_time["median_ms"],
            "binary_size_bytes": o0_size,
            "ir_lines": o0_ir_metrics["ir_lines"],
            "ir_instructions": o0_ir_metrics["ir_instructions"],
            "correctness": "PASS",
            "ir_path": unopt_ir,
            "binary_path": ref_binary
        }

        # 2. Evaluate O2 and O3
        for level in ["O2", "O3"]:
            opt_ir = os.path.join(prog_dir, f"{prog_name}_{level}.ll")
            opt_bin = os.path.join(prog_dir, f"{prog_name}_{level}.out")

            ok, msg = self.pass_runner.run_standard_pipeline(unopt_ir, opt_ir, level=level)
            if not ok:
                results[level] = {
                    "program": prog_name,
                    "optimization": level,
                    "execution_time_ms": 0.0,
                    "binary_size_bytes": 0,
                    "ir_lines": 0,
                    "ir_instructions": 0,
                    "correctness": f"FAIL (opt error: {msg})",
                    "ir_path": "",
                    "binary_path": ""
                }
                continue

            ok, msg = self.compiler.ir_to_executable(opt_ir, opt_bin)
            if not ok:
                results[level] = {
                    "program": prog_name,
                    "optimization": level,
                    "execution_time_ms": 0.0,
                    "binary_size_bytes": 0,
                    "ir_lines": 0,
                    "ir_instructions": 0,
                    "correctness": f"FAIL (link error: {msg})",
                    "ir_path": opt_ir,
                    "binary_path": ""
                }
                continue

            # Verify correctness against reference binary
            is_correct, verify_msg = self.verifier.verify(ref_binary, opt_bin)
            perf = self.benchmark.measure_execution_time(opt_bin)
            bin_size = self.benchmark.measure_binary_size(opt_bin)
            ir_metrics = self.benchmark.measure_ir_metrics(opt_ir)

            results[level] = {
                "program": prog_name,
                "optimization": level,
                "execution_time_ms": perf["median_ms"],
                "binary_size_bytes": bin_size,
                "ir_lines": ir_metrics["ir_lines"],
                "ir_instructions": ir_metrics["ir_instructions"],
                "correctness": "PASS" if is_correct else f"FAIL ({verify_msg})",
                "ir_path": opt_ir,
                "binary_path": opt_bin
            }

        return results

    def save_results_to_csv(self, all_results: List[Dict[str, Any]], csv_path: str) -> None:
        """Saves evaluation results list to a CSV file."""
        os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
        headers = [
            "program",
            "optimization",
            "execution_time_ms",
            "binary_size_bytes",
            "ir_lines",
            "ir_instructions",
            "correctness"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for r in all_results:
                writer.writerow(r)
