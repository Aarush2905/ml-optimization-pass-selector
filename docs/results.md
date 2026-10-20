# Experimental Results & Performance Analysis

**Course**: BCSE307P – Compiler Design Lab
**Project ID**: A26 — Machine-Learning-Guided Optimization Pass Selector

---

## 1. Experimental Methodology & Rigor

All measurements presented in this document were collected directly on actual hardware execution:
- **Host**: WSL2 Ubuntu 22.04 LTS on Windows 11 (x86-64).
- **Toolchain**: clang / LLVM 14 (Ubuntu 22.04 `clang-14` and `llvm-14` packages). IR pass sequences are applied with `opt` (new pass manager); optimized IR is lowered to machine code with `llc -O2` (`-O3` for the `-O3` baseline). The `-O0` reference uses unoptimized code generation.
- **Benchmark Suite**: 30 programs (29 in `tests/programs/` plus `tests/sample.c`), covering recursion, deep branching, loops, memory-bound and floating-point workloads.
- **Candidate Strategies**: 7 named pass pipelines (`scalar_cleanup`, `arithmetic_constant`, `loop_intensive`, `memory_redundancy`, `code_size_dce`, `full_scalar_licm`, `tailcall_simplify`), all measured on every program (210 dataset records).
- **Timing Engine**: 1 warm-up run followed by 7 measured runs for each `-O0`/`-O2`/`-O3` baseline and 5 measured runs for each candidate strategy.
- **Statistical Aggregation**: Median execution time per configuration; geometric means when aggregating speedups across programs.
- **ML Evaluation (leave-one-out)**: the "ML" result for a program is the strategy predicted by a Random Forest trained on the other 29 programs, so every ML number is for a program the model has not seen. "Best Candidate" is the fastest of the 7 strategies for that program (the upper bound of the candidate pool).
- **Zero Fabrication**: No benchmark numbers or speedup claims are hardcoded or simulated. All figures come from `data/baseline_results.csv`, `data/optimization_dataset.csv`, `results/comparison_summary.csv` and `results/feature_category_summary.csv`.

---

## 2. Benchmark Evaluation Table

The following table summarizes the performance across all 30 benchmark programs, sorted by ML speedup over `-O2`:

| Benchmark | Program Nature | -O0 (ms) | -O2 (ms) | -O3 (ms) | ML (ms) | ML Strategy (LOO) | Best Candidate | Speedup vs -O2 | Speedup vs -O3 | ML Beats O2? | ML Beats O3? |
|:---|:---|:---:|:---:|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|
| `roman_numerals` | Long if-else chains | 20.01 | 12.11 | 10.60 | 6.10 | `code_size_dce` | `code_size_dce` | **1.99x** | **1.74x** | **YES** | **YES** |
| `triangle_classifier` | Deeply nested ifs | 6.52 | 4.09 | 3.98 | 2.30 | `code_size_dce` | `code_size_dce` | **1.78x** | **1.73x** | **YES** | **YES** |
| `string_reverse` | Pointer manipulation | 20.35 | 5.60 | 5.81 | 3.23 | `tailcall_simplify` | `scalar_cleanup` | **1.73x** | **1.80x** | **YES** | **YES** |
| `fibonacci` | Double recursion | 6.68 | 3.77 | 3.98 | 2.21 | `tailcall_simplify` | `tailcall_simplify` | **1.70x** | **1.80x** | **YES** | **YES** |
| `matrix_transpose` | Strided memory access | 27.20 | 11.89 | 12.22 | 7.48 | `loop_intensive` | `loop_intensive` | **1.59x** | **1.63x** | **YES** | **YES** |
| `quick_sort` | Recursive partitioning | 25.29 | 15.47 | 16.13 | 9.79 | `full_scalar_licm` | `scalar_cleanup` | **1.58x** | **1.65x** | **YES** | **YES** |
| `factorial` | Recursion arithmetic | 20.38 | 4.19 | 4.86 | 2.69 | `tailcall_simplify` | `tailcall_simplify` | **1.56x** | **1.80x** | **YES** | **YES** |
| `tower_of_hanoi` | Recursive calls | 40.49 | 26.58 | 28.00 | 17.61 | `tailcall_simplify` | `tailcall_simplify` | **1.51x** | **1.59x** | **YES** | **YES** |
| `n_queens` | Recursive backtracking | 13.44 | 6.68 | 6.61 | 4.45 | `loop_intensive` | `code_size_dce` | **1.50x** | **1.49x** | **YES** | **YES** |
| `insertion_sort` | Shifting inner loop | 20.76 | 7.34 | 7.23 | 4.93 | `loop_intensive` | `loop_intensive` | **1.49x** | **1.47x** | **YES** | **YES** |
| `mandelbrot` | Floating-point loop | 11.27 | 4.64 | 5.27 | 3.14 | `full_scalar_licm` | `code_size_dce` | **1.48x** | **1.68x** | **YES** | **YES** |
| `linked_list` | Pointer chasing | 90.82 | 97.68 | 106.53 | 67.62 | `scalar_cleanup` | `full_scalar_licm` | **1.44x** | **1.57x** | **YES** | **YES** |
| `sample` | Arithmetic loop | 1.05 | 0.77 | 0.66 | 0.55 | `tailcall_simplify` | `code_size_dce` | **1.41x** | **1.21x** | **YES** | **YES** |
| `nested_loops` | Compute-heavy loops | 97.31 | 62.66 | 58.03 | 45.00 | `tailcall_simplify` | `arithmetic_constant` | **1.39x** | **1.29x** | **YES** | **YES** |
| `linear_search` | Linear traversal | 120.80 | 50.07 | 47.92 | 36.29 | `full_scalar_licm` | `tailcall_simplify` | **1.38x** | **1.32x** | **YES** | **YES** |
| `histogram` | Indirect array updates | 5.63 | 3.40 | 3.71 | 2.65 | `loop_intensive` | `tailcall_simplify` | **1.28x** | **1.40x** | **YES** | **YES** |
| `bubble_sort` | Nested loop / memory | 1.81 | 1.36 | 1.11 | 1.07 | `loop_intensive` | `loop_intensive` | **1.27x** | **1.03x** | **YES** | **YES** |
| `prime_sieve` | Array sieve / branches | 1.23 | 0.88 | 0.80 | 0.75 | `tailcall_simplify` | `full_scalar_licm` | **1.17x** | **1.06x** | **YES** | **YES** |
| `bytecode_vm` | Switch-dispatch interpreter | 10.73 | 10.49 | 10.23 | 9.34 | `loop_intensive` | `tailcall_simplify` | **1.12x** | **1.10x** | **YES** | **YES** |
| `merge_sort` | Recursive divide & conquer | 33.31 | 14.74 | 15.38 | 13.29 | `code_size_dce` | `memory_redundancy` | **1.11x** | **1.16x** | **YES** | **YES** |
| `branch_heavy` | Multi-case switch | 2.80 | 2.44 | 1.65 | 2.22 | `loop_intensive` | `arithmetic_constant` | **1.10x** | 0.74x | **YES** | NO |
| `convolution_2d` | 2D stencil loops | 13.97 | 1.55 | 1.73 | 1.46 | `loop_intensive` | `loop_intensive` | **1.06x** | **1.19x** | **YES** | **YES** |
| `vector_dot_product` | Vector arithmetic | 67.99 | 16.85 | 13.51 | 16.14 | `tailcall_simplify` | `memory_redundancy` | **1.04x** | 0.84x | **YES** | NO |
| `bit_manipulation` | Bit shifts / masks | 9.71 | 2.74 | 1.24 | 3.03 | `tailcall_simplify` | `full_scalar_licm` | 0.90x | 0.41x | NO | NO |
| `collatz` | Modulo & while loops | 339.26 | 59.22 | 54.15 | 66.81 | `tailcall_simplify` | `loop_intensive` | 0.89x | 0.81x | NO | NO |
| `hash_table` | Hashing & probe loops | 5.18 | 3.68 | 2.91 | 4.31 | `loop_intensive` | `arithmetic_constant` | 0.85x | 0.68x | NO | NO |
| `binary_search` | Branch-heavy search | 83.69 | 21.79 | 24.56 | 28.79 | `loop_intensive` | `full_scalar_licm` | 0.76x | 0.85x | NO | NO |
| `matrix_multiply` | Triple-nested loops | 2.67 | 1.11 | 1.19 | 1.59 | `code_size_dce` | `loop_intensive` | 0.69x | 0.75x | NO | NO |
| `permutations` | Recursive enumeration | 35.24 | 8.83 | 8.64 | 16.32 | `full_scalar_licm` | `loop_intensive` | 0.54x | 0.53x | NO | NO |
| `ackermann` | Deep recursion | 41.12 | 2.44 | 2.06 | 24.62 | `tailcall_simplify` | `tailcall_simplify` | 0.10x | 0.08x | NO | NO |

---

## 3. Key Findings & Detailed Analysis

### 3.1 Where ML-Guided Optimization Wins
1. **Branch-dense code (`roman_numerals`, `triangle_classifier`)**:
   - Both programs are in the "Deep" branch-depth group (13 and 15 conditional branches on the deepest path).
   - The selector chose `code_size_dce` (`mem2reg,simplifycfg,instcombine,dce,adce`), reaching **6.10 ms vs 12.11 ms** for `-O2` on `roman_numerals` (**1.99x**) and **2.30 ms vs 4.09 ms** on `triangle_classifier` (**1.78x**).
2. **Pointer and loop programs (`string_reverse`, `matrix_transpose`, `insertion_sort`)**:
   - `string_reverse` with `tailcall_simplify`: **3.23 ms vs 5.60 ms** (**1.73x** vs `-O2`).
   - `matrix_transpose` and `insertion_sort` with `loop_intensive` (`mem2reg,loop-rotate,licm,loop-unroll,instcombine,simplifycfg`): **1.59x** and **1.49x** vs `-O2`.
3. **Simple recursion (`fibonacci`, `factorial`, `tower_of_hanoi`)**:
   - `tailcall_simplify` was predicted and was also the best candidate for all three, giving **1.70x**, **1.56x** and **1.51x** vs `-O2`.

### 3.2 Where Standard Baselines Outperform ML
1. **Complex recursion (`ackermann`, `permutations`)**:
   - `ackermann` runs in 2.44 ms at `-O2` but 24.62 ms with the ML strategy (**0.10x**), and even the best candidate reaches only 0.10x. `permutations` reaches 0.54x. The default pipelines likely benefit from interprocedural transformations such as inlining, which are not part of the candidate pass pool.
2. **Loop nests that benefit from vectorization or deeper loop optimization (`matrix_multiply`, `binary_search`, `hash_table`, `bit_manipulation`)**:
   - `matrix_multiply` 0.69x, `binary_search` 0.76x, `hash_table` 0.85x and `bit_manipulation` 0.90x vs `-O2`. `bit_manipulation` is fastest at `-O3` (1.24 ms vs 3.03 ms for ML).
3. **Mispredictions**:
   - For several losses a better candidate existed: on `matrix_multiply` the best candidate (`loop_intensive`) reaches 1.44x vs `-O2`, and on `hash_table` (`arithmetic_constant`) 1.74x, but the model predicted a different strategy.

### 3.3 Win Rate Summary
- **ML matched or beat `-O2`**: on **23 out of 30 programs (76.7%)**; geometric-mean speedup **1.14x** over `-O2`.
- **ML matched or beat `-O3`**: on **21 out of 30 programs (70.0%)**; geometric-mean speedup **1.07x** over `-O3`.
- **Geometric-mean speedup over `-O0`**: `-O2` 2.36x, `-O3` 2.50x, ML 2.68x, best candidate 3.09x.
- **Best candidate (upper bound)**: matched or beat `-O2` on 28/30 and `-O3` on 24/30 programs.
- **Model accuracy**: the leave-one-out prediction was the fastest candidate on **10/30 programs (33.3%)**; training accuracy 96.7%. Every predicted strategy compiled and passed correctness on every program (no fallbacks).

### 3.4 Results by Program Feature
Raw execution times can't be compared across different programs, so results are also aggregated **by static program feature**. Programs are grouped as follows:

| Dimension | Groups | Source feature |
|:---|:---|:---|
| Recursion | Recursive / Non-recursive | `is_recursive` |
| Branch depth | Shallow / Moderate / Deep (tertile cut points) | `max_branch_depth` |
| Loop count | No loops / Few (1-3) / Many (4+) | `loop_count` |
| Memory intensity | Compute-heavy / Memory-heavy (median split) | `mem_to_total_ratio` |
| Program size | Small / Medium / Large (tertile cut points, IR instructions) | `instruction_count` |

| Dimension | Group | Programs | Geomean ML vs -O0 | Geomean ML vs -O2 | Geomean ML vs -O3 | Best Candidate vs -O2 | ML Wins vs -O2 | ML Wins vs -O3 |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Recursion | Non-recursive | 22 | 2.64x | **1.22x** | **1.12x** | 1.45x | 17/22 | 15/22 |
| Recursion | Recursive | 8 | 2.79x | 0.93x | 0.95x | 0.97x | 6/8 | 6/8 |
| Branch depth | Shallow (<= 2) | 11 | 2.88x | **1.02x** | 0.93x | 1.12x | 8/11 | 7/11 |
| Branch depth | Moderate (2-4] | 12 | 2.16x | **1.09x** | **1.01x** | 1.39x | 8/12 | 7/12 |
| Branch depth | Deep (> 4) | 7 | 3.48x | **1.44x** | **1.48x** | 1.49x | 7/7 | 7/7 |
| Loop count | Few loops (1-3) | 14 | 2.86x | **1.01x** | 0.91x | 1.14x | 10/14 | 8/14 |
| Loop count | Many loops (4+) | 16 | 2.54x | **1.25x** | **1.23x** | 1.47x | 13/16 | 13/16 |
| Memory intensity | Compute-heavy (<= 0.57) | 16 | 2.90x | **1.04x** | 0.96x | 1.18x | 11/16 | 10/16 |
| Memory intensity | Memory-heavy (> 0.57) | 14 | 2.45x | **1.26x** | **1.22x** | 1.46x | 12/14 | 11/14 |
| Program size | Small (<= 92) | 10 | 2.90x | 0.93x | 0.83x | 1.03x | 6/10 | 6/10 |
| Program size | Medium (92-129] | 10 | 2.70x | **1.27x** | **1.23x** | 1.48x | 9/10 | 7/10 |
| Program size | Large (> 129) | 10 | 2.46x | **1.24x** | **1.20x** | 1.46x | 8/10 | 8/10 |

**Observations:**
- **Recursion**: ML is weaker on recursive programs (geomean **0.93x** vs `-O2`, 6/8 wins) than on non-recursive ones (**1.22x**, 17/22). The recursive group contains the two largest losses (`ackermann`, `permutations`).
- **Branch depth**: the deeper the branching, the larger the ML gain: Shallow **1.02x**, Moderate **1.09x**, Deep **1.44x**, and ML beat both `-O2` and `-O3` on all 7 deep-branching programs.
- **Loops**: programs with many loops (4+) gain more (**1.25x**, 13/16 wins) than programs with few (**1.01x**, 10/14).
- **Memory intensity**: memory-heavy programs gain more (**1.26x**) than compute-heavy ones (**1.04x**).
- **Program size**: small programs are the only size group where ML is slower than `-O2` on average (**0.93x**); medium and large programs gain **1.27x** and **1.24x**.

Outputs: `results/feature_category_summary.csv`, `plots/speedup_by_<dimension>.svg`, and the "Results by Program Feature" card on the web dashboard. Each program's group labels are also written as `group_*` columns in `results/comparison_summary.csv`.

---

## 4. Viva Examination Q&A Guide

**Q1: How does your model select passes for a new C program?**
> *A: Clang compiles the C program to unoptimized LLVM IR with `-disable-O0-optnone`. Our static feature extractor parses the IR text, constructing the Control Flow Graph and call graph to calculate 25 static features (e.g. basic blocks, loops, memory operation ratios, recursion and maximum branch depth). This feature vector is evaluated by a trained Random Forest ensemble to predict the most effective of 7 optimization strategies, which is translated to an ordered sequence of passes applied via LLVM's `opt` and lowered to machine code with `llc -O2`.*

**Q2: Why did you implement CART Decision Trees from scratch?**
> *A: To guarantee complete transparency, zero external dependencies, and inspectability. Every split threshold, Gini impurity calculation, and decision branch is directly visible in our Python codebase (`src/ml/decision_tree.py`), allowing us to trace exactly which features drove the compiler pass selection.*

**Q3: Does pass ordering matter? Can you prove it?**
> *A: Yes. We implemented `PassOrderingExplorer` (`src/optimization/ordering_search.py`), which runs beam search and permutations. For instance, testing permutations of `{instcombine, sccp, simplifycfg}` and applying beam search demonstrated how pass ordering directly changes the intermediate instruction count and branch structures.*

**Q4: Did ML beat -O3 on all programs?**
> *A: No. ML matched or beat -O3 on 21 of 30 programs (70.0%) and -O2 on 23 of 30 (76.7%). It is strongest on deeply branching and loop-heavy code (e.g. `roman_numerals`, 1.99x vs -O2) and weakest on complex recursion (`ackermann`, 0.10x) and on loop nests where the default pipelines' inlining and vectorization help (`matrix_multiply`, `bit_manipulation`), because our candidate pass pool does not include those passes.*

**Q5: How accurate is the model, and how do you know the results are not just memorized?**
> *A: Every ML result is a leave-one-out prediction: for each program, a fresh Random Forest is trained on the other 29 programs and then predicts the held-out one. The prediction was exactly the fastest of the 7 strategies for 10 of 30 programs (33.3%, against 14.3% for random choice among 7). Even when it misses the single best strategy, the chosen one is often close: ML matched or beat -O2 on 23 of 30 programs.*

**Q6: Why categorize results by features rather than by program?**
> *A: Execution times from different programs aren't comparable, and the useful question is which kinds of programs benefit. Grouping by static features (recursion, branch depth, loop count, memory intensity, size) and taking geometric means of speedups shows, for example, that ML gains most on deeply branching code (1.44x vs -O2) and least on recursive code (0.93x).*
