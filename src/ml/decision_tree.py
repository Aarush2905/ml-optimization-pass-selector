"""
CART Decision Tree Implementation in Pure Python
Supports both Classification (Gini Impurity) and Regression (MSE Reduction).
Fully transparent and inspectable for Review 2 viva demonstrations.
"""

import math
from typing import List, Dict, Any, Optional, Tuple, Union


class TreeNode:
    """Represents a single decision node or leaf in the CART tree."""

    def __init__(
        self,
        feature_idx: Optional[int] = None,
        threshold: Optional[float] = None,
        left: Optional["TreeNode"] = None,
        right: Optional["TreeNode"] = None,
        value: Any = None,
        impurity: float = 0.0,
        n_samples: int = 0
    ):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value
        self.impurity = impurity
        self.n_samples = n_samples

    @property
    def is_leaf(self) -> bool:
        return self.value is not None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes node and descendants to a JSON-compatible dictionary."""
        d = {
            "feature_idx": self.feature_idx,
            "threshold": self.threshold,
            "value": self.value,
            "impurity": round(self.impurity, 6),
            "n_samples": self.n_samples,
            "is_leaf": self.is_leaf
        }
        if self.left:
            d["left"] = self.left.to_dict()
        if self.right:
            d["right"] = self.right.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TreeNode":
        """Deserializes node from dictionary."""
        node = cls(
            feature_idx=d.get("feature_idx"),
            threshold=d.get("threshold"),
            value=d.get("value"),
            impurity=d.get("impurity", 0.0),
            n_samples=d.get("n_samples", 0)
        )
        if "left" in d:
            node.left = cls.from_dict(d["left"])
        if "right" in d:
            node.right = cls.from_dict(d["right"])
        return node


class DecisionTree:
    """CART Decision Tree supporting classification and regression."""

    def __init__(
        self,
        task: str = "classification",
        max_depth: int = 6,
        min_samples_split: int = 2,
        max_features: Optional[Union[int, str]] = None
    ):
        self.task = task
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.root: Optional[TreeNode] = None
        self.feature_importances_: Dict[int, float] = {}

    def _gini(self, y: List[Any]) -> float:
        """Calculates Gini Impurity: 1 - sum(p_i^2)."""
        if not y:
            return 0.0
        counts: Dict[Any, int] = {}
        for val in y:
            counts[val] = counts.get(val, 0) + 1
        n = float(len(y))
        gini = 1.0 - sum((c / n) ** 2 for c in counts.values())
        return gini

    def _mse(self, y: List[float]) -> float:
        """Calculates Mean Squared Error."""
        if not y:
            return 0.0
        mean_y = sum(y) / len(y)
        return sum((v - mean_y) ** 2 for v in y) / len(y)

    def _calculate_leaf_value(self, y: List[Any]) -> Any:
        """Majority class for classification, mean for regression."""
        if self.task == "classification":
            counts: Dict[Any, int] = {}
            for v in y:
                counts[v] = counts.get(v, 0) + 1
            return max(counts.items(), key=lambda x: x[1])[0]
        else:
            return sum(y) / len(y)

    def _split(self, X: List[List[float]], y: List[Any], feat_idx: int, thresh: float):
        X_left, y_left, X_right, y_right = [], [], [], []
        for xi, yi in zip(X, y):
            if xi[feat_idx] <= thresh:
                X_left.append(xi)
                y_left.append(yi)
            else:
                X_right.append(xi)
                y_right.append(yi)
        return X_left, y_left, X_right, y_right

    def _best_split(
        self,
        X: List[List[float]],
        y: List[Any],
        candidate_features: List[int]
    ) -> Tuple[Optional[int], Optional[float], float]:
        best_gain = -1.0
        best_feat = None
        best_thresh = None

        parent_impurity = self._gini(y) if self.task == "classification" else self._mse(y)
        n_samples = len(y)

        for feat_idx in candidate_features:
            values = sorted(list(set(row[feat_idx] for row in X)))
            if len(values) <= 1:
                continue

            # Candidate thresholds as midpoints
            thresholds = [(values[i] + values[i+1]) / 2.0 for i in range(len(values) - 1)]

            for thresh in thresholds:
                X_l, y_l, X_r, y_r = self._split(X, y, feat_idx, thresh)
                if len(y_l) == 0 or len(y_r) == 0:
                    continue

                if self.task == "classification":
                    imp_l = self._gini(y_l)
                    imp_r = self._gini(y_r)
                else:
                    imp_l = self._mse(y_l)
                    imp_r = self._mse(y_r)

                child_impurity = (len(y_l) / n_samples) * imp_l + (len(y_r) / n_samples) * imp_r
                gain = parent_impurity - child_impurity

                if gain > best_gain:
                    best_gain = gain
                    best_feat = feat_idx
                    best_thresh = thresh

        return best_feat, best_thresh, (best_gain if best_gain > 0 else 0.0)

    def _build_tree(
        self,
        X: List[List[float]],
        y: List[Any],
        depth: int,
        feature_indices: List[int]
    ) -> TreeNode:
        n_samples = len(y)
        current_impurity = self._gini(y) if self.task == "classification" else self._mse(y)

        # Check stopping conditions
        if (
            depth >= self.max_depth
            or n_samples < self.min_samples_split
            or current_impurity == 0.0
            or len(set(y)) == 1
        ):
            return TreeNode(
                value=self._calculate_leaf_value(y),
                impurity=current_impurity,
                n_samples=n_samples
            )

        # Determine feature candidates for split
        import random
        if isinstance(self.max_features, int):
            k = min(self.max_features, len(feature_indices))
            candidate_feats = random.sample(feature_indices, k)
        elif self.max_features == "sqrt":
            k = max(1, int(math.sqrt(len(feature_indices))))
            candidate_feats = random.sample(feature_indices, k)
        else:
            candidate_feats = feature_indices

        best_feat, best_thresh, gain = self._best_split(X, y, candidate_feats)

        if best_feat is None or gain <= 1e-7:
            return TreeNode(
                value=self._calculate_leaf_value(y),
                impurity=current_impurity,
                n_samples=n_samples
            )

        # Record feature importance (gain * sample proportion)
        weight = n_samples
        self.feature_importances_[best_feat] = (
            self.feature_importances_.get(best_feat, 0.0) + gain * weight
        )

        X_l, y_l, X_r, y_r = self._split(X, y, best_feat, best_thresh)
        left_child = self._build_tree(X_l, y_l, depth + 1, feature_indices)
        right_child = self._build_tree(X_r, y_r, depth + 1, feature_indices)

        return TreeNode(
            feature_idx=best_feat,
            threshold=best_thresh,
            left=left_child,
            right=right_child,
            impurity=current_impurity,
            n_samples=n_samples
        )

    def fit(self, X: List[List[float]], y: List[Any]):
        """Fits the tree on feature matrix X and label/target vector y."""
        if not X or not y:
            raise ValueError("Training data X or y is empty")
        n_features = len(X[0])
        feature_indices = list(range(n_features))
        self.feature_importances_ = {i: 0.0 for i in feature_indices}

        self.root = self._build_tree(X, y, depth=0, feature_indices=feature_indices)

        # Normalize feature importances
        total_imp = sum(self.feature_importances_.values())
        if total_imp > 0:
            for k in self.feature_importances_:
                self.feature_importances_[k] /= total_imp

    def predict_one(self, x: List[float]) -> Any:
        """Predicts for a single feature vector."""
        if not self.root:
            raise RuntimeError("Tree has not been fitted")

        curr = self.root
        while not curr.is_leaf:
            if x[curr.feature_idx] <= curr.threshold:
                curr = curr.left
            else:
                curr = curr.right
        return curr.value

    def predict(self, X: List[List[float]]) -> List[Any]:
        """Predicts for multiple feature vectors."""
        return [self.predict_one(row) for row in X]

    def print_tree(self, feature_names: Optional[List[str]] = None, indent: str = "") -> str:
        """Returns readable string visualization of the tree rules for viva examination."""
        def _render(node: Optional[TreeNode], depth: int, prefix: str) -> str:
            if not node:
                return ""
            if node.is_leaf:
                return f"{prefix}--> Class/Value: {node.value} (samples={node.n_samples}, imp={node.impurity:.3f})\n"

            f_name = (
                feature_names[node.feature_idx]
                if feature_names and node.feature_idx < len(feature_names)
                else f"F{node.feature_idx}"
            )
            s = f"{prefix}if {f_name} <= {node.threshold:.3f}:\n"
            s += _render(node.left, depth + 1, prefix + "  |")
            s += f"{prefix}else (if {f_name} > {node.threshold:.3f}):\n"
            s += _render(node.right, depth + 1, prefix + "  |")
            return s

        return _render(self.root, 0, indent)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "feature_importances": {str(k): round(v, 6) for k, v in self.feature_importances_.items()},
            "root": self.root.to_dict() if self.root else None
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DecisionTree":
        tree = cls(
            task=d["task"],
            max_depth=d["max_depth"],
            min_samples_split=d["min_samples_split"]
        )
        tree.feature_importances_ = {int(k): float(v) for k, v in d.get("feature_importances", {}).items()}
        if d.get("root"):
            tree.root = TreeNode.from_dict(d["root"])
        return tree
