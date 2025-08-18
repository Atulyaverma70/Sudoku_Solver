from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import sys

from sudoku_solver import solve_sudoku   # your solver
from ocr_processing import extract_sudoku_grid  # your OCR

# Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# --- Logging for debug ---
@app.before_request
def log_request_info():
    print(f"--> Incoming {request.method} {request.path}", file=sys.stderr)


# --- Error handlers to always return JSON ---
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "internal server error"}), 500


# Health check
@app.get("/health")
def health():
    return {"status": "ok"}


# Serve frontend (index.html)
@app.get("/")
def home():
    return render_template("index.html")


# Solve Sudoku API
@app.post("/solve")
def solve():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid or missing JSON body"}), 400

    grid = data.get("grid")
    if not grid or len(grid) != 9 or any(len(r) != 9 for r in grid):
        return jsonify({"error": "grid must be 9x9 integers"}), 400

    work = [row[:] for row in grid]
    if solve_sudoku(work):
        return jsonify({"solution": work})
    return jsonify({"error": "unsolvable"}), 422


@app.post("/ocr")
def ocr():
    if "image" not in request.files:
        return jsonify({"error": "image file missing"}), 400

    f = request.files["image"]
    tmp_path = "/tmp/upload.jpg"
    f.save(tmp_path)

    try:
        grid = extract_sudoku_grid(tmp_path)
        if not grid:
            return jsonify({"error": "could not extract grid"}), 422
        return jsonify({"grid": grid})
    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)  # log to Render logs
        return jsonify({"error": f"OCR crashed: {str(e)}"}), 500



# Entry point for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT
    app.run(host="0.0.0.0", port=port)
