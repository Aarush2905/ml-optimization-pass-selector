"""
REST API & Web Dashboard Server
Serves the web dashboard and provides backend optimization API endpoints.
Zero external pip dependencies required (built with Python standard library http.server).
"""

import os
import sys
import json
import tempfile
import glob
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.llvm.compiler import LLVMCompiler
from src.llvm.pass_runner import PassRunner
from src.features.extractor import IRFeatureExtractor
from src.ml.model_wrapper import PassSelectorModel
from src.benchmarking.benchmark import BenchmarkEngine
from src.correctness.verifier import CorrectnessVerifier
from src.optimization.ordering_search import PassOrderingExplorer


class WebDashboardHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler providing REST API and serving Web Dashboard frontend."""

    def log_message(self, format, *args):
        # Suppress routine log messages for cleaner CLI output
        pass

    def _send_json(self, data: Any, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _send_file(self, file_path: str, content_type: str):
        if not os.path.exists(file_path):
            self.send_error(404, f"File not found: {file_path}")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            html_path = os.path.join(PROJECT_ROOT, "src", "web", "static", "index.html")
            self._send_file(html_path, "text/html; charset=utf-8")
        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            static_file = os.path.join(PROJECT_ROOT, "src", "web", "static", rel_path)
            content_type = "text/plain"
            if rel_path.endswith(".css"):
                content_type = "text/css"
            elif rel_path.endswith(".js"):
                content_type = "application/javascript"
            elif rel_path.endswith(".html"):
                content_type = "text/html"
            self._send_file(static_file, content_type)
        elif path == "/api/programs":
            self.handle_get_programs()
        elif path == "/api/baseline_summary":
            self.handle_get_baseline_summary()
        elif path == "/api/dataset":
            self.handle_get_dataset()
        elif path == "/api/ordering":
            self.handle_get_ordering()
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        if self.path == "/api/optimize":
            content_len = int(self.headers.get("Content-Length", 0))
            post_bytes = self.rfile.read(content_len)
            try:
                body = json.loads(post_bytes.decode("utf-8"))
            except Exception:
                body = {}
            self.handle_post_optimize(body)
        else:
            self.send_error(404, "Endpoint not found")

    def handle_get_programs(self):
        prog_dir = os.path.join(PROJECT_ROOT, "tests", "programs")
        progs = []
        if os.path.exists(os.path.join(PROJECT_ROOT, "tests", "sample.c")):
            progs.append({"name": "sample.c", "path": "tests/sample.c", "category": "Baseline Loop"})

        c_files = sorted(glob.glob(os.path.join(prog_dir, "*.c")))
        for f in c_files:
            rel = os.path.relpath(f, PROJECT_ROOT).replace("\\", "/")
            base = os.path.basename(f)
            progs.append({"name": base, "path": rel, "category": "Benchmark Suite"})

        self._send_json(progs)

    def handle_post_optimize(self, body: Dict[str, Any]):
        input_path = body.get("input_path", "tests/sample.c")
        custom_code = body.get("custom_code")

        work_dir = tempfile.mkdtemp(prefix="web_opt_")

        if input_path == "custom" and custom_code:
            input_path = os.path.join(work_dir, "custom_prog.c")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(custom_code)

        full_input = os.path.join(PROJECT_ROOT, input_path) if not os.path.isabs(input_path) else input_path
        if not os.path.exists(full_input):
            self._send_json({"error": f"Input file not found: {input_path}"}, 400)
            return

        prog_name = os.path.splitext(os.path.basename(full_input))[0]

        compiler = LLVMCompiler()
        pass_runner = PassRunner()
        extractor = IRFeatureExtractor()
        benchmark = BenchmarkEngine(runs=3, warmup_runs=1)
        verifier = CorrectnessVerifier()
        ml_model = PassSelectorModel()

        model_path = os.path.join(PROJECT_ROOT, "models", "trained_selector.json")
        if os.path.exists(model_path):
            ml_model.load(model_path)

        unopt_ir = os.path.join(work_dir, f"{prog_name}_unopt.ll")
        ok, msg = compiler.c_to_ir(full_input, unopt_ir)
        if not ok:
            self._send_json({"error": f"Clang failed to generate IR: {msg}"}, 500)
            return

        features = extractor.extract_features(unopt_ir)
        prediction = ml_model.predict(features)

        # Evaluate O0, O2, O3 vs ML
        results = []
        ref_bin = os.path.join(work_dir, f"{prog_name}_O0.out")
        ok, _ = compiler.ir_to_executable(unopt_ir, ref_bin)
        o0_perf = benchmark.measure_execution_time(ref_bin)
        o0_size = benchmark.measure_binary_size(ref_bin)
        o0_ir_metrics = benchmark.measure_ir_metrics(unopt_ir)

        base_time = o0_perf["median_ms"] or 1.0
        results.append({
            "strategy": "O0 (Unoptimized)",
            "execution_time_ms": o0_perf["median_ms"],
            "speedup_vs_o0": 1.0,
            "binary_size_bytes": o0_size,
            "ir_lines": o0_ir_metrics["ir_lines"],
            "correctness": "PASS"
        })

        # O2
        o2_ir = os.path.join(work_dir, f"{prog_name}_O2.ll")
        o2_bin = os.path.join(work_dir, f"{prog_name}_O2.out")
        pass_runner.run_standard_pipeline(unopt_ir, o2_ir, "O2")
        compiler.ir_to_executable(o2_ir, o2_bin)
        o2_perf = benchmark.measure_execution_time(o2_bin)
        o2_size = benchmark.measure_binary_size(o2_bin)
        o2_ir_metrics = benchmark.measure_ir_metrics(o2_ir)
        is_ok, _ = verifier.verify(ref_bin, o2_bin)
        results.append({
            "strategy": "-O2 (Default)",
            "execution_time_ms": o2_perf["median_ms"],
            "speedup_vs_o0": round(base_time / (o2_perf["median_ms"] or 1.0), 2),
            "binary_size_bytes": o2_size,
            "ir_lines": o2_ir_metrics["ir_lines"],
            "correctness": "PASS" if is_ok else "FAIL"
        })

        # O3
        o3_ir = os.path.join(work_dir, f"{prog_name}_O3.ll")
        o3_bin = os.path.join(work_dir, f"{prog_name}_O3.out")
        pass_runner.run_standard_pipeline(unopt_ir, o3_ir, "O3")
        compiler.ir_to_executable(o3_ir, o3_bin)
        o3_perf = benchmark.measure_execution_time(o3_bin)
        o3_size = benchmark.measure_binary_size(o3_bin)
        o3_ir_metrics = benchmark.measure_ir_metrics(o3_ir)
        is_ok, _ = verifier.verify(ref_bin, o3_bin)
        results.append({
            "strategy": "-O3 (Default)",
            "execution_time_ms": o3_perf["median_ms"],
            "speedup_vs_o0": round(base_time / (o3_perf["median_ms"] or 1.0), 2),
            "binary_size_bytes": o3_size,
            "ir_lines": o3_ir_metrics["ir_lines"],
            "correctness": "PASS" if is_ok else "FAIL"
        })

        # ML Selected
        ml_passes = prediction["passes"]
        ml_ir = os.path.join(work_dir, f"{prog_name}_ml.ll")
        ml_bin = os.path.join(work_dir, f"{prog_name}_ml.out")
        pass_runner.run_passes(unopt_ir, ml_ir, ml_passes)
        compiler.ir_to_executable(ml_ir, ml_bin)
        ml_perf = benchmark.measure_execution_time(ml_bin)
        ml_size = benchmark.measure_binary_size(ml_bin)
        ml_ir_metrics = benchmark.measure_ir_metrics(ml_ir)
        is_ok, _ = verifier.verify(ref_bin, ml_bin)
        results.append({
            "strategy": f"ML-Selected ({prediction['strategy']})",
            "execution_time_ms": ml_perf["median_ms"],
            "speedup_vs_o0": round(base_time / (ml_perf["median_ms"] or 1.0), 2),
            "binary_size_bytes": ml_size,
            "ir_lines": ml_ir_metrics["ir_lines"],
            "correctness": "PASS" if is_ok else "FAIL"
        })

        # Read IR snippets for diff viewer
        unopt_text = ""
        ml_text = ""
        if os.path.exists(unopt_ir):
            with open(unopt_ir, "r", encoding="utf-8", errors="replace") as f:
                unopt_text = "".join(f.readlines()[:100])
        if os.path.exists(ml_ir):
            with open(ml_ir, "r", encoding="utf-8", errors="replace") as f:
                ml_text = "".join(f.readlines()[:100])

        self._send_json({
            "program": prog_name,
            "features": features,
            "prediction": prediction,
            "results": results,
            "ir_text": {
                "unopt": unopt_text,
                "ml": ml_text
            }
        })

    def handle_get_baseline_summary(self):
        summary_csv = os.path.join(PROJECT_ROOT, "results", "comparison_summary.csv")
        summary_data = []
        if os.path.exists(summary_csv):
            import csv
            with open(summary_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    summary_data.append({
                        "program": row.get("program"),
                        "o0_time_ms": float(row.get("o0_time_ms", 0.0)),
                        "o2_time_ms": float(row.get("o2_time_ms", 0.0)),
                        "o3_time_ms": float(row.get("o3_time_ms", 0.0)),
                        "ml_time_ms": float(row.get("ml_time_ms", 0.0)),
                        "ml_strategy": row.get("ml_strategy"),
                        "speedup_vs_o2": float(row.get("speedup_vs_o2", 1.0)),
                        "speedup_vs_o3": float(row.get("speedup_vs_o3", 1.0))
                    })
        self._send_json({"summary": summary_data})

    def handle_get_dataset(self):
        model_path = os.path.join(PROJECT_ROOT, "models", "trained_selector.json")
        model_info = {}
        if os.path.exists(model_path):
            with open(model_path, "r", encoding="utf-8") as f:
                model_info = json.load(f)

        self._send_json({
            "total_samples": 75,
            "cv_accuracy": model_info.get("cv_accuracy", 0.20),
            "feature_importances": model_info.get("feature_importances", {}),
            "feature_names": model_info.get("feature_names", [])
        })

    def handle_get_ordering(self):
        sample_ir = os.path.join(PROJECT_ROOT, "tests", "sample.ll")
        work_dir = tempfile.mkdtemp(prefix="web_ord_")
        explorer = PassOrderingExplorer()
        perms = explorer.evaluate_order_sensitivity(sample_ir, work_dir, passes_to_permute=["instcombine", "sccp", "simplifycfg"])
        formatted = []
        for p in perms[:6]:
            formatted.append({
                "sequence": p.get("passes", []),
                "ir_instructions": p.get("ir_instructions", 0),
                "ir_lines": p.get("ir_lines", 0)
            })
        self._send_json({"permutations": formatted})



def run_server(port: int = 8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, WebDashboardHandler)
    print(f"\n=========================================================================")
    print(f"  ML-Guided LLVM Pass Selector Dashboard Server")
    print(f"  Listening on http://localhost:{port}")
    print(f"=========================================================================\n")

    import webbrowser
    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
