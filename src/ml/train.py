"""
Model Training Script
Trains the Machine-Learning-Guided Optimization Pass Selector, performs validation,
displays feature importance rankings, and serializes the model.
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.ml.model_wrapper import PassSelectorModel


def train_and_evaluate(
    dataset_path: str = "data/optimization_dataset.csv",
    model_output: str = "models/trained_selector.json",
    model_type: str = "random_forest"
):
    print("=" * 65)
    print("   ML-GUIDED OPTIMIZATION PASS SELECTOR — MODEL TRAINING")
    print("=" * 65)
    print(f"Dataset path: {dataset_path}")
    print(f"Model type:   {model_type}")

    if not os.path.exists(dataset_path):
        print(f"\n[ERROR] Dataset {dataset_path} does not exist.")
        print("Run `python3 experiments/generate_dataset.py` first.")
        sys.exit(1)

    model = PassSelectorModel(model_type=model_type)
    metrics = model.train(dataset_path)

    print("\n--- Training Results ---")
    print(f"Samples analyzed:          {metrics['n_samples']}")
    print(f"Training accuracy:         {metrics['training_accuracy'] * 100:.1f}%")
    print(f"Leave-One-Out CV accuracy: {metrics['loocv_accuracy'] * 100:.1f}%")
    print(f"Recognized strategy classes: {', '.join(metrics['classes'])}")

    print("\n--- Top Feature Importances ---")
    for feat, imp in list(metrics["feature_importances"].items())[:8]:
        bar = "█" * int(imp * 30)
        print(f"  {feat:<22} {imp:>6.4f} | {bar}")

    model.save(model_output)
    print(f"\n[SUCCESS] Model weights saved to: {model_output}")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ML pass selector model.")
    parser.add_argument("--dataset", default="data/optimization_dataset.csv", help="Path to training CSV")
    parser.add_argument("--output", default="models/trained_selector.json", help="Path to save trained model")
    parser.add_argument("--type", default="random_forest", choices=["random_forest", "decision_tree"], help="Model type")
    args = parser.parse_args()

    train_and_evaluate(args.dataset, args.output, args.type)
