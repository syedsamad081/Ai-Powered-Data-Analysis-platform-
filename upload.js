/* upload.js — Page 1: dataset upload */

(() => {
  const dropzone = document.getElementById("upload-dropzone");
  const fileInput = document.getElementById("file-input");
  const resultBox = document.getElementById("upload-result");
  const previewContainer = document.getElementById("preview-container");

  if (!dropzone) return;

  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => handleFile(e.target.files[0]));

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragging");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragging"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragging");
    handleFile(e.dataTransfer.files[0]);
  });

  async function handleFile(file) {
    if (!file) return;
    App.clearError();
    resultBox.hidden = true;
    App.showLoader("Uploading & parsing dataset…");

    try {
      const formData = new FormData();
      formData.append("file", file);
      const data = await App.postForm("/upload", formData);
      renderResult(data);
    } catch (err) {
      App.showError(err.message || "Upload failed.");
    } finally {
      App.hideLoader();
    }
  }

  function renderResult(data) {
    document.getElementById("stat-file").textContent     = data.filename;
    document.getElementById("stat-rows").textContent     = App.formatNumber(data.rows);
    document.getElementById("stat-cols").textContent     = data.cols;
    document.getElementById("stat-features").textContent = (data.columns || []).length || "—";

    App.renderTable(previewContainer, {
      rows: data.preview,
      columns: data.columns,
      dtypes: data.dtypes,
    });

    resultBox.hidden = false;
  }
})();
