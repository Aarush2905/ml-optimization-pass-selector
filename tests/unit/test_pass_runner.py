"""
Unit Tests for PassRunner and LLVMCompiler
"""

import os
import tempfile
import unittest

from src.llvm.compiler import LLVMCompiler
from src.llvm.pass_runner import PassRunner


class TestLLVMPassRunner(unittest.TestCase):

    def setUp(self):
        self.compiler = LLVMCompiler()
        self.pass_runner = PassRunner()
        self.temp_dir = tempfile.mkdtemp()

    def test_c_to_ir_generation(self):
        out_ir = os.path.join(self.temp_dir, "sample_test.ll")
        ok, msg = self.compiler.c_to_ir("tests/sample.c", out_ir)
        self.assertTrue(ok, f"Compilation to IR failed: {msg}")
        self.assertTrue(os.path.exists(out_ir))
        with open(out_ir, "r") as f:
            content = f.read()
            self.assertIn("define", content)
            self.assertIn("@main", content)

    def test_run_passes_instcombine(self):
        out_ir = os.path.join(self.temp_dir, "opt_test.ll")
        ok, msg = self.pass_runner.run_passes("tests/sample.ll", out_ir, ["mem2reg", "instcombine"])
        self.assertTrue(ok, f"Pass execution failed: {msg}")
        self.assertTrue(os.path.exists(out_ir))

    def test_run_standard_pipeline_o2(self):
        out_ir = os.path.join(self.temp_dir, "opt_o2.ll")
        ok, msg = self.pass_runner.run_standard_pipeline("tests/sample.ll", out_ir, level="O2")
        self.assertTrue(ok, f"O2 pipeline failed: {msg}")
        self.assertTrue(os.path.exists(out_ir))

    def test_invalid_input_file(self):
        out_ir = os.path.join(self.temp_dir, "invalid.ll")
        ok, _ = self.pass_runner.run_passes("tests/does_not_exist.ll", out_ir, ["dce"])
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
