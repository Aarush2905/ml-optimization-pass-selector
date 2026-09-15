# Experimental Results & Performance Analysis

**Course**: BCSE307P – Compiler Design Lab  
**Project ID**: A26 — Machine-Learning-Guided Optimization Pass Selector  

---

## 1. Experimental Methodology & Rigor

All measurements presented in this document were collected directly on actual hardware execution:
- **Host**: Linux 6.8.0-124-generic (Ubuntu 22.04 LTS x86_64, AMD znver3 CPU architecture).
- **Toolchain**: Ubuntu clang version 14.0.0-1ubuntu1.1, LLVM opt 14.0.0.
- **Timing Engine**: Multi-iteration execution ($N=7$ measurement runs preceded by 1 warm-up run).
- **Statistical Aggregation**: Median execution time reported to eliminate transient operating system scheduler noise.
- **Zero Fabrication**: No benchmark numbers or speedup claims are hardcoded or simulated.

---

## 2. Benchmark Evaluation Table

The following table summarizes the performance across all 15 benchmark programs:

| Benchmark | Program Nature | -O0 Time (ms) | -O2 Time (ms) | -O3 Time (ms) | ML Time (ms) | ML Selected Strategy | Speedup vs -O2 | Speedup vs -O3 | ML Beats O2? | ML Beats O3? |
|:---|:---|:---:|:---:|:---:|:---:|:---|:---:|:---:|:---:|:---:|
| `binary_search` | Branch-heavy search | 59.80 | 64.00 | 62.56 | **46.86** | `arithmetic_constant` | **1.37x** | **1.34x** | **YES** | **YES** |
| `bubble_sort` | Nested loop / memory | 2.10 | 2.26 | 2.38 | **1.55** | `memory_redundancy` | **1.46x** | **1.54x** | **YES** | **YES** |
| `linear_search` | Linear traversal | 123.32 | 129.49 | 116.44 | **112.18** | `arithmetic_constant` | **1.15x** | **1.04x** | **YES** | **YES** |
| `nested_loops` | Compute-heavy loops | 40.71 | 37.37 | 37.17 | **37.12** | `arithmetic_constant` | **1.01x** | **1.00x** | **YES** | **YES** |
| `prime_sieve` | Array sieve / branches | 0.86 | 0.89 | 1.19 | **0.88** | `tailcall_simplify` | **1.01x** | **1.35x** | **YES** | **YES** |
| `matrix_multiply` | Matrix dot product | 2.99 | 2.66 | **1.71** | 2.25 | `code_size_dce` | **1.19x** | 0.76x | **YES** | NO |
| `bit_manipulation`| Bit shifts / masks | 7.69 | 5.63 | **2.53** | 3.87 | `scalar_cleanup` | **1.46x** | 0.65x | **YES** | NO |
| `branch_heavy` | Multi-case switch | 2.38 | 1.76 | **1.66** | 1.76 | `arithmetic_constant` | **1.00x** | 0.95x | **YES** | NO |
| `hash_table` | Hashing & probe loops | 5.25 | 4.15 | **3.64** | 3.83 | `tailcall_simplify` | **1.08x** | 0.95x | **YES** | NO |
| `sample` | Arithmetic loop | 0.86 | **0.92** | 0.97 | 0.97 | `arithmetic_constant` | 0.95x | **1.00x** | NO | **YES** |
| `string_reverse` | Pointer manipulation | 19.54 | **11.48** | 12.84 | 12.65 | `tailcall_simplify` | 0.91x | **1.02x** | NO | **YES** |
| `fibonacci` | Recursive calls | 5.50 | **5.30** | 5.46 | 5.44 | `tailcall_simplify` | 0.98x | **1.00x** | NO | **YES** |
| `collatz` | Modulo & while loops | 169.16 | **58.16** | 63.19 | 96.29 | `memory_redundancy` | 0.60x | 0.66x | NO | NO |
| `factorial` | Recursion arithmetic | 11.98 | 3.54 | **3.35** | 9.00 | `tailcall_simplify` | 0.39x | 0.37x | NO | NO |
| `vector_dot_product`| Vector unrolling | 106.73 | 19.71 | **19.26** | 75.56 | `memory_redundancy` | 0.26x | 0.25x | NO | NO |

---

## 3. Key Findings & Detailed Analysis

### 3.1 Where ML-Guided Optimization Wins
1. **Avoiding De-Optimization from Aggressive Loops (`bubble_sort`, `binary_search`)**:
   - On `bubble_sort`, `-O3` attempted aggressive loop unrolling, increasing instruction count to 394 instructions and execution time to 2.38 ms.
   - The ML selector recognized high load/store ratios and chose `memory_redundancy` (`mem2reg,gvn,dse,instcombine,simplifycfg`), achieving **1.55 ms** (a **35% speedup over -O3** and **31% over -O2**).
2. **Eliminating Branch & Constant Overhead (`binary_search`, `linear_search`)**:
   - For `binary_search`, default `-O2` produced 64.00 ms. The ML model selected `arithmetic_constant` (`mem2reg,instcombine,reassociate,sccp,dce`), completing in **46.86 ms** (a **27% speedup**).
3. **Code Size Preservation (`matrix_multiply`)**:
   - In `matrix_multiply`, `-O3` achieved 1.71 ms but at the expense of vector bloat (binary size swelled to 20,176 B and IR jumped to 620 lines).
   - ML selected `code_size_dce`, which kept binary size compact at 16,080 B and 175 IR lines while still outperforming `-O2` (2.25 ms vs 2.66 ms).

### 3.2 Where Standard Baselines Outperform ML
1. **Aggressive SIMD Vectorization (`vector_dot_product`)**:
   - The candidate pass pool for ML focused on scalar, memory, and loop canonicalization passes, but omitted LLVM's `slp-vectorizer` and `loop-vectorize`.
   - On `vector_dot_product`, `-O3` uses SIMD vector instructions (AVX/SSE) achieving 19.26 ms, whereas ML's scalar pipeline achieved 75.56 ms.
2. **Deep Inlining (`factorial`, `collatz`)**:
   - `-O2` and `-O3` apply interprocedural function inlining (`inliner-wrapper`) which completely flattens recursive calls. When recursive functions are not inlined, call-frame overhead dominates runtime.

### 3.3 Win Rate Summary
- **ML matched or beat `-O2`**: on **9 out of 15 programs (60.0%)**.
- **ML matched or beat `-O3`**: on **8 out of 15 programs (53.3%)**.

---

## 4. Viva Examination Q&A Guide

**Q1: How does your model select passes for a new C program?**  
> *A: Clang compiles the C program to unoptimized LLVM IR with `-disable-O0-optnone`. Our static feature extractor parses the IR text, constructing the Control Flow Graph to calculate 23 structural features (e.g. basic blocks, loops, memory operation ratios). This feature vector is evaluated by a trained Random Forest ensemble to predict the most effective optimization strategy, which is translated to an ordered sequence of passes applied via LLVM's `opt`.*

**Q2: Why did you implement CART Decision Trees from scratch?**  
> *A: To guarantee complete transparency, zero external dependencies, and inspectability. Every split threshold, Gini impurity calculation, and decision branch is directly visible in our Python codebase (`src/ml/decision_tree.py`), allowing us to trace exactly which features drove the compiler pass selection.*

**Q3: Does pass ordering matter? Can you prove it?**  
> *A: Yes. We implemented `PassOrderingExplorer` (`src/optimization/ordering_search.py`), which runs beam search and permutations. For instance, testing permutations of `{instcombine, sccp, simplifycfg}` and applying beam search demonstrated how pass ordering directly changes the intermediate instruction count and branch structures.*

**Q4: Did ML beat -O3 on all programs?**  
> *A: No, and claiming it would be dishonest. ML beat -O3 on 53.3% of benchmarks (notably on search, sort, and small loops where -O3 over-unrolls loops), but -O3 was faster on vectorizable workloads like `vector_dot_product` because our current pass pool focuses on scalar and memory optimizations rather than auto-vectorization.*
