/* report.js — Page 5: AI-generated report */

(() => {
  const btn = document.getElementById("btn-generate");
  const empty = document.getElementById("empty-state");
  const section = document.getElementById("report-section");
  const meta = document.getElementById("meta-strip");
  const content = document.getElementById("report-content");
  const exportBtn = document.getElementById("btn-export-md");
  const printBtn = document.getElementById("btn-print-pdf");

  if (!btn) return;
  let reportMd = "";

  btn.addEventListener("click", run);
  exportBtn.addEventListener("click", exportMarkdown);
  printBtn.addEventListener("click", () => window.print());

  async function run() {
    App.clearError();
    btn.disabled = true;
    App.showLoader("Gemini is generating your AI report…");
    try {
      const data = await App.postJSON("/generate-report");
      reportMd = data.report || "";
      render(data);
    } catch (err) {
      App.showError(err.message || "Report generation failed. Upload a dataset first.");
    } finally {
      App.hideLoader();
      btn.disabled = false;
    }
  }

  function render(data) {
    empty.hidden = true;
    section.hidden = false;

    const m = data.profile_summary || {};
    meta.innerHTML = [
      ["Rows",       App.formatNumber(m.rows),                    "🔢", "violet"],
      ["Columns",    m.cols,                                       "📋", "cyan"],
      ["Numeric",    (m.numeric_columns || []).length,             "📊", "emerald"],
      ["Duplicates", App.formatNumber(m.duplicate_rows),           "🔁", "amber"],
    ].map(([label, value, icon, color]) => `
      <div class="card stat">
        <div class="stat-icon ${color}">${icon}</div>
        <div>
          <p class="stat-label">${label}</p>
          <p class="stat-value">${value ?? "—"}</p>
        </div>
      </div>`).join("");

    content.innerHTML = App.markdownToHTML(reportMd);
  }

  function exportMarkdown() {
    if (!reportMd) return;
    const blob = new Blob([reportMd], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ai_report.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
})();
