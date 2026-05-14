"""
app.py  —  Main entry point for the AI Data Platform.

HOW TO RUN:
    python app.py
    Then open http://localhost:5000 in your browser.

HOW IT WORKS:
    This file creates the Flask web server and wires everything together.
    - Templates (HTML pages) are served from the templates/ folder.
    - CSS and JavaScript are served from the static/ folder.
    - All data processing happens in the routes/ and services/ folders.
"""

import os
from flask import Flask, render_template
from dotenv import load_dotenv

# Read the .env file so we can use GEMINI_API_KEY and FLASK_PORT
# throughout the whole application
load_dotenv()

# Import each feature as a Flask "blueprint"
# A blueprint is just a group of related routes bundled together
from routes.upload    import upload_bp      # handles file upload
from routes.analyze   import analyze_bp     # handles data profiling
from routes.clean     import clean_bp       # handles data cleaning
from routes.visualize import visualize_bp   # handles chart generation
from routes.report    import report_bp      # handles AI report generation


def create_app():
    """
    Build and configure the Flask app.
    Called once at startup.
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Create the uploads folder if it doesn't already exist.
    # This is where user-uploaded files (CSV, Excel, PDF, etc.) are saved.
    os.makedirs("uploads", exist_ok=True)

    # Register all feature blueprints with the app
    app.register_blueprint(upload_bp)
    app.register_blueprint(analyze_bp)
    app.register_blueprint(clean_bp)
    app.register_blueprint(visualize_bp)
    app.register_blueprint(report_bp)

    # ── Page routes ───────────────────────────────────────────
    # Each route renders an HTML page. The active= parameter tells
    # the sidebar which menu item to highlight.

    @app.route("/")
    def upload_page():
        """Step 1 — Upload a dataset."""
        return render_template("upload.html", active="upload")

    @app.route("/profile")
    def profile_page():
        """Step 2 — View dataset statistics and column types."""
        return render_template("profile.html", active="profile")

    @app.route("/clean")
    def clean_page():
        """Step 3 — Choose and apply data cleaning operations."""
        return render_template("clean.html", active="clean")

    @app.route("/visualize")
    def visualize_page():
        """Step 4 — Auto-generate charts for the dataset."""
        return render_template("visualize.html", active="visualize")

    @app.route("/report")
    def report_page():
        """Step 5 — Generate an AI-written analysis report."""
        return render_template("report.html", active="report")

    @app.route("/health")
    def health():
        """Quick check to confirm the server is running (used in run.bat)."""
        return {"status": "ok", "message": "AI Data Platform is running"}

    return app


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app = create_app()

    print(f"\n  AI Data Platform is running!")
    print(f"  Open your browser at: http://localhost:{port}\n")

    app.run(debug=True, port=port)
