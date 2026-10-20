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
        self.assertEqual(features["is_recursive"], 0.0)
        self.assertEqual(features["max_branch_depth"], 0.0)

    def test_feature_count(self):
        self.assertEqual(len(IRFeatureExtractor.FEATURE_NAMES), 25)
        features = self.extractor.extract_from_text(NESTED_IF_IR)
        self.assertEqual(len(self.extractor.to_feature_vector(features)), 25)

    def test_direct_recursion_detected(self):
        features = self.extractor.extract_from_text(RECURSIVE_IR)
        self.assertEqual(features["is_recursive"], 1.0)

    def test_mutual_recursion_detected(self):
        features = self.extractor.extract_from_text(MUTUAL_RECURSION_IR)
        self.assertEqual(features["is_recursive"], 1.0)

    def test_non_recursive_sample(self):
        features = self.extractor.extract_features("tests/sample.ll")
        self.assertEqual(features["is_recursive"], 0.0)
        self.assertGreaterEqual(features["max_branch_depth"], 1.0)

    def test_nested_branch_depth(self):
        # Two nested ifs -> two conditional branches on the deepest path
        features = self.extractor.extract_from_text(NESTED_IF_IR)
        self.assertEqual(features["is_recursive"], 0.0)
        self.assertEqual(features["max_branch_depth"], 2.0)

    def test_loop_back_edge_not_counted_twice(self):
        # A single loop header is one conditional branch; the back-edge must not inflate depth
        features = self.extractor.extract_from_text(LOOP_IR)
        self.assertEqual(features["max_branch_depth"], 1.0)

    def test_multiline_switch(self):
        # Case lines must become CFG edges (switch -> nested if = depth 2), not instructions
        features = self.extractor.extract_from_text(SWITCH_IR)
        self.assertEqual(features["max_branch_depth"], 2.0)
        self.assertEqual(features["cond_branch_count"], 2.0)
        # switch, icmp, br, 3x ret = 6 (case lines and "]" excluded)
        self.assertEqual(features["instruction_count"], 6.0)


RECURSIVE_IR = """
define dso_local i32 @fib(i32 noundef %0) {
  %2 = icmp sle i32 %0, 1
  br i1 %2, label %3, label %4

3:
  ret i32 %0

4:
  %5 = sub nsw i32 %0, 1
  %6 = call i32 @fib(i32 noundef %5)
  ret i32 %6
}
"""

MUTUAL_RECURSION_IR = """
define dso_local i32 @is_even(i32 noundef %0) {
  %2 = icmp eq i32 %0, 0
  br i1 %2, label %3, label %4

3:
  ret i32 1

4:
  %5 = sub nsw i32 %0, 1
  %6 = call i32 @is_odd(i32 noundef %5)
  ret i32 %6
}

define dso_local i32 @is_odd(i32 noundef %0) {
  %2 = icmp eq i32 %0, 0
  br i1 %2, label %3, label %4

3:
  ret i32 0

4:
  %5 = sub nsw i32 %0, 1
  %6 = call i32 @is_even(i32 noundef %5)
  ret i32 %6
}
"""

NESTED_IF_IR = """
define dso_local i32 @classify(i32 noundef %0) {
  %2 = icmp sgt i32 %0, 0
  br i1 %2, label %3, label %7

3:
  %4 = icmp sgt i32 %0, 10
  br i1 %4, label %5, label %6

5:
  ret i32 2

6:
  ret i32 1

7:
  %8 = call i32 (ptr, ...) @printf(ptr noundef null)
  ret i32 0
}
"""

SWITCH_IR = """
define dso_local i32 @dispatch(i32 noundef %0) {
  switch i32 %0, label %6 [
    i32 0, label %2
    i32 1, label %5
  ]

2:
  %3 = icmp sgt i32 %0, 10
  br i1 %3, label %4, label %5

4:
  ret i32 2

5:
  ret i32 1

6:
  ret i32 0
}
"""

LOOP_IR = """
define dso_local i32 @sum(i32 noundef %0) {
  br label %2

2:
  %3 = phi i32 [ 0, %1 ], [ %6, %5 ]
  %4 = icmp slt i32 %3, %0
  br i1 %4, label %5, label %7

5:
  %6 = add nsw i32 %3, 1
  br label %2

7:
  ret i32 %3
}
"""


if __name__ == "__main__":
    unittest.main()
