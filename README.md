# AI_Powered  Data Analysis Platform — Final Year Project

A web application that lets you upload a dataset (CSV, Excel, Word, or PDF),
automatically clean it, generate charts, and produce an AI-powered analysis
report using Google Gemini.

---

## What the app does

| Step | Page | What happens |
|------|------|--------------|
| 1 | **Upload** | Upload CSV / XLSX / DOCX / PDF — the app reads the file and shows a preview |
| 2 | **Data Profile** | One click gives you row count, missing values, data types, and statistics |
| 3 | **Data Cleaning** | Pick cleaning operations (remove duplicates, fill nulls, remove outliers, etc.) |
| 4 | **Visualize** | Auto-generated charts: histograms, bar, scatter, pie, heatmap, boxplot |
| 5 | **AI Report** | Gemini AI writes a full analysis report you can export as Markdown or PDF |

---

## Tech Stack

| Part | Technology |
|------|-----------|
| Web framework | Python Flask |
| Data processing | Pandas, NumPy |
| Charts | Matplotlib, Seaborn (rendered server-side as images) |
| File reading | OpenPyXL (Excel), pdfplumber (PDF), python-docx (Word) |
| AI reports | Google Gemini API |
| Frontend | Plain HTML + CSS + JavaScript (no frameworks) |

---

## Folder Structure

```
project/
├── app.py                  <- Main entry point — run this to start the app
├── requirements.txt        <- All Python packages needed
├── .env.example            <- Copy to .env and add your Gemini key
│
├── routes/                 <- API endpoints (one file per feature)
│   ├── upload.py           <- POST /upload
│   ├── analyze.py          <- POST /analyze
│   ├── clean.py            <- POST /clean
│   ├── visualize.py        <- POST /visualize
│   └── report.py           <- POST /generate-report
│
├── services/               <- Core logic (no web code here)
│   ├── file_handler.py     <- Reads CSV, Excel, Word, PDF into a table
│   ├── data_processor.py   <- Profiling and cleaning operations
│   ├── graph_recommender.py<- Picks and renders the right charts
│   └── ai_report.py        <- Calls Gemini to write the report
│
├── templates/              <- HTML pages (one per step)
│   ├── base.html           <- Shared sidebar + layout
│   ├── upload.html
│   ├── profile.html
│   ├── clean.html
│   ├── visualize.html
│   └── report.html
│
├── static/
│   ├── css/styles.css      <- All styling
│   └── js/                 <- One JS file per page
│       ├── common.js       <- Shared helpers (loader, table renderer, fetch)
│       ├── upload.js
│       ├── profile.js
│       ├── clean.js
│       ├── visualize.js
│       └── report.js
│
├── uploads/                <- Uploaded files are saved here temporarily
└── test_data.csv           <- Sample dataset to try the app with
```

---

## Setup (step by step)

### Requirements
- Python 3.10 or newer
- A free Gemini API key from https://aistudio.google.com/apikey

---

### Step 1 — Install Python packages

Open a terminal inside the project folder and run:

```bash
pip install -r requirements.txt
```

This installs Flask, Pandas, Matplotlib, Seaborn, and everything else the app needs.

---

### Step 2 — Add your Gemini API key

1. Copy the example env file:
   ```
   Windows:   copy .env.example .env
   Mac/Linux: cp .env.example .env
   ```

2. Open `.env` in any text editor and replace `your_gemini_api_key_here`
   with your real key from https://aistudio.google.com/apikey

The `.env` file looks like this:
```
GEMINI_API_KEY=AIzaSy...your_key_here...
FLASK_ENV=development
FLASK_PORT=5000
```

---

### Step 3 — Run the app

**Option A — Double-click (Windows only):**
Double-click `run.bat` in the project folder.

**Option B — Terminal:**
```bash
python app.py
```

---

### Step 4 — Open in browser

Go to: **http://localhost:5000**

Upload `test_data.csv` (included) to try everything out.

---

## Common Problems

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Port 5000 already in use | Change `FLASK_PORT=5001` in `.env` |
| AI Report says "quota exhausted" | Free tier has daily limits — try again tomorrow, or use a paid key |
| Charts not showing | Run `pip install matplotlib seaborn` |
| PDF upload fails | Run `pip install pdfplumber` |

---

## Notes for teammates

- The `.env` file contains your personal API key — **do not share it**.
  Each team member should create their own `.env` from `.env.example`.
- Uploaded files are saved in the `uploads/` folder temporarily.
- The app stores the current dataset in memory — restarting the server
  clears it and you will need to upload your file again.
