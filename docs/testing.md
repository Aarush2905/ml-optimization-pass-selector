# Testing, Verification & Defect Log

**Course**: BCSE307P – Compiler Design Lab  
**Project ID**: A26 — Machine-Learning-Guided Optimization Pass Selector  

---

## 1. Test Strategy & Scope

The testing framework guarantees that:
1. **Compilation Integrity**: Every C program compiles cleanly to LLVM IR without `optnone` lock-in.
2. **Behavioral Correctness**: Every optimized binary produces output identical to the unoptimized `-O0` reference.
3. **Reproducible Benchmarking**: Multi-iteration timing filters out transient system noise.
4. **Module Correctness**: Unit and integration tests cover all core components.

---

## 2. Test Suites & Execution

### 2.1 Automated Test Suites
Run all tests with:
```bash
python3 -m unittest tests.unit.test_feature_extractor tests.unit.test_pass_runner tests.unit.test_ml_model tests.unit.test_verifier tests.unit.test_web_server tests.integration.test_pipeline -v
```

### 2.2 Test Results Summary

| Test Case | Module Tested | Input Type | Description | Status |
|:---|:---|:---|:---|:---:|
| `test_direct_recursion_detected` | `IRFeatureExtractor` | LLVM IR | Detects direct self-recursion via the call graph | **PASS** |
| `test_empty_ir_text` | `IRFeatureExtractor` | Boundary | Tests empty IR string handling | **PASS** |
| `test_extract_from_sample_ll` | `IRFeatureExtractor` | LLVM IR | Tests extraction on unoptimized sample loop | **PASS** |
| `test_extract_from_sample_o2_ll` | `IRFeatureExtractor` | LLVM IR | Tests constant-folded single-instruction IR | **PASS** |
| `test_feature_count` | `IRFeatureExtractor` | LLVM IR | Asserts the 25-feature vector length | **PASS** |
| `test_loop_back_edge_not_counted_twice` | `IRFeatureExtractor` | LLVM IR | Loop back-edges do not inflate `max_branch_depth` | **PASS** |
| `test_multiline_switch` | `IRFeatureExtractor` | LLVM IR | Multi-line `switch` cases become CFG edges, not instructions | **PASS** |
| `test_mutual_recursion_detected` | `IRFeatureExtractor` | LLVM IR | Detects mutual recursion across two functions | **PASS** |
| `test_nested_branch_depth` | `IRFeatureExtractor` | LLVM IR | Two nested ifs give `max_branch_depth` = 2 | **PASS** |
| `test_non_recursive_sample` | `IRFeatureExtractor` | LLVM IR | Sample loop is non-recursive with depth >= 1 | **PASS** |
| `test_nonexistent_file` | `IRFeatureExtractor` | Invalid | Asserts FileNotFoundError on missing file | **PASS** |
| `test_c_to_ir_generation` | `LLVMCompiler` | C source | Validates clang invocation and output IR | **PASS** |
| `test_invalid_input_file` | `PassRunner` | Invalid | Asserts graceful failure on missing file | **PASS** |
| `test_licm_wrapped_in_loop_mssa` | `PassRunner` | Pass list | `licm` is passed to `opt` as `loop-mssa(licm)` | **PASS** |
| `test_run_passes_instcombine` | `PassRunner` | Valid Passes | Runs `mem2reg,instcombine` via LLVM 14 `opt` | **PASS** |
| `test_run_standard_pipeline_o2` | `PassRunner` | Pipeline | Runs `default<O2>` through `opt` | **PASS** |
| `test_decision_tree_fit_predict` | `DecisionTree` | Synthetic | Fits CART tree and tests leaf classification | **PASS** |
| `test_pass_selector_wrapper_save_load` | `PassSelectorModel` | End-to-End | Verifies model training, JSON save, and load | **PASS** |
| `test_random_forest_fit_predict` | `RandomForest` | Synthetic | Fits ensemble and verifies voting probabilities | **PASS** |
| `test_run_binary_nonexistent` | `CorrectnessVerifier` | Invalid | Handles missing binary path gracefully | **PASS** |
| `test_verify_identical_binaries` | `CorrectnessVerifier` | Binaries | Verifies exit code and stdout equivalence | **PASS** |
| `test_get_baseline_summary` | `WebDashboardHandler` | HTTP | `/api/baseline_summary` returns the summary | **PASS** |
| `test_get_dataset` | `WebDashboardHandler` | HTTP | `/api/dataset` returns model metadata | **PASS** |
| `test_get_ordering` | `WebDashboardHandler` | HTTP | `/api/ordering` returns pass-order permutations | **PASS** |
| `test_get_programs` | `WebDashboardHandler` | HTTP | `/api/programs` lists the benchmark programs | **PASS** |
| `test_full_pipeline_sample` | `Integration` | Full System | End-to-end test from C to benchmark metrics | **PASS** |

**Total Tests**: 26 | **Passing**: 26 (100%) | **Failing**: 0 | **Execution Time**: ~3.4s (WSL2 Ubuntu 22.04, LLVM 14)

---

## 3. Correctness Verification Across All 30 Benchmarks

Each of the 30 benchmark programs is compiled under `-O0` (the reference), `-O2`, `-O3` and all 7 candidate strategies. Every optimized binary's exit code and standard output are compared with the `-O0` reference; a strategy that fails this check is excluded from the dataset. The ML-selected binary is one of the 7 verified strategy builds.

| Benchmark | Output Checked | -O0 Reference | -O2 Match | -O3 Match | Strategy Builds | ML Match | Overall Status |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `ackermann.c` | Stdout: `Ackermann Total: 28720` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `binary_search.c` | Stdout: `Binary Search Hits: 280000` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `bit_manipulation.c` | Stdout: `Bit Total: 1673891404` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `branch_heavy.c` | Stdout: `Branch Heavy Total: 641884` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `bubble_sort.c` | Stdout: `Checksum: 133590` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `bytecode_vm.c` | Stdout: `Bytecode VM Total: 28638100` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `collatz.c` | Stdout: `Collatz Total Steps: 1756540` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `convolution_2d.c` | Stdout: `Convolution Checksum: 1452` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `factorial.c` | Stdout: `Factorial Total: 736780000` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `fibonacci.c` | Stdout: `Fibonacci Sum: 832039` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `hash_table.c` | Stdout: `Hash Table Checksum: 785000` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `histogram.c` | Stdout: `Histogram Checksum: 309556320` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `insertion_sort.c` | Stdout: `Insertion Sort Checksum: 890402227` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `linear_search.c` | Stdout: `Linear Search Found: 620000` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `linked_list.c` | Stdout: `Linked List Checksum: 497548136` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `mandelbrot.c` | Stdout: `Mandelbrot Iterations: 1215876, Inside: 5475` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `matrix_multiply.c` | Stdout: `Matrix Sum: 25418` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `matrix_transpose.c` | Stdout: `Transpose Checksum: 10480` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `merge_sort.c` | Stdout: `Merge Sort Checksum: 874080649` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `n_queens.c` | Stdout: `N-Queens Total: 434388` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `nested_loops.c` | Stdout: `Nested Loop Accumulator: 359190000` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `permutations.c` | Stdout: `Permutations: 725760, Checksum: 592962873` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `prime_sieve.c` | Stdout: `Primes: 669, Sum: 26521` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `quick_sort.c` | Stdout: `Quick Sort Checksum: 770007951` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `roman_numerals.c` | Stdout: `Roman Checksum: 646824993, Mismatches: 0` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `sample.c` | Exit Code (`172`) | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `string_reverse.c` | Stdout: `String Checksum: 15400000` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `tower_of_hanoi.c` | Stdout: `Hanoi Moves: 4194300, Weighted: 33552400` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `triangle_classifier.c` | Stdout: `Triangles: 431880 240 0 27312 4368 624 164472 235104` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |
| `vector_dot_product.c` | Stdout: `Dot Product Result: 90623200` | Reference | PASS | PASS | 7/7 PASS | PASS | **PASS** |

**Correctness Result**: 60 / 60 `-O2`/`-O3` builds and 210 / 210 candidate-strategy builds (270 / 270 optimized builds in total, 100%) matched the `-O0` reference with zero functional divergence. The ML-selected strategy was a verified build for 30 / 30 programs.

---

## 4. Defect & Issue Log

| Defect ID | Component | Symptom / Issue | Root Cause | Fix Applied |
|:---|:---|:---|:---|:---|
| **DEF-01** | `clang` IR Gen | `opt` passes had zero effect on IR generated via `clang -O0` | Clang adds the `optnone` function attribute by default under `-O0`, instructing `opt` to skip optimizations. | Added `-Xclang -disable-O0-optnone` to IR generation flags in `src/llvm/compiler.py`. |
| **DEF-02** | `opt` Pass Runner | Error: `opt: unknown pass name 'instcombine'` when running `opt -instcombine` | LLVM 14 defaults to the New Pass Manager syntax and rejects legacy `-passname` CLI flags. | Updated `PassRunner` to use `-passes='pass1,pass2,...'` syntax compatible with LLVM 14. |
| **DEF-03** | `DecisionTree` | Zero samples assigned to right branch on discrete integer features | Threshold scanning used strictly integer intervals instead of float midpoints. | Computed float midpoints $(v_i + v_{i+1}) / 2.0$ between consecutive unique sorted feature values. |
| **DEF-04** | `RandomForest` | Python 3.10 NameError: `Tuple` was not imported in `random_forest.py` | Missing `Tuple` in typing import list. | Added `Tuple` to `from typing import ...` in `src/ml/random_forest.py`. |
| **DEF-05** | `generate_dataset`| Script failed with `ModuleNotFoundError: No module named 'src'` when invoked directly | Current working directory when executing script directly lacked project root in `sys.path`. | Added `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))` to entry point scripts. |
| **DEF-06** | `IRFeatureExtractor` | `max_branch_depth` too low for switch-heavy programs (e.g. `branch_heavy` = 1) and inflated `instruction_count` | LLVM prints `switch` case targets on separate lines; the line-based parser kept only the default target and counted each case line and `]` as an instruction. | Case lines of a multi-line `switch` are now parsed as CFG edges of the switch and not counted as instructions (`test_multiline_switch`). |
| **DEF-07** | `opt` Pass Runner | `loop_intensive` and `full_scalar_licm` never appeared in the dataset | LLVM 14's new pass manager rejects a bare `licm` (LICM requires MemorySSA), and the dataset generator skipped `opt` failures without printing them. | `PassRunner` now runs `licm` as `loop-mssa(licm)`; the dataset generator prints a warning for every failed strategy (`test_licm_wrapped_in_loop_mssa`). |
| **DEF-08** | `DecisionTree` / `RandomForest` | LOOCV accuracy changed on every training run with identical data | Per-split feature sub-sampling used Python's unseeded global `random`, so `random_state` only controlled the bootstrap. | Each tree now samples features with the forest's seeded `random.Random`, making training reproducible. |
| **DEF-09** | Web Dashboard | Dashboard always showed 20.0% CV accuracy and an empty feature-importance chart | The server read `cv_accuracy` / `feature_importances` from the top level of the model JSON instead of `metadata.loocv_accuracy` / `metadata.feature_importances`. | Server reads the `metadata` keys; the UI shows "-" when no model is available. |
| **DEF-10** | `LLVMCompiler` | `-O2`/`-O3` baselines and strategies were compiled with unoptimized machine code generation | IR was linked with `clang file.ll` without an optimization flag, so the backend ran at `-O0` for every variant. | Optimized IR is lowered with `llc -O2` (`-O3` for the `-O3` baseline) and then linked; the `-O0` reference keeps unoptimized code generation. |
| **DEF-11** | Result Reporting | Reported "ML-Selected" result was the fastest candidate on the training programs, not the model's prediction | `generate_plots.py` used the dataset's best-strategy row for each program. | ML results now use each program's leave-one-out prediction (stored as `metadata.loo_predictions`), and the best candidate is reported separately. |
