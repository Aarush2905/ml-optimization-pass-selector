"""
Pass Ordering & Sequence Exploration Engine
Implements beam search and ordering permutation analysis to optimize LLVM pass ordering.
Demonstrates the sensitivity of compiler performance to pass sequence order.
"""

import os
import copy
import itertools
from typing import List, Dict, Tuple, Any, Optional

from src.llvm.pass_runner import PassRunner
from src.features.extractor import IRFeatureExtractor
from src.benchmarking.benchmark import BenchmarkEngine
from src.llvm.compiler import LLVMCompiler
from src.correctness.verifier import CorrectnessVerifier


class PassOrderingExplorer:
    """Explores pass ordering configurations and searches for optimal sequences."""

    DEFAULT_PASS_CANDIDATES = [
        "instcombine",
        "simplifycfg",
        "sccp",
        "dce",
        "reassociate",
        "loop-rotate",
        "licm"
    ]

    def __init__(self):
        self.pass_runner = PassRunner()
        self.feature_extractor = IRFeatureExtractor()
        self.compiler = LLVMCompiler()
        self.benchmark = BenchmarkEngine(runs=3, warmup_runs=1)
        self.verifier = CorrectnessVerifier()

    def evaluate_order_sensitivity(
        self,
        unopt_ir_path: str,
        work_dir: str,
        passes_to_permute: List[str] = ["instcombine", "sccp", "simplifycfg"]
    ) -> List[Dict[str, Any]]:
        """
        Tests permutations of a fixed set of passes to demonstrate how order changes IR size.
        Always starts with 'mem2reg' to establish valid SSA form.
        """
        os.makedirs(work_dir, exist_ok=True)
        results: List[Dict[str, Any]] = []

        permutations = list(itertools.permutations(passes_to_permute))

        for idx, perm in enumerate(permutations):
            full_seq = ["mem2reg"] + list(perm)
            seq_str = ",".join(full_seq)
            out_ir = os.path.join(work_dir, f"perm_{idx}.ll")

            ok, msg = self.pass_runner.run_passes(unopt_ir_path, out_ir, full_seq)
            if not ok:
                continue

            metrics = self.benchmark.measure_ir_metrics(out_ir)
            results.append({
                "permutation_index": idx + 1,
                "sequence": seq_str,
                "passes": full_seq,
                "ir_instructions": metrics["ir_instructions"],
                "ir_lines": metrics["ir_lines"]
            })

        # Sort by instruction count (ascending = best reduction)
        results.sort(key=lambda r: r["ir_instructions"])
        return results

    def beam_search(
        self,
        unopt_ir_path: str,
        work_dir: str,
        candidate_pool: Optional[List[str]] = None,
        max_depth: int = 4,
        beam_width: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Heuristic Beam Search over pass sequences:
        Maintains top `beam_width` sequences at each depth level based on instruction reduction.
        """
        candidates = candidate_pool or self.DEFAULT_PASS_CANDIDATES
        os.makedirs(work_dir, exist_ok=True)

        # Level 0: Start with ["mem2reg"]
        current_beam: List[Tuple[List[str], int, str]] = []

        initial_ir = os.path.join(work_dir, "beam_init.ll")
        ok, _ = self.pass_runner.run_passes(unopt_ir_path, initial_ir, ["mem2reg"])
        if not ok:
            return []

        init_metrics = self.benchmark.measure_ir_metrics(initial_ir)
        current_beam.append((["mem2reg"], init_metrics["ir_instructions"], initial_ir))

        # Search iterations
        for depth in range(1, max_depth + 1):
            next_candidates: List[Tuple[List[str], int, str]] = []

            for seq, inst_count, ir_file in current_beam:
                for candidate_pass in candidates:
                    new_seq = seq + [candidate_pass]
                    seq_key = f"beam_d{depth}_{'_'.join(new_seq)}"
                    out_ir = os.path.join(work_dir, f"{seq_key}.ll")

                    ok, _ = self.pass_runner.run_passes(ir_file, out_ir, [candidate_pass])
                    if not ok:
                        continue

                    metrics = self.benchmark.measure_ir_metrics(out_ir)
                    next_candidates.append((new_seq, metrics["ir_instructions"], out_ir))

            if not next_candidates:
                break

            # Retain top beam_width sequences
            next_candidates.sort(key=lambda item: item[1])
            current_beam = next_candidates[:beam_width]

        # Return formatted results
        beam_results = []
        for rank, (seq, insts, ir_path) in enumerate(current_beam):
            beam_results.append({
                "rank": rank + 1,
                "sequence": ",".join(seq),
                "passes": seq,
                "ir_instructions": insts,
                "ir_path": ir_path
            })

        return beam_results
