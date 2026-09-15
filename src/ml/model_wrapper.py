"""
Pass Selector Model Wrapper
Unified ML interface for feature parsing, model training, persistence, and pass sequence prediction.
"""

import os
import csv
import json
from typing import Dict, List, Any, Optional, Tuple

from src.features.extractor import IRFeatureExtractor
from src.optimization.sequence_generator import SequenceGenerator
from src.ml.decision_tree import DecisionTree
from src.ml.random_forest import RandomForest


class PassSelectorModel:
    """Orchestrates ML-guided selection of optimization pass sequences from IR features."""

    def __init__(self, model_type: str = "random_forest", n_estimators: int = 25, max_depth: int = 5):
        self.model_type = model_type
        self.feature_names = IRFeatureExtractor.FEATURE_NAMES
        self.seq_gen = SequenceGenerator()

        if model_type == "random_forest":
            self.model = RandomForest(
                task="classification",
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42
            )
        else:
            self.model = DecisionTree(
                task="classification",
                max_depth=max_depth
            )

        self.is_trained = False
        self.training_metadata: Dict[str, Any] = {}

    def load_dataset(self, csv_path: str) -> Tuple[List[List[float]], List[str], List[str]]:
        """
        Loads training dataset from CSV.
        Extracts one training example per unique benchmark program using its best strategy.
        Returns (X, y, program_names).
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset not found at {csv_path}")

        records_by_prog: Dict[str, Dict[str, Any]] = {}
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                prog = row["program"]
                if prog not in records_by_prog:
                    records_by_prog[prog] = row
                elif int(row.get("is_best_strategy", 0)) == 1:
                    records_by_prog[prog] = row

        X: List[List[float]] = []
        y: List[str] = []
        program_names: List[str] = []

        for prog, row in sorted(records_by_prog.items()):
            feature_vector = [float(row[fn]) for fn in self.feature_names]
            target = row["best_strategy_target"]
            X.append(feature_vector)
            y.append(target)
            program_names.append(prog)

        return X, y, program_names

    def train(self, csv_path: str) -> Dict[str, Any]:
        """Trains the model on the dataset and returns training performance metrics."""
        X, y, prog_names = self.load_dataset(csv_path)

        if not X:
            raise ValueError(f"No valid training samples found in {csv_path}")

        self.model.fit(X, y)
        self.is_trained = True

        # Compute training accuracy
        preds = self.model.predict(X)
        correct = sum(1 for p, actual in zip(preds, y) if p == actual)
        accuracy = correct / len(y) if y else 0.0

        # Leave-One-Out Cross-Validation (LOOCV) for rigorous academic reporting
        loocv_correct = 0
        n_samples = len(X)
        if n_samples > 2:
            for i in range(n_samples):
                X_train = [X[j] for j in range(n_samples) if j != i]
                y_train = [y[j] for j in range(n_samples) if j != i]
                x_val = [X[i]]
                y_val = y[i]

                if self.model_type == "random_forest":
                    fold_model = RandomForest(
                        task="classification",
                        n_estimators=self.model.n_estimators,
                        max_depth=self.model.max_depth,
                        random_state=42 + i
                    )
                else:
                    fold_model = DecisionTree(
                        task="classification",
                        max_depth=self.model.max_depth
                    )
                fold_model.fit(X_train, y_train)
                val_pred = fold_model.predict(x_val)[0]
                if val_pred == y_val:
                    loocv_correct += 1

            loocv_acc = loocv_correct / n_samples
        else:
            loocv_acc = accuracy

        # Calculate feature importance rankings
        feat_importances = self.get_feature_importances()

        self.training_metadata = {
            "n_samples": n_samples,
            "training_accuracy": round(accuracy, 4),
            "loocv_accuracy": round(loocv_acc, 4),
            "feature_importances": feat_importances,
            "classes": sorted(list(set(y)))
        }

        return self.training_metadata

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Takes static IR features and predicts:
        - Best strategy name
        - Corresponding LLVM pass sequence
        - Confidence / probability distribution
        - Top contributing features
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained or loaded before prediction")

        x = [features.get(fn, 0.0) for fn in self.feature_names]

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(x)
            pred_strategy = max(probs.items(), key=lambda item: item[1])[0]
        else:
            pred_strategy = self.model.predict_one(x)
            probs = {pred_strategy: 1.0}

        try:
            passes = self.seq_gen.get_sequence(pred_strategy)
        except KeyError:
            # Fallback
            passes = ["mem2reg", "instcombine", "simplifycfg"]

        return {
            "strategy": pred_strategy,
            "passes": passes,
            "pass_string": ",".join(passes),
            "probabilities": {k: round(v, 4) for k, v in probs.items()},
            "confidence": round(probs.get(pred_strategy, 1.0), 4)
        }

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns sorted feature importances mapped to feature names."""
        if not self.is_trained:
            return {}

        raw_imp = self.model.feature_importances_
        results = {}
        for idx, imp in raw_imp.items():
            if idx < len(self.feature_names):
                results[self.feature_names[idx]] = round(imp, 4)

        # Sort descending
        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

    def save(self, file_path: str):
        """Saves trained model state and metadata to JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        data = {
            "model_type": self.model_type,
            "feature_names": self.feature_names,
            "metadata": self.training_metadata,
            "model_state": self.model.to_dict()
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, file_path: str):
        """Loads trained model state from JSON."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Model file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.model_type = data["model_type"]
        self.feature_names = data.get("feature_names", IRFeatureExtractor.FEATURE_NAMES)
        self.training_metadata = data.get("metadata", {})

        if self.model_type == "random_forest":
            self.model = RandomForest.from_dict(data["model_state"])
        else:
            self.model = DecisionTree.from_dict(data["model_state"])

        self.is_trained = True
