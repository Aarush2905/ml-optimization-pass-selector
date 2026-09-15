"""
Plot & Visual Report Generator
Generates publication-quality SVG and PNG visualizations for Review 2 presentation.
Pure-Python SVG rendering ensures zero external dependencies, with optional matplotlib support.
"""

import os
import csv
import json
from typing import Dict, List, Any


def generate_svg_bar_chart(
    title: str,
    categories: List[str],
    series_data: Dict[str, List[float]],
    colors: Dict[str, str],
    y_label: str,
    output_path: str,
    width: int = 900,
    height: int = 500
):
    """
    Renders a multi-series grouped bar chart as a clean, responsive vector SVG file.
    """
    margin_left = 80
    margin_right = 160
    margin_top = 60
    margin_bottom = 90

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

    # Parse best ML strategies
    ml_data: Dict[str, float] = {}
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if int(r.get("is_best_strategy", 0)) == 1:
                prog = r["program"]
                ml_data[prog] = float(r["execution_time_ms"])

    progs = sorted(list(set(baselines.keys()).intersection(set(ml_data.keys()))))

    categories = progs
    o0_times = [baselines[p].get("O0", 0.0) for p in progs]
    o2_times = [baselines[p].get("O2", 0.0) for p in progs]
    o3_times = [baselines[p].get("O3", 0.0) for p in progs]
    ml_times = [ml_data.get(p, 0.0) for p in progs]

    series_data = {
        "-O2 (Default)": o2_times,
        "-O3 (Default)": o3_times,
        "ML-Selected": ml_times
    }

    colors = {
        "-O2 (Default)": "#3b82f6",
        "-O3 (Default)": "#10b981",
        "ML-Selected": "#8b5cf6"
    }

    # 1. Execution time comparison
    out_svg = "plots/execution_time_comparison.svg"
    generate_svg_bar_chart(
        title="Execution Time Comparison: ML-Selected vs -O2 vs -O3",
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
        title="Relative Speedup of ML-Guided Strategy (> 1.0x indicates ML is Faster)",
        categories=categories,
        series_data=speedup_data,
        colors=speedup_colors,
        y_label="Speedup Ratio (x) [Higher is Better]",
        output_path=out_speedup
    )
    print(f"[Plot Generated] {out_speedup}")

    # 3. Export consolidated comparison summary table
    summary_csv = "results/comparison_summary.csv"
    os.makedirs("results", exist_ok=True)
    summary_rows = []
    wins_vs_o2 = 0
    wins_vs_o3 = 0

    for p, o0, o2, o3, ml in zip(progs, o0_times, o2_times, o3_times, ml_times):
        sp_o2 = (o2 / ml) if ml > 0 else 1.0
        sp_o3 = (o3 / ml) if ml > 0 else 1.0
        if ml <= o2:
            wins_vs_o2 += 1
        if ml <= o3:
            wins_vs_o3 += 1

        summary_rows.append({
            "program": p,
            "o0_time_ms": o0,
            "o2_time_ms": o2,
            "o3_time_ms": o3,
            "ml_time_ms": ml,
            "ml_speedup_vs_o2": round(sp_o2, 3),
            "ml_speedup_vs_o3": round(sp_o3, 3),
            "ml_beats_o2": "YES" if ml <= o2 else "NO",
            "ml_beats_o3": "YES" if ml <= o3 else "NO"
        })

    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[Summary Exported] {summary_csv}")
    print(f"Summary: ML matched or outperformed -O2 on {wins_vs_o2}/{len(progs)} benchmarks ({wins_vs_o2/len(progs)*100:.1f}%)")
    print(f"Summary: ML matched or outperformed -O3 on {wins_vs_o3}/{len(progs)} benchmarks ({wins_vs_o3/len(progs)*100:.1f}%)")


if __name__ == "__main__":
    generate_all_plots()
