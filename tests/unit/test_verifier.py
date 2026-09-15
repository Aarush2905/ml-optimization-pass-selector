"""
Unit Tests for CorrectnessVerifier
"""

import os
import tempfile
import unittest
from src.correctness.verifier import CorrectnessVerifier
from src.llvm.compiler import LLVMCompiler


class TestCorrectnessVerifier(unittest.TestCase):

    def setUp(self):
        self.verifier = CorrectnessVerifier(timeout_sec=5)
        self.compiler = LLVMCompiler()
        self.temp_dir = tempfile.mkdtemp()

    def test_run_binary_nonexistent(self):
        res = self.verifier.run_binary("/path/does/not/exist")
        self.assertFalse(res["success"])
        self.assertEqual(res["error"], "not_found")

    def test_verify_identical_binaries(self):
        bin1 = os.path.join(self.temp_dir, "b1")
        bin2 = os.path.join(self.temp_dir, "b2")

        # Compile sample.c to two identical binaries
        self.compiler.c_to_executable("tests/sample.c", bin1)
        self.compiler.c_to_executable("tests/sample.c", bin2)

        is_ok, msg = self.verifier.verify(bin1, bin2)
        self.assertTrue(is_ok, f"Identical binaries failed verification: {msg}")


if __name__ == "__main__":
    unittest.main()
