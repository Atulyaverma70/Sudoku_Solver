from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, sys, shutil

from sudoku_solver import solve_sudoku
from ocr_processing import extract_sudoku_grid

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

@app.before_request
def _log():
    print(f"--> {request.method} {request.path}", file=sys.stderr)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def home():
    return send_from_directory("templates", "index.html")

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
        return jsonify({"error": str(e)}), 500
