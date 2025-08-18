from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os, sys, shutil

from sudoku_solver import solve_sudoku
from ocr_processing import extract_sudoku_grid

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

@app.before_request
def _log():
    print(f"--> {request.method} {request.path}", file=sys.stderr)

@app.errorhandler(404)
def _404(e):
    return jsonify({"error": "not found"}), 404

@app.errorhandler(500)
def _500(e):
    return jsonify({"error": "internal server error"}), 500

@app.get("/health")
def health():
    return {"status": "ok"}

# quick diag to confirm tesseract is present and where
@app.get("/diag")
def diag():
    return {
        "tesseract_in_path": shutil.which("tesseract") or "",
        "TESSERACT_CMD_env": os.environ.get("TESSERACT_CMD", ""),
    }

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/solve")
def solve():
    data = request.get_json(silent=True)
    if not data or "grid" not in data:
        return jsonify({"error": "invalid or missing JSON body"}), 400
    grid = data["grid"]
    if not isinstance(grid, list) or len(grid) != 9 or any(len(r) != 9 for r in grid):
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
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": f"OCR crashed: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
