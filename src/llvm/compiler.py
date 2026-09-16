"""
LLVM Compiler & Driver Module
Handles invoking clang to produce unoptimized LLVM IR and linking IR to executables.
"""

import os
import sys
import shutil
import subprocess
from typing import Optional, Tuple


def _find_tool(name: str, candidate_paths: list) -> str:
    found = shutil.which(name)
    if found:
        return found
    for cand in candidate_paths:
        if os.path.exists(cand):
            return cand
    return name


class LLVMCompiler:
    """Wrapper around clang and LLVM tools for compiling C source to IR and binaries."""

    def __init__(self, clang_path: str = "clang", opt_path: str = "opt", llc_path: str = "llc"):
        win_clang_candidates = [
            r"C:\Program Files\LLVM\bin\clang.exe",
            r"C:\Users\SI\OneDrive\VIT\compiler\mingw64\bin\clang.exe",
        ]
        win_opt_candidates = [
            r"C:\Program Files\LLVM\bin\opt.exe",
        ]
        win_llc_candidates = [
            r"C:\Program Files\LLVM\bin\llc.exe",
        ]

        self.clang_path = _find_tool(clang_path, win_clang_candidates)
        self.opt_path = _find_tool(opt_path, win_opt_candidates)
        self.llc_path = _find_tool(llc_path, win_llc_candidates)

        if sys.platform == "win32":
            extra_paths = [
                r"C:\Users\SI\OneDrive\VIT\compiler\mingw64\bin",
                r"C:\Program Files\LLVM\bin",
            ]
            current_path = os.environ.get("PATH", "")
            for p in extra_paths:
                if os.path.exists(p) and p.lower() not in current_path.lower():
                    current_path = f"{p};{current_path}"
            os.environ["PATH"] = current_path

    def c_to_ir(self, c_path: str, ir_path: str) -> Tuple[bool, str]:
        """
        Compiles a C source file to LLVM IR (.ll) with O0 and disabled optnone.
        Disabling optnone is critical so subsequent opt passes can modify the code.
        """
        if not os.path.exists(c_path):
            return False, f"Source file does not exist: {c_path}"

        os.makedirs(os.path.dirname(os.path.abspath(ir_path)), exist_ok=True)
        cmd = [
            self.clang_path,
            "-O0",
            "-Xclang",
            "-disable-O0-optnone",
            "-S",
            "-emit-llvm",
            c_path,
            "-o",
            ir_path
        ]
        if sys.platform == "win32":
            cmd.insert(1, "--target=x86_64-w64-windows-gnu")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, ir_path
        except subprocess.CalledProcessError as e:
            return False, f"Clang error: {e.stderr}"

    def ir_to_executable(self, ir_path: str, exe_path: str) -> Tuple[bool, str]:
        """
        Compiles an LLVM IR file to a native executable using clang.
        Links the standard math library (-lm).
        """
        if not os.path.exists(ir_path):
            return False, f"IR file does not exist: {ir_path}"

        os.makedirs(os.path.dirname(os.path.abspath(exe_path)), exist_ok=True)
        cmd = [
            self.clang_path,
            ir_path,
            "-lm",
            "-o",
            exe_path
        ]
        if sys.platform == "win32":
            cmd.insert(1, "--target=x86_64-w64-windows-gnu")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, exe_path
        except subprocess.CalledProcessError as e:
            return False, f"Clang linking error: {e.stderr}"

    def c_to_executable(self, c_path: str, exe_path: str, opt_level: str = "-O0") -> Tuple[bool, str]:
        """
        Directly compiles a C source file to an executable with a specific optimization level.
        """
        if not os.path.exists(c_path):
            return False, f"Source file does not exist: {c_path}"

        os.makedirs(os.path.dirname(os.path.abspath(exe_path)), exist_ok=True)
        cmd = [
            self.clang_path,
            opt_level,
            c_path,
            "-lm",
            "-o",
            exe_path
        ]
        if sys.platform == "win32":
            cmd.insert(1, "--target=x86_64-w64-windows-gnu")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, exe_path
        except subprocess.CalledProcessError as e:
            return False, f"Clang direct compilation error: {e.stderr}"

