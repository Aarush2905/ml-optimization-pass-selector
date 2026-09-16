"""
LLVM Pass Runner Module
Executes optimization passes and pipelines using LLVM 14 opt.
"""

import os
import sys
import shutil
import subprocess
from typing import List, Optional, Tuple, Union


class PassRunner:
    """Wrapper around LLVM opt tool / clang for applying optimization passes."""

    def __init__(self, opt_path: str = "opt", clang_path: str = "clang"):
        win_opt = r"C:\Program Files\LLVM\bin\opt.exe"
        win_clang = r"C:\Program Files\LLVM\bin\clang.exe"

        if shutil.which(opt_path) is None and os.path.exists(win_opt):
            opt_path = win_opt
        if shutil.which(clang_path) is None and os.path.exists(win_clang):
            clang_path = win_clang

        self.opt_path = opt_path
        self.clang_path = clang_path

    def _opt_available(self) -> bool:
        if shutil.which(self.opt_path) or os.path.exists(self.opt_path):
            try:
                res = subprocess.run([self.opt_path, "--version"], capture_output=True, text=True)
                return res.returncode == 0
            except Exception:
                return False
        return False

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

        if self._opt_available():
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
        else:
            # Fallback to clang optimization when opt is unavailable (e.g., standard Windows LLVM)
            opt_flag = "-O2"
            lowered = pass_str.lower()
            if "o3" in lowered:
                opt_flag = "-O3"
            elif "o1" in lowered:
                opt_flag = "-O1"
            elif "os" in lowered:
                opt_flag = "-Os"
            elif "oz" in lowered:
                opt_flag = "-Oz"
            elif "o0" in lowered:
                opt_flag = "-O0"
            elif "code_size" in lowered or "adce" in lowered:
                opt_flag = "-Os"

            cmd = [
                self.clang_path,
                opt_flag,
                "-S",
                "-emit-llvm",
                input_ir,
                "-o",
                output_ir
            ]
            if sys.platform == "win32":
                cmd.insert(1, "--target=x86_64-w64-windows-gnu")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return True, output_ir
            except subprocess.CalledProcessError as e:
                return False, f"Clang optimization error: {e.stderr}"

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

