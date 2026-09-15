"""
LLVM 14 Optimization Pass Pool
Defines the controlled candidate set of LLVM 14 passes and categories.
"""

from typing import Dict, List, Set


class PassPool:
    """Registry and taxonomy of LLVM 14 optimization passes."""

    # Passes categorized by optimization intent
    PASS_CATEGORIES: Dict[str, List[str]] = {
        "scalar_cleanup": [
            "mem2reg",
            "instcombine",
            "simplifycfg",
            "reassociate",
            "aggressive-instcombine"
        ],
        "loop_transforms": [
            "loop-rotate",
            "licm",
            "loop-unroll",
            "loop-simplifycfg"
        ],
        "redundancy_elim": [
            "gvn",
            "sccp",
            "ipsccp",
            "dse",
            "dce",
            "adce"
        ],
        "control_flow": [
            "simplifycfg",
            "tailcallelim"
        ]
    }

    # Pass descriptions for documentation and reports
    PASS_DESCRIPTIONS: Dict[str, str] = {
        "mem2reg": "Promote memory to register (SSA form construction)",
        "instcombine": "Combine redundant instructions into simpler canonical forms",
        "simplifycfg": "Simplify the control flow graph (dead block deletion, branch merging)",
        "reassociate": "Reassociate commutative arithmetic expressions for better optimization",
        "aggressive-instcombine": "Aggressively combine expressions across extended patterns",
        "loop-rotate": "Transform for/while loops into do-while loops with guarding header",
        "licm": "Loop-invariant code motion (hoists loop-invariant computations)",
        "loop-unroll": "Unroll loops to eliminate branch overhead and increase instruction parallelism",
        "loop-simplifycfg": "Simplify control flow structure inside loops",
        "gvn": "Global Value Numbering (detects and eliminates redundant expressions across CFG)",
        "sccp": "Sparse Conditional Constant Propagation (propagates constants through branches)",
        "ipsccp": "Interprocedural Sparse Conditional Constant Propagation",
        "dse": "Dead Store Elimination (removes memory stores overwritten before use)",
        "dce": "Dead Code Elimination (removes instructions whose values are unused)",
        "adce": "Aggressive Dead Code Elimination (removes dead control flow and code)",
        "tailcallelim": "Eliminate recursive tail calls into iterative loops"
    }

    @classmethod
    def get_all_passes(cls) -> List[str]:
        """Returns the unique list of supported candidate passes."""
        passes = set()
        for cat_passes in cls.PASS_CATEGORIES.values():
            passes.update(cat_passes)
        return sorted(list(passes))

    @classmethod
    def get_description(cls, pass_name: str) -> str:
        """Returns the explanation of a specific pass."""
        return cls.PASS_DESCRIPTIONS.get(pass_name, "LLVM 14 Optimization Pass")
