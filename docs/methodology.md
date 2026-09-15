# Methodology & Theoretical Formulation

**Course**: BCSE307P – Compiler Design Lab  
**Project ID**: A26 — Machine-Learning-Guided Optimization Pass Selector  

---

## 1. Problem Formulation

Compilers traditionally employ fixed optimization suites (such as LLVM's `-O2` and `-O3`). While these default pipelines perform reasonably well on average, they suffer from two major limitations:
1. **Pass Phase Ordering Problem**: Optimization passes interact non-linearly. Applying pass $A$ before pass $B$ can unlock transformations that $B \rightarrow A$ fails to see, or conversely, premature simplification can destroy canonical patterns needed by aggressive loop transformations.
2. **One-Size-Fits-All Overhead**: Heavy loop unrolling or aggressive vectorization in `-O3` can increase binary code size and instruction cache misses on memory-bound or small-loop programs, causing `-O3` to perform slower than `-O2` or custom pipelines.

Our objective is to formulate a mapping:
$$\Phi: \mathcal{X} \rightarrow \mathcal{S}$$
where $\mathcal{X} \in \mathbb{R}^{23}$ is a 23-dimensional static feature vector extracted from the program's unoptimized LLVM IR, and $\mathcal{S}$ is an ordered sequence of LLVM optimization passes $\langle p_1, p_2, \dots, p_k \rangle$ that maximizes runtime speedup and minimizes binary bloat while preserving functional correctness.

---

## 2. Static Feature Extraction Rationale

Rather than relying on dynamic profiling (which is expensive and input-dependent), we extract static IR characteristics directly from the compiler's intermediate representation:

| Feature Name | Compiler Significance |
|:---|:---|
| `instruction_count` | Total work volume; correlates with baseline execution scale. |
| `basic_block_count` | Control flow complexity and basic block granularity. |
| `loop_count` | Identifies opportunities for loop rotation, unrolling, and invariant code motion. |
| `branch_count`, `cond_branch_count` | Measures branch predictability and control flow divergence. |
| `load_count`, `store_count` | Quantifies memory bandwidth demand; indicates need for `mem2reg` and `gvn`. |
| `alloca_count` | Stack variable usage before SSA conversion. |
| `gep_count` | Array and pointer indexing operations; targets memory optimization. |
| `arithmetic_count` | Arithmetic density; indicates opportunity for `reassociate` and `instcombine`. |
| `bitwise_count` | Bitwise manipulation density; benefits from strength reduction. |
| `cmp_count` | Condition check density. |
| `call_count` | Function call overhead; indicates candidate for inlining / tail call elimination. |
| `load_store_ratio` | $\text{Loads} / \max(\text{Stores}, 1)$; distinguishes read-heavy from write-heavy workloads. |
| `mem_to_total_ratio` | $\text{Memory Ops} / \text{Total Inst}$; memory-bound vs compute-bound indicator. |
| `branch_to_bb_ratio` | Control flow density per basic block. |

---

## 3. LLVM 14 Optimization Pass Pool

The candidate pass space is curated to cover core optimization categories without generating an intractable search explosion:

1. **Memory & SSA Promotion (`mem2reg`)**:
   - Converts memory-allocated stack variables (`alloca`, `load`, `store`) into SSA registers and $\phi$-nodes.
   - Foundation pass: must run first before scalar or loop optimizations.
2. **Instruction Combining (`instcombine`)**:
   - Algebraic simplification and peephole rewrites (e.g. `x * 2` $\rightarrow$ `x << 1`).
3. **Reassociation (`reassociate`)**:
   - Reorders operands in commutative expressions to expose common subexpressions and constant folding opportunities.
4. **Sparse Conditional Constant Propagation (`sccp`)**:
   - Simultaneously propagates constants and eliminates branches that are conditionally dead.
5. **Control Flow Simplification (`simplifycfg`)**:
   - Deletes unreachable basic blocks and merges single-successor blocks.
6. **Global Value Numbering (`gvn`)**:
   - Redundancy elimination across basic block boundaries.
7. **Dead Code & Store Elimination (`dce`, `dse`, `adce`)**:
   - Cleans up dead computations and stores overwritten before use.
8. **Loop Transformations (`loop-rotate`, `licm`, `loop-unroll`)**:
   - Converts loops into do-while form, hoists invariants out of loops, and unrolls loop bodies.
9. **Tail Call Elimination (`tailcallelim`)**:
   - Transforms recursive calls in tail position into iterative jumps.

---

## 4. Machine Learning Model Formulation

### 4.1 CART Decision Tree
At each node $N$, the algorithm evaluates all candidate features $j \in \{1, \dots, D\}$ and all candidate split thresholds $t \in \text{midpoints}(X_j)$.
The optimal split maximizes the reduction in Gini Impurity:
$$\Delta I_G(N) = I_G(N) - \left( \frac{N_L}{N} I_G(N_L) + \frac{N_R}{N} I_G(N_R) \right)$$
where:
$$I_G(S) = 1 - \sum_{c \in \mathcal{C}} p_c^2$$

### 4.2 Random Forest Ensemble
To mitigate overfitting on benchmark programs, we train a Bagging ensemble of $M=25$ trees:
1. For each tree $m \in \{1, \dots, M\}$:
   - Sample $N$ training examples with replacement (bootstrap sample).
   - At each split, evaluate only a random subset of $k = \lfloor\sqrt{D}\rfloor$ features.
2. Final prediction:
   $$\hat{y} = \arg\max_{c \in \mathcal{C}} \sum_{m=1}^M \mathbb{I}(T_m(x) = c)$$

### 4.3 Feature Importance Computation
The feature importance for feature $j$ is accumulated across all trees in the ensemble:
$$\text{Imp}(j) = \frac{\sum_{T} \sum_{n \in T : v(n) = j} N_n \cdot \Delta I_G(n)}{\sum_{j'} \text{Total Imp}(j')}$$

---

## 5. Pass Ordering & Heuristic Beam Search

To tackle pass ordering sensitivity, the framework implements Beam Search:
- Let $B$ be the beam width ($B=2$) and $L$ be the search depth ($L=4$).
- Initial beam: $\mathcal{B}_0 = \{ \langle \text{mem2reg} \rangle \}$.
- At depth $d \in \{1, \dots, L\}$:
  - Generate candidates $\mathcal{C}_d = \{ \text{seq} \circ [p] \mid \text{seq} \in \mathcal{B}_{d-1}, p \in \mathcal{P} \}$.
  - Evaluate each candidate by measuring intermediate IR instruction count reduction.
  - Set $\mathcal{B}_d = \text{Top-}B(\mathcal{C}_d)$.
- Final result: Best-ordered pass sequence found within the exploration budget.
