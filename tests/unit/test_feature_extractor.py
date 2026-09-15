"""
Unit Tests for IRFeatureExtractor
"""

import os
import unittest
from src.features.extractor import IRFeatureExtractor


class TestIRFeatureExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = IRFeatureExtractor()

    def test_extract_from_sample_ll(self):
        sample_path = "tests/sample.ll"
        self.assertTrue(os.path.exists(sample_path), "sample.ll should exist")
        features = self.extractor.extract_features(sample_path)

        self.assertIn("instruction_count", features)
        self.assertGreater(features["instruction_count"], 0)
        self.assertEqual(features["function_count"], 1.0)
        self.assertGreaterEqual(features["loop_count"], 1.0)
        self.assertGreater(features["load_count"], 0)
        self.assertGreater(features["store_count"], 0)

    def test_extract_from_sample_o2_ll(self):
        o2_path = "tests/sample_O2.ll"
        self.assertTrue(os.path.exists(o2_path), "sample_O2.ll should exist")
        features = self.extractor.extract_features(o2_path)

        # In sample_O2.ll, constant folding reduced body to a single return
        self.assertEqual(features["instruction_count"], 1.0)
        self.assertEqual(features["ret_count"], 1.0)
        self.assertEqual(features["loop_count"], 0.0)
        self.assertEqual(features["load_count"], 0.0)

    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_features("tests/nonexistent_file.ll")

    def test_empty_ir_text(self):
        features = self.extractor.extract_from_text("")
        self.assertEqual(features["instruction_count"], 0.0)
        self.assertEqual(features["basic_block_count"], 0.0)


if __name__ == "__main__":
    unittest.main()
