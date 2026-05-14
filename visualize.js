/* visualize.js — Page 4: chart gallery */

(() => {
  const TYPE_ICONS = {
    histogram: "📊", bar: "📉", scatter: "⚡", line: "📈",
    pie: "🥧", heatmap: "🔥", boxplot: "📦",
  };

  const btn = document.getElementById("btn-generate");
  const empty = document.getElementById("empty-state");
  const section = document.getElementById("charts-section");
  const togglesEl = document.getElementById("chart-toggles");
  const gridEl = document.getElementById("chart-grid");
  const countEl = document.getElementById("chart-count");

  if (!btn) return;
  btn.addEventListener("click", run);

  let charts = [];
  const visible = new Set();

  async function run() {
    App.clearError();
    btn.disabled = true;
    App.showLoader("Rendering charts with seaborn / matplotlib…");
    try {
      const data = await App.postJSON("/visualize");
      charts = data.charts || [];
      visible.clear();
      charts.forEach(c => visible.add(c.id));
      render();
    } catch (err) {
      App.showError(err.message || "Visualization failed. Upload a dataset first.");
    } finally {
      App.hideLoader();
      btn.disabled = false;
    }
  }

  function render() {
    empty.hidden = true;
    section.hidden = false;
    countEl.textContent = charts.length;

    togglesEl.innerHTML = charts.map(c => `
      <button class="chart-toggle ${visible.has(c.id) ? "active" : ""}" data-id="${c.id}">
        <span>${TYPE_ICONS[c.type] || "📊"}</span>
        ${cap(c.type)}
        <span class="muted">— ${truncate(c.title, 26)}</span>
      </button>`).join("");

    togglesEl.onclick = (e) => {
      const tog = e.target.closest(".chart-toggle");
      if (!tog) return;
      const id = tog.dataset.id;
      if (visible.has(id)) visible.delete(id);
      else visible.add(id);
      render();
    };

    const visibleCharts = charts.filter(c => visible.has(c.id));
    if (!visibleCharts.length) {
      gridEl.innerHTML = `<div class="card empty">No charts selected. Use the toggles above.</div>`;
      return;
    }

    gridEl.innerHTML = visibleCharts.map(c => `
      <div class="card chart-card">
        <div class="chart-head">
          <div>
            <h3 class="chart-title">${escapeHtml(c.title)}</h3>
            <p class="chart-desc">${escapeHtml(c.description)}</p>
          </div>
          <a class="btn btn-secondary" download="${c.id}.png" href="${c.image}" style="font-size:11px;padding:6px 12px;">⬇ PNG</a>
        </div>
        <img src="${c.image}" alt="${escapeHtml(c.title)}" class="chart-img" />
      </div>`).join("");
  }

  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function truncate(s, n) { return s && s.length > n ? s.slice(0, n - 1) + "…" : s; }
  function escapeHtml(s) {
    return String(s || "").replace(/[<>&"]/g, ch => ({ "<":"&lt;", ">":"&gt;", "&":"&amp;", "\"":"&quot;" }[ch]));
  }
})();
