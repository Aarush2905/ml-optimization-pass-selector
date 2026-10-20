"""
Plot & Visual Report Generator
Generates publication-quality SVG and PNG visualizations for Review 2 presentation.
Pure-Python SVG rendering ensures zero external dependencies, with optional matplotlib support.
"""

import os
import sys
import csv
import json
import math
from typing import Callable, Dict, List, Any, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def generate_svg_bar_chart(
    title: str,
    categories: List[str],
    series_data: Dict[str, List[float]],
    colors: Dict[str, str],
    y_label: str,
    output_path: str,
    width: int = 900,
    height: int = 500,
    margin_bottom: int = 90
):
    """
    Renders a multi-series grouped bar chart as a clean, responsive vector SVG file.
    """
    margin_left = 80
    margin_right = 160
    margin_top = 60

    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    # Find max y
    all_vals = [v for s in series_data.values() for v in s]
    max_val = max(all_vals) if all_vals else 1.0
    # Add 15% headroom
    max_y = max_val * 1.15

    n_cats = len(categories)
    n_series = len(series_data)
    cat_w = plot_w / max(n_cats, 1)
    bar_w = (cat_w * 0.7) / max(n_series, 1)

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;">',
        f'  <style>',
        f'    .title {{ font-size: 18px; font-weight: bold; fill: #1e293b; }}',
        f'    .axis-label {{ font-size: 12px; fill: #64748b; font-weight: 500; }}',
        f'    .cat-label {{ font-size: 11px; fill: #334155; }}',
        f'    .grid {{ stroke: #e2e8f0; stroke-dasharray: 3,3; }}',
        f'    .bar:hover {{ opacity: 0.85; }}',
        f'  </style>',
        f'  <text x="{width / 2}" y="30" text-anchor="middle" class="title">{title}</text>',
    ]

    # Y-axis grid lines (5 intervals)
    for i in range(6):
        ratio = i / 5.0
        val = max_y * (1.0 - ratio)
        y_pos = margin_top + ratio * plot_h
        svg_lines.append(f'  <line x1="{margin_left}" y1="{y_pos}" x2="{margin_left + plot_w}" y2="{y_pos}" class="grid" />')
        svg_lines.append(f'  <text x="{margin_left - 10}" y="{y_pos + 4}" text-anchor="end" class="axis-label">{val:.2f}</text>')

    # Y-axis label
    svg_lines.append(
        f'  <text transform="rotate(-90)" x="-{margin_top + plot_h / 2}" y="25" text-anchor="middle" class="axis-label">{y_label}</text>'
    )

    # X-axis line
    svg_lines.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{margin_left + plot_w}" y2="{margin_top + plot_h}" stroke="#94a3b8" stroke-width="1.5" />')

    # Bars
    series_names = list(series_data.keys())
    for cat_idx, cat in enumerate(categories):
        cat_x = margin_left + cat_idx * cat_w
        group_x = cat_x + (cat_w - bar_w * n_series) / 2

        # Cat label
        svg_lines.append(
            f'  <text transform="rotate(-35 {group_x + (bar_w * n_series)/2} {margin_top + plot_h + 15})" '
            f'x="{group_x + (bar_w * n_series)/2}" y="{margin_top + plot_h + 15}" text-anchor="end" class="cat-label">{cat}</text>'
        )

        for s_idx, s_name in enumerate(series_names):
            val = series_data[s_name][cat_idx]
            bar_h = (val / max_y) * plot_h if max_y > 0 else 0
            b_x = group_x + s_idx * bar_w
            b_y = margin_top + plot_h - bar_h
            color = colors.get(s_name, "#3b82f6")
            svg_lines.append(
                f'  <rect x="{b_x:.1f}" y="{b_y:.1f}" width="{bar_w * 0.9:.1f}" height="{bar_h:.1f}" fill="{color}" rx="2" class="bar">'
                f'<title>{s_name} on {cat}: {val:.3f}</title></rect>'
            )

    # Legend
    leg_x = margin_left + plot_w + 20
    leg_y = margin_top + 10
    for idx, s_name in enumerate(series_names):
        c = colors.get(s_name, "#3b82f6")
        svg_lines.append(f'  <rect x="{leg_x}" y="{leg_y + idx * 24}" width="14" height="14" fill="{c}" rx="3" />')
        svg_lines.append(f'  <text x="{leg_x + 22}" y="{leg_y + idx * 24 + 11}" class="axis-label" fill="#1e293b">{s_name}</text>')

    svg_lines.append('</svg>')

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))


def geometric_mean(values: List[float]) -> float:
    """Geometric mean, the standard way to average speedup ratios across programs."""
    positive = [v for v in values if v > 0]
    if not positive:
        return 0.0
    return math.exp(sum(math.log(v) for v in positive) / len(positive))


def tertile_cuts(values: List[float]) -> Tuple[float, float]:
    """Returns the 1/3 and 2/3 cut points so programs split into roughly equal low/mid/high groups."""
    s = sorted(values)
    n = len(s)
    return s[max(math.ceil(n / 3) - 1, 0)], s[max(math.ceil(2 * n / 3) - 1, 0)]


def _fmt(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"


def tertile_grouper(feature: str, names: Tuple[str, str, str], values: List[float]) -> Callable[[Dict[str, float]], str]:
    lo, hi = tertile_cuts(values)

    def label(f: Dict[str, float]) -> str:
        v = f[feature]
        if v <= lo:
            return f"{names[0]} (<= {_fmt(lo)})"
        if v <= hi:
            return f"{names[1]} ({_fmt(lo)}-{_fmt(hi)}]"
        return f"{names[2]} (> {_fmt(hi)})"
    return label


FeatureGrouper = Tuple[str, Callable[[Dict[str, float]], str]]


def build_feature_groupers(program_features: Dict[str, Dict[str, float]]) -> Dict[str, FeatureGrouper]:
    """
    Defines the feature dimensions used to categorize results.
    Each entry maps a dimension to (underlying feature, function giving a program's group label).
    """
    feats = list(program_features.values())
    mem_median = sorted(f["mem_to_total_ratio"] for f in feats)[len(feats) // 2]

    def loop_label(f: Dict[str, float]) -> str:
        n = f["loop_count"]
        if n == 0:
            return "No loops"
        if n <= 3:
            return "Few loops (1-3)"
        return "Many loops (4+)"

    return {
        "recursion": ("is_recursive", lambda f: "Recursive" if f["is_recursive"] >= 1 else "Non-recursive"),
        "branch_depth": ("max_branch_depth", tertile_grouper(
            "max_branch_depth", ("Shallow", "Moderate", "Deep"), [f["max_branch_depth"] for f in feats])),
        "loop_count": ("loop_count", loop_label),
        "memory_intensity": ("mem_to_total_ratio", lambda f: (
            f"Memory-heavy (> {mem_median:.2f})" if f["mem_to_total_ratio"] > mem_median
            else f"Compute-heavy (<= {mem_median:.2f})")),
        "program_size": ("instruction_count", tertile_grouper(
            "instruction_count", ("Small", "Medium", "Large"), [f["instruction_count"] for f in feats])),
    }


def generate_feature_category_report(
    summary_rows: List[Dict[str, Any]],
    groupers: Dict[str, FeatureGrouper],
    program_features: Dict[str, Dict[str, float]],
    output_csv: str = "results/feature_category_summary.csv",
    plots_dir: str = "plots"
) -> List[Dict[str, Any]]:
    """
    Aggregates per-program results by static program feature (recursion, branch depth, ...)
    instead of by program name. Raw times are not comparable across programs, so each group
    reports geometric-mean speedups and ML win rates (ML = leave-one-out prediction), plus the
    best candidate strategy's speedup as an upper bound for the candidate pool.
    """
    category_rows: List[Dict[str, Any]] = []

    for dim, (feature, grouper) in groupers.items():
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for row in summary_rows:
            groups.setdefault(grouper(program_features[row["program"]]), []).append(row)

        # Order groups low -> high by their underlying feature value
        def group_order(label: str) -> float:
            vals = [program_features[m["program"]][feature] for m in groups[label]]
            return sum(vals) / len(vals)

        dim_rows = []
        for label in sorted(groups, key=group_order):
            members = groups[label]
            n = len(members)
            dim_rows.append({
                "dimension": dim,
                "group": label,
                "n_programs": n,
                "programs": " ".join(sorted(m["program"] for m in members)),
                "geomean_ml_speedup_vs_o0": round(geometric_mean([m["o0_time_ms"] / m["ml_time_ms"] for m in members if m["ml_time_ms"] > 0]), 3),
                "geomean_ml_speedup_vs_o2": round(geometric_mean([m["ml_speedup_vs_o2"] for m in members]), 3),
                "geomean_ml_speedup_vs_o3": round(geometric_mean([m["ml_speedup_vs_o3"] for m in members]), 3),
                "geomean_best_candidate_speedup_vs_o2": round(geometric_mean([m["best_candidate_speedup_vs_o2"] for m in members]), 3),
                "ml_win_rate_vs_o2": round(sum(1 for m in members if m["ml_beats_o2"] == "YES") / n, 3),
                "ml_win_rate_vs_o3": round(sum(1 for m in members if m["ml_beats_o3"] == "YES") / n, 3),
            })
        category_rows.extend(dim_rows)

        out_svg = os.path.join(plots_dir, f"speedup_by_{dim}.svg")
        generate_svg_bar_chart(
            title=f"ML Speedup by {dim.replace('_', ' ').title()} (geometric mean, > 1.0x = faster)",
            categories=[f"{r['group']} n={r['n_programs']}" for r in dim_rows],
            series_data={
                "ML vs -O2 Speedup": [r["geomean_ml_speedup_vs_o2"] for r in dim_rows],
                "ML vs -O3 Speedup": [r["geomean_ml_speedup_vs_o3"] for r in dim_rows],
                "Best candidate vs -O2": [r["geomean_best_candidate_speedup_vs_o2"] for r in dim_rows],
            },
            colors={"ML vs -O2 Speedup": "#6366f1", "ML vs -O3 Speedup": "#ec4899",
                    "Best candidate vs -O2": "#94a3b8"},
            y_label="Geomean Speedup (x) [Higher is Better]",
            output_path=out_svg,
            height=560,
            margin_bottom=150
        )
        print(f"[Plot Generated] {out_svg}")

    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(category_rows[0].keys()))
        writer.writeheader()
        writer.writerows(category_rows)
    print(f"[Summary Exported] {output_csv}")

    print("\nResults by program feature (geomean ML speedup vs -O2 / -O3, win rate vs -O2):")
    for r in category_rows:
        print(f"  {r['dimension']:<17} {r['group']:<28} n={r['n_programs']:<3} "
              f"{r['geomean_ml_speedup_vs_o2']:.2f}x / {r['geomean_ml_speedup_vs_o3']:.2f}x  "
              f"wins {r['ml_win_rate_vs_o2'] * 100:.0f}%")

    return category_rows


def generate_all_plots():
    """Generates the full visual suite comparing ML, O0, O2, and O3."""
    dataset_path = "data/optimization_dataset.csv"
    baseline_path = "data/baseline_results.csv"

    if not os.path.exists(dataset_path) or not os.path.exists(baseline_path):
        print("[ERROR] Required data files missing. Run dataset generation and baseline benchmark first.")
        return

    # Parse baselines
    baselines: Dict[str, Dict[str, float]] = {}
    with open(baseline_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            prog = r["program"]
            opt = r["optimization"]
            if prog not in baselines:
                baselines[prog] = {}
            baselines[prog][opt] = float(r["execution_time_ms"])

    # The ML result for each program is the model's leave-one-out prediction: the strategy chosen
    # by a model trained on all *other* programs. Using the full model (or the best candidate)
    # would evaluate the selector on its own training data.
    model_path = "models/trained_selector.json"
    loo_predictions: Dict[str, str] = {}
    if os.path.exists(model_path):
        with open(model_path, "r", encoding="utf-8") as f:
            loo_predictions = json.load(f).get("metadata", {}).get("loo_predictions", {})
    if not loo_predictions:
        print(f"[ERROR] {model_path} has no leave-one-out predictions. Re-run `python3 src/main.py --train` first.")
        return

    # Parse every measured strategy per program, the best candidate, and static IR features
    from src.features.extractor import IRFeatureExtractor
    strategy_times: Dict[str, Dict[str, float]] = {}
    best_strategy: Dict[str, str] = {}
    program_features: Dict[str, Dict[str, float]] = {}
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [fn for fn in IRFeatureExtractor.FEATURE_NAMES if fn not in (reader.fieldnames or [])]
        if missing:
            print(f"[ERROR] {dataset_path} is missing feature columns {missing}. "
                  f"Re-run experiments/generate_dataset.py first.")
            return
        for r in reader:
            prog = r["program"]
            if prog not in program_features:
                program_features[prog] = {fn: float(r[fn]) for fn in IRFeatureExtractor.FEATURE_NAMES}
            strategy_times.setdefault(prog, {})[r["strategy"]] = float(r["execution_time_ms"])
            if int(r.get("is_best_strategy", 0)) == 1:
                best_strategy[prog] = r["strategy"]

    progs = sorted(set(baselines) & set(best_strategy) & set(loo_predictions))

    categories = progs
    o0_times = [baselines[p].get("O0", 0.0) for p in progs]
    o2_times = [baselines[p].get("O2", 0.0) for p in progs]
    o3_times = [baselines[p].get("O3", 0.0) for p in progs]
    best_times = [strategy_times[p][best_strategy[p]] for p in progs]

    # If the predicted strategy failed on a program (no measured row), the compiler would have to
    # fall back to the unoptimized build, so the O0 time is used and the row is flagged.
    ml_times = []
    ml_fallback = []
    for p, o0 in zip(progs, o0_times):
        pred = loo_predictions[p]
        if pred in strategy_times[p]:
            ml_times.append(strategy_times[p][pred])
            ml_fallback.append(False)
        else:
            ml_times.append(o0)
            ml_fallback.append(True)

    series_data = {
        "-O2 (Default)": o2_times,
        "-O3 (Default)": o3_times,
        "ML (leave-one-out)": ml_times
    }

    colors = {
        "-O2 (Default)": "#3b82f6",
        "-O3 (Default)": "#10b981",
        "ML (leave-one-out)": "#8b5cf6"
    }

    # 1. Execution time comparison
    out_svg = "plots/execution_time_comparison.svg"
    generate_svg_bar_chart(
        title="Execution Time Comparison: ML (leave-one-out) vs -O2 vs -O3",
        categories=categories,
        series_data=series_data,
        colors=colors,
        y_label="Execution Time (ms) [Lower is Better]",
        output_path=out_svg
    )
    print(f"[Plot Generated] {out_svg}")

    # 2. Relative speedup vs O2
    speedup_data = {
        "ML vs -O2 Speedup": [round((o2 / ml if ml > 0 else 1.0), 3) for o2, ml in zip(o2_times, ml_times)],
        "ML vs -O3 Speedup": [round((o3 / ml if ml > 0 else 1.0), 3) for o3, ml in zip(o3_times, ml_times)]
    }
    speedup_colors = {
        "ML vs -O2 Speedup": "#6366f1",
        "ML vs -O3 Speedup": "#ec4899"
    }
    out_speedup = "plots/speedup_comparison.svg"
    generate_svg_bar_chart(
        title="Relative Speedup of ML (leave-one-out) Strategy (> 1.0x indicates ML is Faster)",
        categories=categories,
        series_data=speedup_data,
        colors=speedup_colors,
        y_label="Speedup Ratio (x) [Higher is Better]",
        output_path=out_speedup
    )
    print(f"[Plot Generated] {out_speedup}")

    # 3. Export consolidated comparison summary table (one row per program, tagged with its feature groups)
    summary_csv = "results/comparison_summary.csv"
    os.makedirs("results", exist_ok=True)
    groupers = build_feature_groupers({p: program_features[p] for p in progs})
    summary_rows = []
    wins_vs_o2 = 0
    wins_vs_o3 = 0
    best_wins_vs_o2 = 0
    picked_best = 0

    for p, o0, o2, o3, ml, best, fell_back in zip(progs, o0_times, o2_times, o3_times, ml_times, best_times, ml_fallback):
        sp_o2 = (o2 / ml) if ml > 0 else 1.0
        sp_o3 = (o3 / ml) if ml > 0 else 1.0
        if ml <= o2:
            wins_vs_o2 += 1
        if ml <= o3:
            wins_vs_o3 += 1
        if best <= o2:
            best_wins_vs_o2 += 1
        if loo_predictions[p] == best_strategy[p]:
            picked_best += 1

        row = {
            "program": p,
            "o0_time_ms": o0,
            "o2_time_ms": o2,
            "o3_time_ms": o3,
            "ml_time_ms": ml,
            "ml_strategy": loo_predictions[p],
            "ml_fallback": "YES" if fell_back else "NO",
            "best_candidate_strategy": best_strategy[p],
            "best_candidate_time_ms": best,
            "ml_picked_best": "YES" if loo_predictions[p] == best_strategy[p] else "NO",
            "ml_speedup_vs_o2": round(sp_o2, 3),
            "ml_speedup_vs_o3": round(sp_o3, 3),
            "best_candidate_speedup_vs_o2": round((o2 / best) if best > 0 else 1.0, 3),
            "ml_beats_o2": "YES" if ml <= o2 else "NO",
            "ml_beats_o3": "YES" if ml <= o3 else "NO",
            "is_recursive": int(program_features[p]["is_recursive"]),
            "max_branch_depth": int(program_features[p]["max_branch_depth"]),
            "loop_count": int(program_features[p]["loop_count"]),
        }
        for dim, (_, grouper) in groupers.items():
            row[f"group_{dim}"] = grouper(program_features[p])
        summary_rows.append(row)

    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[Summary Exported] {summary_csv}")
    print(f"Summary: ML matched or outperformed -O2 on {wins_vs_o2}/{len(progs)} benchmarks ({wins_vs_o2/len(progs)*100:.1f}%)")
    print(f"Summary: ML matched or outperformed -O3 on {wins_vs_o3}/{len(progs)} benchmarks ({wins_vs_o3/len(progs)*100:.1f}%)")
    print(f"Summary: ML (leave-one-out) picked the best candidate strategy on {picked_best}/{len(progs)} programs")
    print(f"Summary: Best candidate (upper bound) matched or outperformed -O2 on {best_wins_vs_o2}/{len(progs)} benchmarks")
    if any(ml_fallback):
        print(f"[WARN] Predicted strategy failed (O0 fallback) on: {', '.join(p for p, fb in zip(progs, ml_fallback) if fb)}")

    # 4. Results categorized by program features (recursion, branch depth, loops, memory, size)
    generate_feature_category_report(summary_rows, groupers, program_features)


if __name__ == "__main__":
    generate_all_plots()
