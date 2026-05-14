/* clean.js — Page 3: data cleaning */

(() => {
  const OPERATIONS = [
    { id: "drop_duplicates",      icon: "🔁", label: "Remove Duplicate Rows",          desc: "Drop all exact duplicate rows using pandas drop_duplicates()." },
    { id: "fill_missing_mean",    icon: "📊", label: "Fill Missing Values (Mean)",     desc: "Replace numeric nulls with the column mean." },
    { id: "fill_missing_median",  icon: "📐", label: "Fill Missing Values (Median)",   desc: "Replace numeric nulls with the column median. Robust to outliers." },
    { id: "fill_missing_mode",    icon: "🏆", label: "Fill Missing Values (Mode)",     desc: "Replace nulls with the most frequent value. Good for categoricals." },
    { id: "remove_outliers_iqr",  icon: "📍", label: "Remove Outliers (IQR Method)",   desc: "Drop rows outside Q1 − 1.5·IQR and Q3 + 1.5·IQR." },
    { id: "drop_high_null_cols",  icon: "🗑️", label: "Drop High-Null Columns",         desc: "Remove columns where more than 50% of values are missing." },
    { id: "normalize_numeric",    icon: "⚖️", label: "Normalize Numeric Columns",      desc: "Min-max scale all numeric columns to [0, 1] using NumPy." },
    { id: "convert_dtypes",       icon: "🔄", label: "Smart Type Conversion",          desc: "Auto-convert columns to the best possible dtype." },
  ];

  const list = document.getElementById("operations-list");
  const summary = document.getElementById("selected-summary");
  const countBadge = document.getElementById("selected-count");
  const applyBtn = document.getElementById("btn-apply");
  const resultBox = document.getElementById("clean-result");
  const previewSection = document.getElementById("preview-section");
  const previewContainer = document.getElementById("preview-container");

  if (!list) return;
  const selected = new Set();

  // Render operation toggles
  list.innerHTML = OPERATIONS.map(op => `
    <div class="toggle-card" data-id="${op.id}">
      <div class="toggle-checkbox">
        <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
        </svg>
      </div>
      <div class="toggle-icon">${op.icon}</div>
      <div>
        <p class="toggle-label">${op.label}</p>
        <p class="toggle-desc">${op.desc}</p>
      </div>
    </div>`).join("");

  list.addEventListener("click", (e) => {
    const card = e.target.closest(".toggle-card");
    if (!card) return;
    const id = card.dataset.id;
    if (selected.has(id)) selected.delete(id);
    else selected.add(id);
    card.classList.toggle("selected", selected.has(id));
    updateSummary();
  });

  applyBtn.addEventListener("click", apply);

  function updateSummary() {
    countBadge.textContent = `${selected.size} selected`;
    applyBtn.disabled = selected.size === 0;
    if (!selected.size) {
      summary.innerHTML = `<p class="muted">No operations selected.</p>`;
      return;
    }
    summary.innerHTML = [...selected].map(id => {
      const op = OPERATIONS.find(o => o.id === id);
      return `<div class="item">${op.icon} ${op.label}</div>`;
    }).join("");
  }

  async function apply() {
    App.clearError();
    App.showLoader("Applying cleaning operations…");
    try {
      const data = await App.postJSON("/clean", { operations: [...selected] });
      renderResult(data);
    } catch (err) {
      App.showError(err.message || "Cleaning failed. Upload a dataset first.");
    } finally {
      App.hideLoader();
    }
  }

  function renderResult(d) {
    document.getElementById("r-rows").textContent  = d.rows_removed;
    document.getElementById("r-cols").textContent  = (d.columns_removed || []).length;
    document.getElementById("r-shape").textContent = `${d.cleaned_shape.rows} × ${d.cleaned_shape.cols}`;
    resultBox.hidden = false;

    if (d.preview && d.preview.length) {
      previewSection.hidden = false;
      const cols = d.columns && d.columns.length ? d.columns : Object.keys(d.preview[0] || {});
      App.renderTable(previewContainer, { rows: d.preview, columns: cols });
    }
  }
})();
