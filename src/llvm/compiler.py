"""
LLVM Compiler & Driver Module
Handles invoking clang to produce unoptimized LLVM IR and linking IR to executables.
"""

import os
import subprocess
from typing import Optional, Tuple


class LLVMCompiler:
    """Wrapper around clang and LLVM tools for compiling C source to IR and binaries."""

    def __init__(self, clang_path: str = "clang", opt_path: str = "opt", llc_path: str = "llc"):
        self.clang_path = clang_path
        self.opt_path = opt_path
        self.llc_path = llc_path

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
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, exe_path
        except subprocess.CalledProcessError as e:
            return False, f"Clang direct compilation error: {e.stderr}"
