"""
Random Forest Ensemble Implementation in Pure Python
Bagging ensemble of CART decision trees with bootstrap sampling and feature subsampling.
"""

import random
from typing import List, Dict, Any, Optional, Union, Tuple
from src.ml.decision_tree import DecisionTree


class RandomForest:
    """Bagging ensemble of Decision Trees for Classification and Regression."""

    def __init__(
        self,
        task: str = "classification",
        n_estimators: int = 20,
        max_depth: int = 5,
        min_samples_split: int = 2,
        max_features: Optional[Union[int, str]] = "sqrt",
        random_state: int = 42
    ):
        self.task = task
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.random_state = random_state
        self.trees: List[DecisionTree] = []
        self.feature_importances_: Dict[int, float] = {}

    def _bootstrap_sample(
        self,
        X: List[List[float]],
        y: List[Any],
        rng: random.Random
    ) -> Tuple[List[List[float]], List[Any]]:
        n_samples = len(X)
        indices = [rng.randint(0, n_samples - 1) for _ in range(n_samples)]
        return [X[i] for i in indices], [y[i] for i in indices]

    def fit(self, X: List[List[float]], y: List[Any]):
        """Fits an ensemble of trees on bootstrap samples."""
        rng = random.Random(self.random_state)
        self.trees = []
        n_features = len(X[0])
        accumulated_importances: Dict[int, float] = {i: 0.0 for i in range(n_features)}

        for _ in range(self.n_estimators):
            X_boot, y_boot = self._bootstrap_sample(X, y, rng)
            tree = DecisionTree(
                task=self.task,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                max_features=self.max_features
            )
            tree.fit(X_boot, y_boot)
            self.trees.append(tree)

            for feat_idx, imp in tree.feature_importances_.items():
                accumulated_importances[feat_idx] += imp

        # Normalize averaged feature importances
        total_imp = sum(accumulated_importances.values())
        if total_imp > 0:
            self.feature_importances_ = {
                k: v / total_imp for k, v in accumulated_importances.items()
            }
        else:
            self.feature_importances_ = accumulated_importances

    def predict_one(self, x: List[float]) -> Any:
        """Predicts for a single instance using ensemble voting / averaging."""
        preds = [tree.predict_one(x) for tree in self.trees]
        if self.task == "classification":
            counts: Dict[Any, int] = {}
            for p in preds:
                counts[p] = counts.get(p, 0) + 1
            return max(counts.items(), key=lambda item: item[1])[0]
        else:
            return sum(preds) / len(preds)

    def predict(self, X: List[List[float]]) -> List[Any]:
        """Predicts for a collection of instances."""
        return [self.predict_one(x) for x in X]

    def predict_proba(self, x: List[float]) -> Dict[Any, float]:
        """Returns class probabilities (vote proportions) for classification."""
        if self.task != "classification":
            raise ValueError("predict_proba only available for classification")
        preds = [tree.predict_one(x) for tree in self.trees]
        counts: Dict[Any, int] = {}
        for p in preds:
            counts[p] = counts.get(p, 0) + 1
        n = float(len(preds))
        return {cls: count / n for cls, count in counts.items()}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "feature_importances": {str(k): round(v, 6) for k, v in self.feature_importances_.items()},
            "trees": [tree.to_dict() for tree in self.trees]
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RandomForest":
        rf = cls(
            task=d["task"],
            n_estimators=d["n_estimators"],
            max_depth=d["max_depth"],
            min_samples_split=d["min_samples_split"]
        )
        rf.feature_importances_ = {int(k): float(v) for k, v in d.get("feature_importances", {}).items()}
        rf.trees = [DecisionTree.from_dict(t) for t in d.get("trees", [])]
        return rf
