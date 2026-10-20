"""
LLVM IR Feature Extractor
Extracts static code characteristics and graph metrics from LLVM Intermediate Representation (.ll).
"""

import os
import re
from typing import Dict, List, Set, Any, Optional


class IRFeatureExtractor:
    """
    Parses LLVM IR textual assembly (.ll) and extracts static program features
    including instruction counts, CFG properties, loop metrics, and memory operation ratios.
    """

    # Opcode classifications
    ARITHMETIC_OPS = {
        "add", "sub", "mul", "udiv", "sdiv", "fadd", "fsub", "fmul", "fdiv",
        "urem", "srem", "frem"
    }
    LOGIC_BIT_OPS = {
        "shl", "lshr", "ashr", "and", "or", "xor"
    }
    MEMORY_OPS = {
        "load", "store", "alloca", "getelementptr", "fence", "cmpxchg", "atomicrmw"
    }
    COMPARISON_OPS = {
        "icmp", "fcmp"
    }
    CALL_OPS = {
        "call", "invoke"
    }
    BRANCH_OPS = {
        "br", "switch", "indirectbr"
    }

    FEATURE_NAMES = [
        "instruction_count",
        "basic_block_count",
        "function_count",
        "loop_count",
        "branch_count",
        "cond_branch_count",
        "uncond_branch_count",
        "load_count",
        "store_count",
        "alloca_count",
        "gep_count",
        "phi_count",
        "arithmetic_count",
        "bitwise_count",
        "cmp_count",
        "call_count",
        "ret_count",
        "mem_op_count",
        # Normalized / Derived features
        "load_store_ratio",
        "mem_to_total_ratio",
        "arith_to_total_ratio",
        "branch_to_bb_ratio",
        "phi_to_bb_ratio",
        # Structural features (call graph / per-function CFG)
        "is_recursive",
        "max_branch_depth"
    ]

    def __init__(self):
        pass

    def extract_features(self, ir_path: str) -> Dict[str, float]:
        """
        Extracts all static features from an LLVM IR file.
        Returns a dictionary mapping feature name to numeric value.
        """
        if not os.path.exists(ir_path):
            raise FileNotFoundError(f"LLVM IR file does not exist: {ir_path}")

        with open(ir_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return self.extract_from_text(content)

    def extract_from_text(self, ir_text: str) -> Dict[str, float]:
        """Parses IR text directly and returns the feature dictionary."""
        lines = ir_text.splitlines()

        instruction_count = 0
        basic_block_count = 0
        function_count = 0
        branch_count = 0
        cond_branch_count = 0
        uncond_branch_count = 0
        load_count = 0
        store_count = 0
        alloca_count = 0
        gep_count = 0
        phi_count = 0
        arithmetic_count = 0
        bitwise_count = 0
        cmp_count = 0
        call_count = 0
        ret_count = 0
        mem_op_count = 0

        # CFG and loop tracking
        in_function = False
        current_bb = None
        bb_order: List[str] = []
        cfg_successors: Dict[str, Set[str]] = {}

        # Per-function CFG and call graph (block labels like %4 repeat across functions)
        current_func: Optional[str] = None
        func_cfgs: Dict[str, Dict[str, Set[str]]] = {}
        func_entry: Dict[str, str] = {}
        func_cond_blocks: Dict[str, Set[str]] = {}
        call_graph: Dict[str, Set[str]] = {}
        entry_has_inst = False
        in_switch = False  # inside the "[ ... ]" case list of a multi-line switch

        for line in lines:
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith(";"):
                continue

            # Check function boundaries
            if stripped.startswith("define ") and "{" in stripped:
                in_function = True
                function_count += 1
                current_bb = "entry"
                bb_order.append(current_bb)
                cfg_successors[current_bb] = set()
                basic_block_count += 1

                name_match = re.search(r"@([\w\.\$\"-]+)\s*\(", stripped)
                current_func = name_match.group(1).strip('"') if name_match else f"__func{function_count}"
                func_cfgs[current_func] = {"entry": set()}
                func_entry[current_func] = "entry"
                func_cond_blocks[current_func] = set()
                call_graph.setdefault(current_func, set())
                entry_has_inst = False
                continue

            if stripped == "}":
                in_function = False
                in_switch = False
                current_bb = None
                current_func = None
                continue

            if not in_function:
                continue

            # Basic block label detection
            # e.g., "4:" or "entry:" or "bb12:"
            bb_match = re.match(r"^([a-zA-Z0-9_\.]+):\s*(;.*)?$", stripped)
            if bb_match:
                current_bb = bb_match.group(1)
                bb_order.append(current_bb)
                cfg_successors[current_bb] = set()
                basic_block_count += 1

                if current_func:
                    fcfg = func_cfgs[current_func]
                    # An explicit first label replaces the empty implicit entry block
                    if not entry_has_inst and func_entry[current_func] == "entry" and len(fcfg) == 1:
                        del fcfg["entry"]
                        func_entry[current_func] = current_bb
                    fcfg.setdefault(current_bb, set())
                    entry_has_inst = True
                continue

            # Strip inline comments for instruction parsing
            inst_code = stripped.split(";")[0].strip()
            if not inst_code:
                continue
            entry_has_inst = True

            # Case lines of a multi-line switch ("i32 0, label %8" ... "]") are
            # successor edges of the switch, not separate instructions
            if in_switch:
                targets = re.findall(r"label\s+%([a-zA-Z0-9_\.]+)", inst_code)
                if current_bb:
                    cfg_successors[current_bb].update(targets)
                    if current_func:
                        func_cfgs[current_func].setdefault(current_bb, set()).update(targets)
                if "]" in inst_code:
                    in_switch = False
                continue

            # Instruction token parsing
            # Remove left-hand variable assignment (e.g., "%1 = load ...")
            if "=" in inst_code:
                parts = inst_code.split("=", 1)
                right_hand = parts[1].strip()
            else:
                right_hand = inst_code

            tokens = right_hand.split()
            if not tokens:
                continue

            opcode = tokens[0].lower()

            # Skip non-instruction statements inside function body
            if opcode in {"ret", "br", "switch", "indirectbr"}:
                pass
            elif opcode not in self.ARITHMETIC_OPS and opcode not in self.LOGIC_BIT_OPS and \
                 opcode not in self.MEMORY_OPS and opcode not in self.COMPARISON_OPS and \
                 opcode not in self.CALL_OPS and opcode != "phi":
                # Check for prefixed instructions or other statements
                if not any(token in self.MEMORY_OPS or token in self.ARITHMETIC_OPS for token in tokens):
                    # Could be metadata or attributes
                    pass

            instruction_count += 1

            # Count by opcode
            if opcode in self.ARITHMETIC_OPS:
                arithmetic_count += 1
            elif opcode in self.LOGIC_BIT_OPS:
                bitwise_count += 1
            elif opcode == "load":
                load_count += 1
                mem_op_count += 1
            elif opcode == "store":
                store_count += 1
                mem_op_count += 1
            elif opcode == "alloca":
                alloca_count += 1
                mem_op_count += 1
            elif opcode == "getelementptr":
                gep_count += 1
                mem_op_count += 1
            elif opcode in self.MEMORY_OPS:
                mem_op_count += 1
            elif opcode in self.COMPARISON_OPS:
                cmp_count += 1
            elif opcode in self.CALL_OPS:
                call_count += 1
            elif opcode == "phi":
                phi_count += 1
            elif opcode == "ret":
                ret_count += 1
            elif opcode == "br":
                branch_count += 1
                # Check if conditional: "br i1 %cond, label %a, label %b"
                if len(tokens) > 1 and tokens[1].startswith("i1"):
                    cond_branch_count += 1
                    # Extract target labels
                    targets = re.findall(r"label\s+%([a-zA-Z0-9_\.]+)", inst_code)
                    if current_bb:
                        for tgt in targets:
                            cfg_successors[current_bb].add(tgt)
                else:
                    uncond_branch_count += 1
                    # "br label %a"
                    targets = re.findall(r"label\s+%([a-zA-Z0-9_\.]+)", inst_code)
                    if current_bb:
                        for tgt in targets:
                            cfg_successors[current_bb].add(tgt)
            elif opcode == "switch":
                branch_count += 1
                cond_branch_count += 1
                targets = re.findall(r"label\s+%([a-zA-Z0-9_\.]+)", inst_code)
                if current_bb:
                    for tgt in targets:
                        cfg_successors[current_bb].add(tgt)
                if "[" in inst_code and "]" not in inst_code:
                    in_switch = True

            if current_func and current_bb:
                # Per-function CFG edges for branch-depth analysis
                if opcode in ("br", "switch"):
                    targets = re.findall(r"label\s+%([a-zA-Z0-9_\.]+)", inst_code)
                    func_cfgs[current_func].setdefault(current_bb, set()).update(targets)
                    if opcode == "switch" or (len(tokens) > 1 and tokens[1].startswith("i1")):
                        func_cond_blocks[current_func].add(current_bb)
                # Direct call edges for recursion detection
                elif re.search(r"\b(call|invoke)\b", right_hand):
                    callee = re.search(r"@([\w\.\$\"-]+)\s*\(", right_hand)
                    if callee:
                        call_graph[current_func].add(callee.group(1).strip('"'))

        # Estimate loop count by detecting back-edges in CFG
        # A back-edge is an edge from u to v where v appears at or before u in topological/natural order
        bb_index = {bb: idx for idx, bb in enumerate(bb_order)}
        loop_count = 0
        back_edges = set()

        for u, succs in cfg_successors.items():
            u_idx = bb_index.get(u, -1)
            for v in succs:
                v_idx = bb_index.get(v, -1)
                if v_idx != -1 and v_idx <= u_idx:
                    back_edges.add((u, v))

        # Check for loop metadata '!llvm.loop' in text if back-edges gave 0
        meta_loops = len(re.findall(r"!llvm\.loop", ir_text))
        loop_count = max(len(back_edges), meta_loops)

        # Derived metrics & normalization
        total_inst = max(instruction_count, 1)
        total_bb = max(basic_block_count, 1)

        load_store_ratio = float(load_count) / max(store_count, 1)
        mem_to_total_ratio = float(mem_op_count) / total_inst
        arith_to_total_ratio = float(arithmetic_count + bitwise_count) / total_inst
        branch_to_bb_ratio = float(branch_count) / total_bb
        phi_to_bb_ratio = float(phi_count) / total_bb

        is_recursive = self._has_recursion(call_graph)
        max_branch_depth = 0
        for fname, fcfg in func_cfgs.items():
            depth = self._max_branch_depth(fcfg, func_entry[fname], func_cond_blocks[fname])
            max_branch_depth = max(max_branch_depth, depth)

        features = {
            "instruction_count": float(instruction_count),
            "basic_block_count": float(basic_block_count),
            "function_count": float(function_count),
            "loop_count": float(loop_count),
            "branch_count": float(branch_count),
            "cond_branch_count": float(cond_branch_count),
            "uncond_branch_count": float(uncond_branch_count),
            "load_count": float(load_count),
            "store_count": float(store_count),
            "alloca_count": float(alloca_count),
            "gep_count": float(gep_count),
            "phi_count": float(phi_count),
            "arithmetic_count": float(arithmetic_count),
            "bitwise_count": float(bitwise_count),
            "cmp_count": float(cmp_count),
            "call_count": float(call_count),
            "ret_count": float(ret_count),
            "mem_op_count": float(mem_op_count),
            "load_store_ratio": round(load_store_ratio, 4),
            "mem_to_total_ratio": round(mem_to_total_ratio, 4),
            "arith_to_total_ratio": round(arith_to_total_ratio, 4),
            "branch_to_bb_ratio": round(branch_to_bb_ratio, 4),
            "phi_to_bb_ratio": round(phi_to_bb_ratio, 4),
            "is_recursive": float(is_recursive),
            "max_branch_depth": float(max_branch_depth),
        }

        return features

    @staticmethod
    def _has_recursion(call_graph: Dict[str, Set[str]]) -> bool:
        """True if any defined function can reach itself through direct calls (self or mutual recursion)."""
        for start in call_graph:
            stack = list(call_graph[start])
            seen: Set[str] = set()
            while stack:
                fn = stack.pop()
                if fn == start:
                    return True
                if fn in seen or fn not in call_graph:
                    continue
                seen.add(fn)
                stack.extend(call_graph[fn])
        return False

    @staticmethod
    def _max_branch_depth(cfg: Dict[str, Set[str]], entry: str, cond_blocks: Set[str]) -> int:
        """
        Largest number of conditional branches along any acyclic path from the entry block.
        Back-edges (loop latches) are discovered via DFS and ignored so the CFG becomes a DAG.
        """
        if entry not in cfg:
            return 0

        # Iterative DFS: record post-order and back-edges (edges to a node still on the stack)
        post_order: List[str] = []
        back_edges: Set[tuple] = set()
        state: Dict[str, int] = {entry: 1}  # 1 = on stack, 2 = finished
        stack = [(entry, iter(sorted(cfg.get(entry, ()))))]
        while stack:
            node, succ_iter = stack[-1]
            advanced = False
            for succ in succ_iter:
                if succ not in cfg:
                    continue
                s = state.get(succ, 0)
                if s == 1:
                    back_edges.add((node, succ))
                elif s == 0:
                    state[succ] = 1
                    stack.append((succ, iter(sorted(cfg.get(succ, ())))))
                    advanced = True
                    break
            if not advanced:
                state[node] = 2
                post_order.append(node)
                stack.pop()

        # Longest path on the DAG; post-order visits successors before predecessors
        depth: Dict[str, int] = {}
        for node in post_order:
            best = 0
            for succ in cfg.get(node, ()):
                if succ in depth and (node, succ) not in back_edges:
                    best = max(best, depth[succ])
            depth[node] = best + (1 if node in cond_blocks else 0)
        return depth.get(entry, 0)

    def to_feature_vector(self, features: Dict[str, float]) -> List[float]:
        """Converts feature dictionary to an ordered list of floats for ML models."""
        return [features[name] for name in self.FEATURE_NAMES]
