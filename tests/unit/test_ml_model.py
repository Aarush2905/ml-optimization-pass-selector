"""
Unit Tests for Machine Learning Models (DecisionTree, RandomForest, PassSelectorModel)
"""

import os
import tempfile
import unittest

from src.ml.decision_tree import DecisionTree
from src.ml.random_forest import RandomForest
from src.ml.model_wrapper import PassSelectorModel


class TestMLModels(unittest.TestCase):

    def setUp(self):
        # Synthetic separable dataset: 2 features, 2 classes
        self.X = [
            [1.0, 2.0],
            [1.5, 1.8],
            [2.0, 2.2],
            [8.0, 9.0],
            [8.5, 8.8],
            [9.0, 9.5]
        ]
        self.y = ["class_A", "class_A", "class_A", "class_B", "class_B", "class_B"]

    def test_decision_tree_fit_predict(self):
        tree = DecisionTree(task="classification", max_depth=3)
        tree.fit(self.X, self.y)
        preds = tree.predict(self.X)
        self.assertEqual(preds, self.y)

        # Test single prediction
        pred_a = tree.predict_one([1.2, 2.1])
        pred_b = tree.predict_one([8.2, 9.1])
        self.assertEqual(pred_a, "class_A")
        self.assertEqual(pred_b, "class_B")

        # Test tree serialization
        d = tree.to_dict()
        restored = DecisionTree.from_dict(d)
        self.assertEqual(restored.predict(self.X), self.y)

    def test_random_forest_fit_predict(self):
        rf = RandomForest(task="classification", n_estimators=10, max_depth=3, random_state=42)
        rf.fit(self.X, self.y)
        preds = rf.predict(self.X)
        self.assertEqual(preds, self.y)

        # Test probability prediction
        probs = rf.predict_proba([1.1, 1.9])
        self.assertGreater(probs.get("class_A", 0), 0.5)

    def test_pass_selector_wrapper_save_load(self):
        model = PassSelectorModel(model_type="random_forest", n_estimators=5)
        dataset_path = "data/optimization_dataset.csv"
        if os.path.exists(dataset_path):
            metrics = model.train(dataset_path)
            self.assertGreater(metrics["n_samples"], 0)
            self.assertGreater(metrics["training_accuracy"], 0.5)

            # Test save and load
            temp_model_path = os.path.join(tempfile.mkdtemp(), "test_model.json")
            model.save(temp_model_path)
            self.assertTrue(os.path.exists(temp_model_path))

            loaded = PassSelectorModel()
            loaded.load(temp_model_path)
            self.assertTrue(loaded.is_trained)


if __name__ == "__main__":
    unittest.main()
