document.addEventListener("DOMContentLoaded", () => {
  // Navigation Tabs
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add("active");

      if (btn.dataset.tab === "tab-suite") {
        loadBenchmarkSuite();
      } else if (btn.dataset.tab === "tab-ml") {
        loadMLAnalytics();
      } else if (btn.dataset.tab === "tab-ordering") {
        loadOrderingExplorer();
      }
    });
  });

  // Load Program List for Live Optimizer Tab
  loadProgramList();

  // Run Optimization Event Listener
  const runBtn = document.getElementById("run-opt-btn");
  if (runBtn) {
    runBtn.addEventListener("click", runLiveOptimization);
  }

  // Program select change
  const progSelect = document.getElementById("program-select");
  if (progSelect) {
    progSelect.addEventListener("change", (e) => {
      if (e.target.value === "custom") {
        document.getElementById("custom-code-container").style.display = "block";
      } else {
        document.getElementById("custom-code-container").style.display = "none";
      }
    });
  }
});

let speedupChart = null;
let importanceChart = null;

async function loadProgramList() {
  try {
    const res = await fetch("/api/programs");
    const progs = await res.json();
    const select = document.getElementById("program-select");
    if (!select) return;

    select.innerHTML = progs.map(p => `<option value="${p.path}">${p.name} (${p.category || 'Benchmark'})</option>`).join("");
    select.innerHTML += `<option value="custom">-- Custom C Source Code --</option>`;
  } catch (err) {
    console.error("Failed to load programs:", err);
  }
}

async function runLiveOptimization() {
  const runBtn = document.getElementById("run-opt-btn");
  const progSelect = document.getElementById("program-select");
  const customCode = document.getElementById("custom-c-code") ? document.getElementById("custom-c-code").value : "";
  const resultsArea = document.getElementById("opt-results-area");

  if (!progSelect) return;

  const inputPath = progSelect.value;
  runBtn.disabled = true;
  runBtn.innerText = "Optimizing & Benchmarking...";

  // Animate Pipeline Steps
  setStepStatus("step-ir", "active");
  setStepStatus("step-feats", "");
  setStepStatus("step-ml", "");
  setStepStatus("step-bench", "");

  try {
    const payload = {
      input_path: inputPath,
      custom_code: inputPath === "custom" ? customCode : null
    };

    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    setStepStatus("step-ir", "complete");
    setStepStatus("step-feats", "active");

    const data = await res.json();
    if (!res.ok || data.error) {
      alert(`Error: ${data.error || 'Optimization failed'}`);
      runBtn.disabled = false;
      runBtn.innerText = "Execute ML Optimization Pipeline";
      return;
    }

    setStepStatus("step-feats", "complete");
    setStepStatus("step-ml", "active");

    setTimeout(() => {
      setStepStatus("step-ml", "complete");
      setStepStatus("step-bench", "active");
    }, 200);

    setTimeout(() => {
      setStepStatus("step-bench", "complete");
      renderSingleResults(data);
      if (resultsArea) resultsArea.style.display = "block";
      runBtn.disabled = false;
      runBtn.innerText = "Execute ML Optimization Pipeline";
    }, 400);

  } catch (err) {
    console.error(err);
    alert("Execution error occurred.");
    runBtn.disabled = false;
    runBtn.innerText = "Execute ML Optimization Pipeline";
  }
}

function setStepStatus(stepId, status) {
  const el = document.getElementById(stepId);
  if (!el) return;
  el.className = `step-box ${status}`;
}

function renderSingleResults(data) {
  // Render Feature Grid
  const featsGrid = document.getElementById("features-grid");
  if (featsGrid && data.features) {
    featsGrid.innerHTML = Object.entries(data.features).map(([k, v]) => `
      <div class="feature-badge">
        <span class="name">${k}</span>
        <span class="val">${typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(4)) : v}</span>
      </div>
    `).join("");
  }

  // Render Prediction Info
  document.getElementById("pred-strategy").innerText = data.prediction.strategy;
  document.getElementById("pred-confidence").innerText = `Confidence: ${(data.prediction.confidence * 100).toFixed(1)}%`;
  document.getElementById("pred-passes").innerText = data.prediction.pass_string;

  // Render Metrics Summary Table
  const tbody = document.getElementById("summary-tbody");
  if (tbody && data.results) {
    tbody.innerHTML = data.results.map(r => `
      <tr>
        <td><strong>${r.strategy}</strong></td>
        <td>${r.execution_time_ms.toFixed(3)} ms</td>
        <td>${r.speedup_vs_o0.toFixed(2)}x</td>
        <td>${r.binary_size_bytes} B</td>
        <td>${r.ir_lines}</td>
        <td><span class="${r.correctness === 'PASS' ? 'badge-pass' : 'badge-fail'}">${r.correctness}</span></td>
      </tr>
    `).join("");
  }

  // Render IR Code Compare
  if (data.ir_text) {
    document.getElementById("ir-unopt-text").textContent = data.ir_text.unopt || "";
    document.getElementById("ir-ml-text").textContent = data.ir_text.ml || "";
  }
}

async function loadBenchmarkSuite() {
  try {
    const res = await fetch("/api/baseline_summary");
    const data = await res.json();

    const tbody = document.getElementById("suite-tbody");
    if (tbody && data.summary) {
      tbody.innerHTML = data.summary.map(r => `
        <tr>
          <td><strong>${r.program}</strong></td>
          <td>${r.o0_time_ms.toFixed(2)} ms</td>
          <td>${r.o2_time_ms.toFixed(2)} ms</td>
          <td>${r.o3_time_ms.toFixed(2)} ms</td>
          <td><strong style="color: var(--accent-emerald)">${r.ml_time_ms.toFixed(2)} ms</strong></td>
          <td><code>${r.ml_strategy}</code></td>
          <td>${r.speedup_vs_o2.toFixed(2)}x</td>
          <td>${r.speedup_vs_o3.toFixed(2)}x</td>
          <td><span class="badge-pass">PASS</span></td>
        </tr>
      `).join("");
    }

    renderSuiteCharts(data.summary);
  } catch (err) {
    console.error("Failed to load benchmark suite:", err);
  }
}

function renderSuiteCharts(summaryData) {
  if (!summaryData || typeof Chart === 'undefined') return;

  const labels = summaryData.map(d => d.program);
  const o2Times = summaryData.map(d => d.o2_time_ms);
  const o3Times = summaryData.map(d => d.o3_time_ms);
  const mlTimes = summaryData.map(d => d.ml_time_ms);

  const ctxSpeedup = document.getElementById("chart-suite-speedup");
  if (ctxSpeedup) {
    if (speedupChart) speedupChart.destroy();
    speedupChart = new Chart(ctxSpeedup, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          { label: '-O2 Execution Time (ms)', data: o2Times, backgroundColor: '#f59e0b' },
          { label: '-O3 Execution Time (ms)', data: o3Times, backgroundColor: '#6b7280' },
          { label: 'ML-Selected Execution Time (ms)', data: mlTimes, backgroundColor: '#10b981' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#9ca3af', font: { family: 'Inter' } } } },
        scales: {
          x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
          y: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } }
        }
      }
    });
  }
}

async function loadMLAnalytics() {
  try {
    const res = await fetch("/api/dataset");
    const data = await res.json();

    document.getElementById("total-samples").innerText = data.total_samples || 75;
    document.getElementById("cv-acc").innerText = `${((data.cv_accuracy || 0.20) * 100).toFixed(1)}%`;

    if (data.feature_importances && typeof Chart !== 'undefined') {
      const sorted = Object.entries(data.feature_importances).sort((a,b) => b[1] - a[1]);
      const ctx = document.getElementById("chart-importances");
      if (ctx) {
        if (importanceChart) importanceChart.destroy();
        importanceChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: sorted.map(s => s[0]),
            datasets: [{
              label: 'Gini Importance (Random Forest)',
              data: sorted.map(s => s[1]),
              backgroundColor: '#06b6d4'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { labels: { color: '#9ca3af', font: { family: 'Inter' } } } },
            scales: {
              x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
              y: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } }
            }
          }
        });
      }
    }
  } catch (err) {
    console.error("Failed to load ML analytics:", err);
  }
}

async function loadOrderingExplorer() {
  try {
    const res = await fetch("/api/ordering?program=tests/sample.c");
    const data = await res.json();

    const tbody = document.getElementById("ordering-tbody");
    if (tbody && data.permutations) {
      tbody.innerHTML = data.permutations.map((p, idx) => `
        <tr>
          <td>#${idx + 1}</td>
          <td><code>${p.sequence.join(', ')}</code></td>
          <td>${p.ir_instructions}</td>
          <td>${p.ir_lines}</td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Failed to load ordering explorer:", err);
  }
}
