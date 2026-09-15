"""
LLVM Pass Runner Module
Executes optimization passes and pipelines using LLVM 14 opt.
"""

import os
import subprocess
from typing import List, Optional, Tuple, Union


class PassRunner:
    """Wrapper around LLVM opt tool for applying optimization passes."""

    def __init__(self, opt_path: str = "opt"):
        self.opt_path = opt_path

    def run_passes(
        self,
        input_ir: str,
        output_ir: str,
        passes: Union[str, List[str]]
    ) -> Tuple[bool, str]:
        """
        Runs a list of passes or a pipeline string on an input IR file using the new pass manager.
        Example passes: ['mem2reg', 'instcombine', 'simplifycfg']
        or 'default<O2>'
        """
        if not os.path.exists(input_ir):
            return False, f"Input IR file does not exist: {input_ir}"

        if isinstance(passes, list):
            pass_str = ",".join(passes)
        else:
            pass_str = passes

        os.makedirs(os.path.dirname(os.path.abspath(output_ir)), exist_ok=True)
        cmd = [
            self.opt_path,
            f"-passes={pass_str}",
            input_ir,
            "-S",
            "-o",
            output_ir
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, output_ir
        except subprocess.CalledProcessError as e:
            return False, f"LLVM opt error: {e.stderr}"

    def run_standard_pipeline(
        self,
        input_ir: str,
        output_ir: str,
        level: str = "O2"
    ) -> Tuple[bool, str]:
        """
        Runs standard LLVM default optimization pipeline (O0, O1, O2, O3, Os, Oz).
        """
        valid_levels = {"O0", "O1", "O2", "O3", "Os", "Oz"}
        norm_level = level.upper().replace("-", "")
        if norm_level not in valid_levels:
            return False, f"Invalid optimization level: {level}. Valid: {valid_levels}"

        return self.run_passes(input_ir, output_ir, f"default<{norm_level}>")
