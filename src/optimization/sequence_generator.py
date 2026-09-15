"""
Pass Sequence Generator & Search Space
Defines named candidate optimization sequences and generates ordered sequences for exploration.
"""

import itertools
from typing import Dict, List, Set, Optional
from src.optimization.pass_pool import PassPool


class SequenceGenerator:
    """Manages candidate optimization pass sequences and ordering exploration."""

    # Pre-defined named sequences aligned with compiler optimization strategies
    NAMED_STRATEGIES: Dict[str, List[str]] = {
        "scalar_cleanup": [
            "mem2reg",
            "instcombine",
            "simplifycfg"
        ],
        "arithmetic_constant": [
            "mem2reg",
            "instcombine",
            "reassociate",
            "sccp",
            "dce"
        ],
        "loop_intensive": [
            "mem2reg",
            "loop-rotate",
            "licm",
            "loop-unroll",
            "instcombine",
            "simplifycfg"
        ],
        "memory_redundancy": [
            "mem2reg",
            "gvn",
            "dse",
            "instcombine",
            "simplifycfg"
        ],
        "code_size_dce": [
            "mem2reg",
            "simplifycfg",
            "instcombine",
            "dce",
            "adce"
        ],
        "full_scalar_licm": [
            "mem2reg",
            "sccp",
            "loop-rotate",
            "licm",
            "instcombine",
            "simplifycfg",
            "dce"
        ],
        "tailcall_simplify": [
            "mem2reg",
            "tailcallelim",
            "simplifycfg",
            "instcombine",
            "dce"
        ]
    }

    def __init__(self):
        self.pass_pool = PassPool()

    def get_named_strategies(self) -> Dict[str, List[str]]:
        """Returns all named candidate strategies."""
        return dict(self.NAMED_STRATEGIES)

    def get_strategy_names(self) -> List[str]:
        """Returns list of all named strategy identifiers."""
        return list(self.NAMED_STRATEGIES.keys())

    def get_sequence(self, strategy_name: str) -> List[str]:
        """Returns the pass sequence for a specific strategy name."""
        if strategy_name not in self.NAMED_STRATEGIES:
            raise KeyError(f"Unknown strategy '{strategy_name}'. Available: {list(self.NAMED_STRATEGIES.keys())}")
        return self.NAMED_STRATEGIES[strategy_name]

    def generate_permutations(self, base_passes: List[str], max_permutations: int = 10) -> List[List[str]]:
        """
        Generates different orderings for a set of passes to test pass ordering sensitivity.
        Always retains 'mem2reg' at the beginning if present, since SSA promotion is prerequisite.
        """
        has_mem2reg = "mem2reg" in base_passes
        other_passes = [p for p in base_passes if p != "mem2reg"]

        perms = list(itertools.permutations(other_passes))
        results: List[List[str]] = []

        for p in perms[:max_permutations]:
            seq = ["mem2reg"] + list(p) if has_mem2reg else list(p)
            results.append(seq)

        return results

    def generate_candidate_pool(self, include_permutations: bool = False) -> Dict[str, List[str]]:
        """
        Returns a dictionary of strategy_name -> pass_sequence for dataset exploration.
        """
        candidates = dict(self.NAMED_STRATEGIES)

        if include_permutations:
            # Add order-variation sequences to explore ordering effects
            base = ["instcombine", "sccp", "simplifycfg"]
            perms = self.generate_permutations(["mem2reg"] + base, max_permutations=4)
            for idx, seq in enumerate(perms):
                candidates[f"order_variant_{idx+1}"] = seq

        return candidates
