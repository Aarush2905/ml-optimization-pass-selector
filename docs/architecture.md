# System Architecture & Technical Specifications

**Course**: BCSE307P – Compiler Design Lab  
**Project ID**: A26  
**Project Title**: Machine-Learning-Guided Optimization Pass Selector  
**Target Environment**: Ubuntu 22.04 LTS (native or WSL2 on Windows) | LLVM / Clang 14 | Python 3.10  

---

## 1. High-Level Architecture

The framework replaces static, monolithic compiler optimization pipelines (such as `-O2` and `-O3`) with an intelligent, data-driven optimization selector that tailors pass selection and ordering to the structural characteristics of intermediate code.

```mermaid
flowchart TD
    subgraph Frontend [LLVM Frontend Stage]
        C[C Source Code .c] -->|clang -O0 -Xclang -disable-O0-optnone -S -emit-llvm| IR[Unoptimized LLVM IR .ll]
    end

    subgraph Analysis [Static Analysis Stage]
        IR --> Extractor[src/features/extractor.py]
        Extractor --> Features["25-Dimensional Feature Vector\n(Opcode counts, CFG edges, loop depth, memory ratios)"]
    end

    subgraph Intelligence [ML Optimization Decision Engine]
        Features --> MLModel[src/ml/model_wrapper.py\nRandom Forest & CART Decision Trees]
        MLModel --> BestStrat[Predicted Strategy Label]
        BestStrat --> SeqGen[src/optimization/sequence_generator.py]
        SeqGen --> Passes["Selected Pass Pipeline\n(e.g., mem2reg, instcombine, reassociate, sccp, dce)"]
    end

    subgraph Pass_Execution [LLVM Transformation Stage]
        IR --> Opt[LLVM 14 opt -passes=...]
        Passes --> Opt
        Opt --> OptIR[Optimized LLVM IR .ll]
        OptIR --> ClangLink[clang -lm]
        ClangLink --> OptBin[Optimized Native Binary]
    end

    subgraph Verification_Benchmarking [Evaluation & Verification Stage]
        IR --> RefBin[O0 Reference Binary]
        RefBin --> Verifier[src/correctness/verifier.py]
        OptBin --> Verifier
        Verifier -->|Match Verified| Bench[src/benchmarking/benchmark.py]
        Bench --> Results["Execution Time (ms)\nBinary Size (B)\nIR Instruction Count\nSpeedup vs O0/O2/O3"]
    end
```

---

## 2. Component Specifications

### 2.1 Compiler & Pass Engine (`src/llvm/`)
- **`compiler.py` (`LLVMCompiler`)**:
  - Handles invoking `clang` with `-O0 -Xclang -disable-O0-optnone -S -emit-llvm` to produce intermediate representation that is not locked by `optnone` attributes.
  - Lowers optimized `.ll` files to machine code with `llc -O2` (`-O3` for the `-O3` baseline, `--relocation-model=pic`) and links the object with clang and `-lm`. The `-O0` reference binary is compiled directly by clang with unoptimized code generation.
- **`pass_runner.py` (`PassRunner`)**:
  - Interacts with LLVM 14 `opt`.
  - Configures the **New Pass Manager** syntax: `-passes='pass1,pass2,...'` and default pipelines `default<O0>`, `default<O2>`, `default<O3>`.
  - Runs `licm` as `loop-mssa(licm)`, since LICM requires MemorySSA under the new pass manager.

### 2.2 Static IR Feature Extractor (`src/features/extractor.py`)
- Automatically parses the textual LLVM IR assembly without requiring LLVM C++ library bindings.
- Tracks Control Flow Graphs (CFG) per function to compute natural loop counts using cycle back-edge detection (`u -> v` where topological index of `v <= u`).
- Extracts 25 static program features categorized into:
  - **Magnitude features**: `instruction_count`, `basic_block_count`, `function_count`, `loop_count`.
  - **Instruction distributions**: `load_count`, `store_count`, `alloca_count`, `gep_count`, `phi_count`, `arithmetic_count`, `bitwise_count`, `cmp_count`, `call_count`, `ret_count`.
  - **Control flow**: `branch_count`, `cond_branch_count`, `uncond_branch_count`.
  - **Structural ratios**: `load_store_ratio`, `mem_to_total_ratio`, `arith_to_total_ratio`, `branch_to_bb_ratio`, `phi_to_bb_ratio`.

### 2.4 Machine Learning Engine (`src/ml/`)
- **`decision_tree.py`**: Pure Python CART Decision Tree classifier implementing Gini Impurity split criteria.
- **`random_forest.py`**: Ensemble Random Forest with bootstrap aggregating (bagging) and feature sub-sampling.
- **`model_wrapper.py`**: Serializes trained weights to JSON and provides feature vector normalization and inference.

### 2.5 Web Dashboard & REST API (`src/web/`)
- **`server.py` (`WebDashboardHandler`)**:
  - Built with standard library `http.server` (zero external pip requirements).
  - Provides REST API endpoints (`/api/optimize`, `/api/programs`, `/api/baseline_summary`, `/api/feature_summary`, `/api/dataset`, `/api/ordering`).
  - Automatically opens default browser to `http://localhost:8080`.
- **Frontend SPA (`src/web/static/`)**:
  - Interactive HTML5/CSS3/JS single page application featuring live optimization pipeline, 25-feature metrics display, results-by-program-feature breakdown, Chart.js multi-program comparisons, feature importance visualizer, and LLVM IR code diff viewer.

  - Implements permutation ordering sensitivity analysis to measure instruction reduction under different pass orders.

### 2.4 Machine Learning Engine (`src/ml/`)
- **Zero External Dependencies**: Implemented from scratch in pure Python standard library for maximum portability and viva inspectability.
- **`decision_tree.py` (`DecisionTree`)**:
  - Full CART implementation.
  - Gini Impurity for classification: $I_G(p) = 1 - \sum_{i=1}^J p_i^2$.
  - Midpoint threshold scanning across all continuous feature dimensions.
  - Recursive tree construction and ASCII tree rendering for viva examinations.
- **`random_forest.py` (`RandomForest`)**:
  - Bootstrap aggregation (Bagging) of $M=25$ trees.
  - Random feature subspace selection ($k = \sqrt{F}$).
  - Out-of-bag voting and aggregated feature importance weights.
- **`model_wrapper.py` (`PassSelectorModel`)**:
  - Unified interface with persistence (`save` / `load` to JSON).
  - Runs leave-one-out cross-validation during training and stores each program's held-out prediction (`metadata.loo_predictions`), which `plots/generate_plots.py` uses as the reported ML result.
  - Feature sub-sampling in each tree uses the forest's seeded generator, so training is reproducible.

### 2.5 Benchmarking & Correctness (`src/benchmarking/`, `src/correctness/`)
- **`benchmark.py` (`BenchmarkEngine`)**:
  - High-precision wall-clock timing using `time.perf_counter_ns()`.
  - Warm-up execution + 7 measurement iterations.
  - Computes median, mean, min, and standard deviation to filter out OS scheduler jitter.
  - Exact byte count accounting for generated binary executables.
- **`verifier.py` (`CorrectnessVerifier`)**:
  - Runs reference `-O0` binary and optimized test binary.
  - Asserts exact equality of exit code and standard output. Flags any divergence as `FAIL`.

---

## 3. Data Flow & Artifact Storage

```
data/
├── baseline_results.csv       # O0, O2, O3 metrics across all benchmark programs
├── optimization_dataset.csv   # Feature matrix + pass sequence exploration data (210 records: 30 programs x 7 strategies)
└── optimization_dataset.json  # Structured JSON dataset

models/
└── trained_selector.json      # Serialized trained model weights, thresholds, and metadata (incl. leave-one-out predictions)

results/
├── comparison_summary.csv         # Per-program performance comparison (ML vs O2 vs O3) with feature groups
└── feature_category_summary.csv   # Results aggregated by program feature group

plots/
├── execution_time_comparison.svg  # Grouped execution time visualization
├── speedup_comparison.svg         # Speedup distribution chart
└── speedup_by_<dimension>.svg     # Geomean speedup per feature group (recursion, branch depth, loops, memory, size)
```
