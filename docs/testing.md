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
python3 -m unittest discover -s tests/unit -p "test_*.py" -v
python3 -m unittest discover -s tests/integration -p "test_*.py" -v
```

### 2.2 Test Results Summary

| Test Case | Module Tested | Input Type | Description | Status |
|:---|:---|:---|:---|:---:|
| `test_extract_from_sample_ll` | `IRFeatureExtractor` | LLVM IR | Tests extraction on unoptimized sample loop | **PASS** |
| `test_extract_from_sample_o2_ll`| `IRFeatureExtractor` | LLVM IR | Tests constant-folded single-instruction IR | **PASS** |
| `test_empty_ir_text` | `IRFeatureExtractor` | Boundary | Tests empty IR string handling | **PASS** |
| `test_nonexistent_file` | `IRFeatureExtractor` | Invalid | Asserts FileNotFoundError on missing file | **PASS** |
| `test_c_to_ir_generation` | `LLVMCompiler` | C source | Validates clang invocation and output IR | **PASS** |
| `test_invalid_input_file` | `PassRunner` | Invalid | Asserts graceful failure on missing file | **PASS** |
| `test_run_passes_instcombine` | `PassRunner` | Valid Passes | Runs `mem2reg,instcombine` via LLVM 14 `opt` | **PASS** |
| `test_run_standard_pipeline_o2` | `PassRunner` | Pipeline | Runs `default<O2>` through `opt` | **PASS** |
| `test_decision_tree_fit_predict`| `DecisionTree` | Synthetic | Fits CART tree and tests leaf classification | **PASS** |
| `test_random_forest_fit_predict`| `RandomForest` | Synthetic | Fits ensemble and verifies voting probabilities | **PASS** |
| `test_pass_selector_wrapper` | `PassSelectorModel`| End-to-End | Verifies model training, JSON save, and load | **PASS** |
| `test_run_binary_nonexistent` | `CorrectnessVerifier` | Invalid | Handles missing binary path gracefully | **PASS** |
| `test_verify_identical_binaries`| `CorrectnessVerifier` | Binaries | Verifies exit code and stdout equivalence | **PASS** |
| `test_full_pipeline_sample` | `Integration` | Full System | End-to-end test from C to benchmark metrics | **PASS** |

**Total Tests**: 14 | **Passing**: 14 (100%) | **Failing**: 0 | **Execution Time**: ~0.45s

---

## 3. Correctness Verification Across All 15 Benchmarks

Each of the 15 benchmark programs was compiled and executed under 4 distinct optimization regimes (`-O0`, `-O2`, `-O3`, and `ML-Selected`), resulting in 60 total compilations and executions.

| Benchmark | Output Checked | -O0 Reference | -O2 Match | -O3 Match | ML Match | Overall Status |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `sample.c` | Exit Code (`172`) | Reference | PASS | PASS | PASS | **PASS** |
| `binary_search.c` | Stdout: `Binary Search Hits: 280000` | Reference | PASS | PASS | PASS | **PASS** |
| `bit_manipulation.c` | Stdout: `Bit Total: 1673891404` | Reference | PASS | PASS | PASS | **PASS** |
| `branch_heavy.c` | Stdout: `Branch Heavy Total: 641884` | Reference | PASS | PASS | PASS | **PASS** |
| `bubble_sort.c` | Stdout: `Checksum: 133590` | Reference | PASS | PASS | PASS | **PASS** |
| `collatz.c` | Stdout: `Collatz Total Steps: 1756540` | Reference | PASS | PASS | PASS | **PASS** |
| `factorial.c` | Stdout: `Factorial Total: 736780000` | Reference | PASS | PASS | PASS | **PASS** |
| `fibonacci.c` | Stdout: `Fibonacci Sum: 832039` | Reference | PASS | PASS | PASS | **PASS** |
| `hash_table.c` | Stdout: `Hash Table Checksum: 785000` | Reference | PASS | PASS | PASS | **PASS** |
| `linear_search.c` | Stdout: `Linear Search Found: 620000` | Reference | PASS | PASS | PASS | **PASS** |
| `matrix_multiply.c`| Stdout: `Matrix Sum: 25418` | Reference | PASS | PASS | PASS | **PASS** |
| `nested_loops.c` | Stdout: `Nested Loop Accumulator: 359190000` | Reference | PASS | PASS | PASS | **PASS** |
| `prime_sieve.c` | Stdout: `Primes: 669, Sum: 26521` | Reference | PASS | PASS | PASS | **PASS** |
| `string_reverse.c` | Stdout: `String Checksum: 15400000` | Reference | PASS | PASS | PASS | **PASS** |
| `vector_dot_product.c`| Stdout: `Dot Product Result: 90623200` | Reference | PASS | PASS | PASS | **PASS** |

**Correctness Result**: 60 / 60 executions (100%) maintained perfect semantic equivalence with zero functional divergence.

---

## 4. Defect & Issue Log

| Defect ID | Component | Symptom / Issue | Root Cause | Fix Applied |
|:---|:---|:---|:---|:---|
| **DEF-01** | `clang` IR Gen | `opt` passes had zero effect on IR generated via `clang -O0` | Clang adds the `optnone` function attribute by default under `-O0`, instructing `opt` to skip optimizations. | Added `-Xclang -disable-O0-optnone` to IR generation flags in `src/llvm/compiler.py`. |
| **DEF-02** | `opt` Pass Runner | Error: `opt: unknown pass name 'instcombine'` when running `opt -instcombine` | LLVM 14 defaults to the New Pass Manager syntax and rejects legacy `-passname` CLI flags. | Updated `PassRunner` to use `-passes='pass1,pass2,...'` syntax compatible with LLVM 14. |
| **DEF-03** | `DecisionTree` | Zero samples assigned to right branch on discrete integer features | Threshold scanning used strictly integer intervals instead of float midpoints. | Computed float midpoints $(v_i + v_{i+1}) / 2.0$ between consecutive unique sorted feature values. |
| **DEF-04** | `RandomForest` | Python 3.10 NameError: `Tuple` was not imported in `random_forest.py` | Missing `Tuple` in typing import list. | Added `Tuple` to `from typing import ...` in `src/ml/random_forest.py`. |
| **DEF-05** | `generate_dataset`| Script failed with `ModuleNotFoundError: No module named 'src'` when invoked directly | Current working directory when executing script directly lacked project root in `sys.path`. | Added `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))` to entry point scripts. |
