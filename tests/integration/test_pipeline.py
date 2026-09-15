"""
Integration Test for the Complete End-to-End Optimization Pipeline
"""

import os
import unittest
from src.llvm.compiler import LLVMCompiler
from src.llvm.pass_runner import PassRunner
from src.features.extractor import IRFeatureExtractor
from src.ml.model_wrapper import PassSelectorModel
from src.correctness.verifier import CorrectnessVerifier
from src.benchmarking.benchmark import BenchmarkEngine


class TestEndToEndPipeline(unittest.TestCase):

    def test_full_pipeline_sample(self):
        # 1. Compile C to unoptimized IR
        compiler = LLVMCompiler()
        unopt_ir = "tests/sample.ll"
        self.assertTrue(os.path.exists(unopt_ir))

        # 2. Extract features
        extractor = IRFeatureExtractor()
        features = extractor.extract_features(unopt_ir)
        self.assertGreater(features["instruction_count"], 0)

        # 3. Model prediction
        model = PassSelectorModel()
        model_path = "models/trained_selector.json"
        self.assertTrue(os.path.exists(model_path), "Model must exist")
        model.load(model_path)
        pred = model.predict(features)
        self.assertIn("strategy", pred)
        self.assertIn("passes", pred)
        self.assertGreater(len(pred["passes"]), 0)

        # 4. Apply passes
        pass_runner = PassRunner()
        opt_ir = "/tmp/test_integration_opt.ll"
        ok, msg = pass_runner.run_passes(unopt_ir, opt_ir, pred["passes"])
        self.assertTrue(ok, f"Passes failed: {msg}")

        # 5. Compile binary and verify correctness
        ref_bin = "/tmp/test_integration_ref.out"
        opt_bin = "/tmp/test_integration_opt.out"
        compiler.ir_to_executable(unopt_ir, ref_bin)
        compiler.ir_to_executable(opt_ir, opt_bin)

        verifier = CorrectnessVerifier()
        is_ok, v_msg = verifier.verify(ref_bin, opt_bin)
        self.assertTrue(is_ok, f"Correctness failed: {v_msg}")

        # 6. Benchmark
        bench = BenchmarkEngine(runs=3, warmup_runs=1)
        res = bench.measure_execution_time(opt_bin)
        self.assertTrue(res["success"])
        self.assertGreater(res["median_ms"], 0.0)

        # Clean up
        for p in [opt_ir, ref_bin, opt_bin]:
            if os.path.exists(p):
                os.remove(p)


if __name__ == "__main__":
    unittest.main()
