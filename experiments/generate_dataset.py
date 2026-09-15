"""
Automated Dataset Generation Pipeline
Compiles benchmarks, extracts static IR features, applies candidate pass sequences,
benchmarks performance and correctness, and compiles the labeled training dataset.
"""

import os
import sys
import glob
import json
import csv
import tempfile
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llvm.compiler import LLVMCompiler
from src.llvm.pass_runner import PassRunner
from src.features.extractor import IRFeatureExtractor
from src.optimization.sequence_generator import SequenceGenerator
from src.benchmarking.benchmark import BenchmarkEngine
from src.correctness.verifier import CorrectnessVerifier


def generate_dataset(
    benchmark_dir: str = "tests/programs",
    output_csv: str = "data/optimization_dataset.csv",
    output_json: str = "data/optimization_dataset.json",
    runs: int = 5,
    include_permutations: bool = False
) -> List[Dict[str, Any]]:
    """
    Builds the dataset by systematically exploring pass sequences on benchmark programs.
    """
    compiler = LLVMCompiler()
    pass_runner = PassRunner()
    feature_extractor = IRFeatureExtractor()
    seq_gen = SequenceGenerator()
    benchmark_engine = BenchmarkEngine(runs=runs, warmup_runs=1)
    verifier = CorrectnessVerifier()

    work_dir = tempfile.mkdtemp(prefix="ml_dataset_gen_")

    c_files = sorted(glob.glob(os.path.join(benchmark_dir, "*.c")))
    sample_c = "tests/sample.c"
    if os.path.exists(sample_c) and sample_c not in c_files:
        c_files.append(sample_c)

    strategies = seq_gen.generate_candidate_pool(include_permutations=include_permutations)
    dataset_records: List[Dict[str, Any]] = []

    print(f"[Dataset Gen] Exploring {len(c_files)} programs across {len(strategies)} optimization strategies...")

    for c_file in c_files:
        prog_name = os.path.splitext(os.path.basename(c_file))[0]
        prog_dir = os.path.join(work_dir, prog_name)
        os.makedirs(prog_dir, exist_ok=True)

        # 1. Generate unoptimized IR
        unopt_ir = os.path.join(prog_dir, f"{prog_name}_unopt.ll")
        ok, msg = compiler.c_to_ir(c_file, unopt_ir)
        if not ok:
            print(f"  [ERROR] Could not compile {c_file} to IR: {msg}")
            continue

        # 2. Extract static features from unoptimized IR
        features = feature_extractor.extract_features(unopt_ir)

        # 3. Build reference O0 binary for correctness and baseline speedup
        ref_binary = os.path.join(prog_dir, f"{prog_name}_ref.out")
        ok, msg = compiler.ir_to_executable(unopt_ir, ref_binary)
        if not ok:
            print(f"  [ERROR] Could not compile reference binary: {msg}")
            continue

        ref_perf = benchmark_engine.measure_execution_time(ref_binary)
        ref_time = ref_perf["median_ms"]
        ref_size = benchmark_engine.measure_binary_size(ref_binary)

        program_evaluations: List[Dict[str, Any]] = []

        # 4. Evaluate each candidate pass sequence
        for strat_name, pass_list in strategies.items():
            pass_str = ",".join(pass_list)
            opt_ir = os.path.join(prog_dir, f"{prog_name}_{strat_name}.ll")
            opt_bin = os.path.join(prog_dir, f"{prog_name}_{strat_name}.out")

            ok, msg = pass_runner.run_passes(unopt_ir, opt_ir, pass_list)
            if not ok:
                continue

            ok, msg = compiler.ir_to_executable(opt_ir, opt_bin)
            if not ok:
                continue

            # Verify correctness
            is_correct, verify_msg = verifier.verify(ref_binary, opt_bin)
            if not is_correct:
                print(f"  [WARN] Strategy {strat_name} failed correctness on {prog_name}: {verify_msg}")
                continue

            # Measure performance
            perf = benchmark_engine.measure_execution_time(opt_bin)
            bin_size = benchmark_engine.measure_binary_size(opt_bin)
            ir_metrics = benchmark_engine.measure_ir_metrics(opt_ir)

            exec_time = perf["median_ms"]
            speedup = (ref_time / exec_time) if exec_time > 0 else 1.0

            eval_record = {
                "strategy": strat_name,
                "passes": pass_str,
                "execution_time_ms": exec_time,
                "binary_size_bytes": bin_size,
                "ir_lines": ir_metrics["ir_lines"],
                "ir_instructions": ir_metrics["ir_instructions"],
                "speedup_vs_o0": round(speedup, 4)
            }
            program_evaluations.append(eval_record)

        if not program_evaluations:
            continue

        # Find best strategy for this program (fastest execution time)
        best_eval = min(program_evaluations, key=lambda x: x["execution_time_ms"])
        best_strategy = best_eval["strategy"]

        print(f"  {prog_name:<18} -> Best Strategy: '{best_strategy}' ({best_eval['execution_time_ms']} ms, {best_eval['speedup_vs_o0']}x vs O0)")

        # Create records for dataset
        for ev in program_evaluations:
            record = {
                "program": prog_name,
                "strategy": ev["strategy"],
                "passes": ev["passes"],
                "execution_time_ms": ev["execution_time_ms"],
                "binary_size_bytes": ev["binary_size_bytes"],
                "ir_lines": ev["ir_lines"],
                "ir_instructions": ev["ir_instructions"],
                "speedup_vs_o0": ev["speedup_vs_o0"],
                "is_best_strategy": 1 if ev["strategy"] == best_strategy else 0,
                "best_strategy_target": best_strategy
            }
            # Append all feature columns
            for feat_k, feat_v in features.items():
                record[feat_k] = feat_v

            dataset_records.append(record)

    # 5. Save to CSV and JSON
    if dataset_records:
        os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
        keys = list(dataset_records[0].keys())
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(dataset_records)

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(dataset_records, f, indent=2)

        print(f"\n[Dataset Gen] Successfully wrote {len(dataset_records)} records to {output_csv} and {output_json}")

    return dataset_records


if __name__ == "__main__":
    generate_dataset()
