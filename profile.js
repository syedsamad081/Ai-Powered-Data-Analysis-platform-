/* profile.js — Page 2: data profiling */

(() => {
  const btn = document.getElementById("btn-analyze");
  const empty = document.getElementById("empty-state");
  const result = document.getElementById("profile-result");

  if (!btn) return;
  btn.addEventListener("click", run);

  async function run() {
    App.clearError();
    btn.disabled = true;
    App.showLoader("Profiling dataset…");
    try {
      const data = await App.postJSON("/analyze");
      render(data);
    } catch (err) {
      App.showError(err.message || "Analysis failed. Upload a dataset first.");
    } finally {
      App.hideLoader();
      btn.disabled = false;
    }
  }

  function render(d) {
    empty.hidden = true;
    result.hidden = false;

    const totalMissing = Object.values(d.missing_values || {}).reduce((s, v) => s + v.count, 0);
    const missingCols = Object.values(d.missing_values || {}).filter(v => v.count > 0).length;

    document.getElementById("p-rows").textContent      = App.formatNumber(d.rows);
    document.getElementById("p-cols").textContent      = d.cols;
    document.getElementById("p-missing").textContent   = App.formatNumber(totalMissing);
    document.getElementById("p-missing-sub").textContent = `across ${missingCols} columns`;
    document.getElementById("p-dups").textContent      = App.formatNumber(d.duplicate_rows);
    document.getElementById("p-num").textContent       = (d.numeric_columns || []).length;

    fillBadges("info-numeric",     d.numeric_columns,     "cyan");
    fillBadges("info-categorical", d.categorical_columns, "amber");
    fillBadges("info-datetime",    d.datetime_columns,    "emerald");

    renderMissing(d.missing_values || {});
    renderDescribe(d.describe || {});
  }

  function fillBadges(id, items = [], color = "violet") {
    const el = document.getElementById(id);
    if (!items.length) {
      el.innerHTML = `<p class="muted small">None detected</p>`;
      return;
    }
    el.innerHTML = items.map(c => `<span class="badge ${color}">${escapeHtml(c)}</span>`).join("");
  }

  function renderMissing(missing) {
    const section = document.getElementById("missing-section");
    const container = document.getElementById("missing-bars");
    const entries = Object.entries(missing);
    if (!entries.length) { section.hidden = true; return; }
    section.hidden = false;

    container.innerHTML = entries.map(([col, info]) => {
      const cls = info.pct > 50 ? "red" : info.pct > 20 ? "amber" : "violet";
      return `
        <div class="missing-row">
          <span class="missing-name">${escapeHtml(col)}</span>
          <div class="bar"><div class="bar-fill ${cls}" style="width:${info.pct}%"></div></div>
          <span class="missing-pct">${info.pct}%</span>
          <span class="missing-cnt">${App.formatNumber(info.count)} cells</span>
        </div>`;
    }).join("");
  }

  function renderDescribe(describe) {
    const section = document.getElementById("describe-section");
    const table = document.getElementById("describe-table");
    const cols = Object.keys(describe);
    if (!cols.length) { section.hidden = true; return; }
    section.hidden = false;

    const stats = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"];
    const head = `<thead><tr><th>Statistic</th>${cols.map(c => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead>`;
    const body = stats.map(stat => `
      <tr>
        <td style="color:#C4B5FD;font-weight:600;">${stat}</td>
        ${cols.map(c => {
          const v = describe[c]?.[stat];
          if (v === null || v === undefined) return `<td>—</td>`;
          return `<td>${Number(v).toLocaleString(undefined, { maximumFractionDigits: 4 })}</td>`;
        }).join("")}
      </tr>`).join("");
    table.innerHTML = head + `<tbody>${body}</tbody>`;
  }

  function escapeHtml(s) {
    return String(s).replace(/[<>&]/g, ch => ({ "<":"&lt;", ">":"&gt;", "&":"&amp;" }[ch]));
  }
})();
