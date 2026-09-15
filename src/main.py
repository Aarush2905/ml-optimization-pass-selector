"""
ML-Guided Optimization Pass Selector — Main CLI Entry Point
Course: BCSE307P Compiler Design Lab | Project ID: A26

Usage:
  python3 src/main.py --input tests/sample.c --strategy ml
  python3 src/main.py --input tests/sample.c --explore-ordering
  python3 src/main.py --benchmark-all
  python3 src/main.py --train
"""

import os
import sys
import argparse
import tempfile
import glob
from typing import Dict, List, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llvm.compiler import LLVMCompiler
from src.llvm.pass_runner import PassRunner
from src.features.extractor import IRFeatureExtractor
from src.ml.model_wrapper import PassSelectorModel
from src.optimization.sequence_generator import SequenceGenerator
from src.optimization.ordering_search import PassOrderingExplorer
from src.benchmarking.benchmark import BenchmarkEngine
from src.correctness.verifier import CorrectnessVerifier
from src.utils.visualizer import Visualizer


def run_pipeline_for_program(
    input_path: str,
    strategy: str = "ml",
    model_path: str = "models/trained_selector.json",
    runs: int = 7,
    output_dir: str = "results"
):
    print(Visualizer.banner(
        "MACHINE-LEARNING-GUIDED OPTIMIZATION PASS SELECTOR",
        "Compiler Design Lab Project A26 — Review 2 Prototype"
    ))

    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    prog_name = os.path.splitext(os.path.basename(input_path))[0]
    is_c_source = input_path.endswith(".c")

    compiler = LLVMCompiler()
    pass_runner = PassRunner()
    feature_extractor = IRFeatureExtractor()
    seq_gen = SequenceGenerator()
    benchmark_engine = BenchmarkEngine(runs=runs, warmup_runs=1)
    verifier = CorrectnessVerifier()

    work_dir = tempfile.mkdtemp(prefix=f"opt_selector_{prog_name}_")

    # Step 1: Obtain unoptimized LLVM IR
    print(f"\n[Step 1] Preparing LLVM IR for target: {input_path}")
    if is_c_source:
        unopt_ir = os.path.join(work_dir, f"{prog_name}_unopt.ll")
        ok, msg = compiler.c_to_ir(input_path, unopt_ir)
        if not ok:
            print(f"  [ERROR] Clang compilation failed: {msg}")
            sys.exit(1)
        print(f"  Generated unoptimized IR with -disable-O0-optnone -> {unopt_ir}")
    else:
        unopt_ir = input_path
        print(f"  Using provided LLVM IR directly -> {unopt_ir}")

    # Step 2: Extract static features
    print(f"\n[Step 2] Extracting static IR features...")
    features = feature_extractor.extract_features(unopt_ir)
    print(Visualizer.format_features(features))

    # Step 3: Load ML model and predict optimal pass sequence
    print(f"\n[Step 3] Querying Machine Learning model for optimization passes...")
    ml_model = PassSelectorModel()
    if os.path.exists(model_path):
        ml_model.load(model_path)
    else:
        print(f"  [WARN] Pre-trained model {model_path} not found. Training on default dataset...")
        dataset_csv = "data/optimization_dataset.csv"
        if not os.path.exists(dataset_csv):
            print("  Dataset not found. Generating dataset first...")
            from experiments.generate_dataset import generate_dataset
            generate_dataset()
        ml_model.train(dataset_csv)
        ml_model.save(model_path)

    prediction = ml_model.predict(features)
    pred_strategy = prediction["strategy"]
    pred_passes = prediction["passes"]
    pass_str = prediction["pass_string"]

    print(f"  ML Predicted Strategy:   '{pred_strategy}' (confidence: {prediction['confidence'] * 100:.1f}%)")
    print(f"  Selected Pass Sequence:  {pass_str}")

    # Step 4: Run reference O0 baseline
    print(f"\n[Step 4] Compiling and benchmarking baselines vs ML-guided pipeline...")
    ref_binary = os.path.join(work_dir, f"{prog_name}_O0.out")
    ok, msg = compiler.ir_to_executable(unopt_ir, ref_binary)
    if not ok:
        print(f"  [ERROR] Failed to compile reference binary: {msg}")
        sys.exit(1)

    ref_perf = benchmark_engine.measure_execution_time(ref_binary)
    ref_time = ref_perf["median_ms"]
    ref_size = benchmark_engine.measure_binary_size(ref_binary)
    ref_ir_metrics = benchmark_engine.measure_ir_metrics(unopt_ir)

    # Strategies to evaluate: O0, O2, O3, and ML-selected
    evaluation_targets = [
        ("O0 (Unoptimized)", "None", unopt_ir, ref_binary, ref_time, ref_size, ref_ir_metrics, True),
    ]

    for level in ["O2", "O3"]:
        opt_ir = os.path.join(work_dir, f"{prog_name}_{level}.ll")
        opt_bin = os.path.join(work_dir, f"{prog_name}_{level}.out")
        pass_runner.run_standard_pipeline(unopt_ir, opt_ir, level=level)
        compiler.ir_to_executable(opt_ir, opt_bin)

        is_corr, _ = verifier.verify(ref_binary, opt_bin)
        perf = benchmark_engine.measure_execution_time(opt_bin)
        bin_size = benchmark_engine.measure_binary_size(opt_bin)
        ir_met = benchmark_engine.measure_ir_metrics(opt_ir)
        evaluation_targets.append((
            f"-{level} (Default)",
            f"default<{level}>",
            opt_ir,
            opt_bin,
            perf["median_ms"],
            bin_size,
            ir_met,
            is_corr
        ))

    # Evaluate ML-selected sequence
    ml_ir = os.path.join(work_dir, f"{prog_name}_ML.ll")
    ml_bin = os.path.join(work_dir, f"{prog_name}_ML.out")
    pass_runner.run_passes(unopt_ir, ml_ir, pred_passes)
    compiler.ir_to_executable(ml_ir, ml_bin)

    ml_corr, corr_msg = verifier.verify(ref_binary, ml_bin)
    ml_perf = benchmark_engine.measure_execution_time(ml_bin)
    ml_size = benchmark_engine.measure_binary_size(ml_bin)
    ml_ir_met = benchmark_engine.measure_ir_metrics(ml_ir)

    evaluation_targets.append((
        f"ML-Selected ({pred_strategy})",
        pass_str,
        ml_ir,
        ml_bin,
        ml_perf["median_ms"],
        ml_size,
        ml_ir_met,
        ml_corr
    ))

    # Step 5: Render Results Table
    table_headers = [
        "Strategy",
        "Execution Time",
        "Speedup vs O0",
        "Binary Size",
        "IR Lines",
        "Correctness"
    ]
    table_alignments = ["<", ">", ">", ">", ">", "^"]
    table_rows = []

    for name, passes, ir_p, bin_p, exec_t, b_size, ir_m, is_valid in evaluation_targets:
        speedup_str = f"{ref_time / exec_t:.2f}x" if exec_t > 0 else "1.00x"
        corr_badge = "PASS" if is_valid else "FAIL"
        table_rows.append([
            name,
            f"{exec_t:.3f} ms",
            speedup_str,
            f"{b_size} B",
            str(ir_m["ir_lines"]),
            corr_badge
        ])

    print(Visualizer.section_header("[Comparative Performance Summary]"))
    print(Visualizer.format_table(table_headers, table_rows, table_alignments))

    # Analysis Commentary
    o2_time = evaluation_targets[1][4]
    o3_time = evaluation_targets[2][4]
    ml_time = ml_perf["median_ms"]

    print("Observations:")
    if ml_time <= o2_time:
        diff = ((o2_time - ml_time) / o2_time) * 100
        print(f"  • ML pass sequence is {diff:.1f}% faster than standard -O2.")
    else:
        diff = ((ml_time - o2_time) / o2_time) * 100
        print(f"  • ML pass sequence took {diff:.1f}% longer than standard -O2.")

    if ml_time <= o3_time:
        diff = ((o3_time - ml_time) / o3_time) * 100
        print(f"  • ML pass sequence is {diff:.1f}% faster than standard -O3.")
    else:
        diff = ((ml_time - o3_time) / o3_time) * 100
        print(f"  • ML pass sequence took {diff:.1f}% longer than standard -O3.")

    print(f"  • Functional correctness verified: {ml_corr}")


def run_ordering_exploration(input_path: str):
    """Runs beam search and permutation ordering exploration on target program."""
    print(Visualizer.banner("LLVM PASS ORDERING EXPLORATION", "Beam Search & Order Permutation Analysis"))
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    prog_name = os.path.splitext(os.path.basename(input_path))[0]
    work_dir = tempfile.mkdtemp(prefix=f"ordering_{prog_name}_")

    compiler = LLVMCompiler()
    explorer = PassOrderingExplorer()

    if input_path.endswith(".c"):
        unopt_ir = os.path.join(work_dir, f"{prog_name}_unopt.ll")
        compiler.c_to_ir(input_path, unopt_ir)
    else:
        unopt_ir = input_path

    print(f"\n1. Evaluating Order Permutations for base set: [instcombine, sccp, simplifycfg]")
    perm_results = explorer.evaluate_order_sensitivity(unopt_ir, work_dir)

    headers = ["Rank", "Pass Order Sequence", "IR Instructions", "IR Lines"]
    rows = []
    for idx, r in enumerate(perm_results):
        rows.append([idx + 1, r["sequence"], r["ir_instructions"], r["ir_lines"]])
    print(Visualizer.format_table(headers, rows, ["^", "<", ">", ">"]))

    print("\n2. Running Heuristic Beam Search (Depth=3, Beam Width=2)...")
    beam_results = explorer.beam_search(unopt_ir, work_dir, max_depth=3, beam_width=2)
    b_headers = ["Rank", "Beam Search Discovered Sequence", "IR Instructions"]
    b_rows = []
    for b in beam_results:
        b_rows.append([b["rank"], b["sequence"], b["ir_instructions"]])
    print(Visualizer.format_table(b_headers, b_rows, ["^", "<", ">"]))


def run_benchmark_all():
    """Runs evaluation across all benchmarks in tests/programs and produces comparison summary."""
    from src.benchmarking.baseline_runner import BaselineRunner
    runner = BaselineRunner()
    c_files = sorted(glob.glob("tests/programs/*.c") + ["tests/sample.c"])
    print(f"Running baseline benchmark across {len(c_files)} programs...")
    all_res = []
    for cf in c_files:
        p_name = os.path.splitext(os.path.basename(cf))[0]
        res = runner.evaluate_program(cf)
        for opt in ["O0", "O2", "O3"]:
            all_res.append(res[opt])
            print(f"  {p_name:<18} [{opt}] time: {res[opt]['execution_time_ms']:.2f}ms | {res[opt]['correctness']}")
    runner.save_results_to_csv(all_res, "data/baseline_results.csv")
    print("\nSaved all results to data/baseline_results.csv")


def main():
    parser = argparse.ArgumentParser(
        description="Machine-Learning-Guided LLVM Optimization Pass Selector (Review 2)"
    )
    parser.add_argument("--input", help="Path to input C file or LLVM IR file")
    parser.add_argument("--strategy", default="ml", help="Optimization strategy (ml, o0, o2, o3)")
    parser.add_argument("--explore-ordering", action="store_true", help="Run pass ordering exploration")
    parser.add_argument("--benchmark-all", action="store_true", help="Run baselines across all benchmark programs")
    parser.add_argument("--train", action="store_true", help="Train the ML pass selector model")
    parser.add_argument("--runs", type=int, default=7, help="Number of benchmark iterations")

    args = parser.parse_args()

    if args.train:
        from src.ml.train import train_and_evaluate
        train_and_evaluate()
    elif args.benchmark_all:
        run_benchmark_all()
    elif args.explore_ordering:
        if not args.input:
            print("[ERROR] Please provide --input <file.c> with --explore-ordering")
            sys.exit(1)
        run_ordering_exploration(args.input)
    elif args.input:
        run_pipeline_for_program(args.input, strategy=args.strategy, runs=args.runs)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
