from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from sudoku_solver import solve_sudoku  # uses your existing solver
# choose ONE OCR module; ensure it DOES NOT hardcode a Windows path
from ocr_processing import extract_sudoku_grid  # rename your good module to ocr_processing.py

app = Flask(__name__)
CORS(app)  # allow your Render frontend to call this API

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/solve")
def solve():
    data = request.get_json(force=True)
    grid = data.get("grid")
    if not grid or len(grid) != 9 or any(len(r) != 9 for r in grid):
        return jsonify({"error": "grid must be 9x9 integers"}), 400
    # copy grid to avoid in-place mutation if you want
    work = [row[:] for row in grid]
    if solve_sudoku(work):
        return jsonify({"solution": work})
    return jsonify({"error": "unsolvable"}), 422

@app.post("/ocr")
def ocr():
    # accepts multipart/form-data with file field 'image'
    if "image" not in request.files:
        return jsonify({"error": "image file missing"}), 400
    f = request.files["image"]
    tmp_path = "/tmp/upload.jpg"
    f.save(tmp_path)
    grid = extract_sudoku_grid(tmp_path)
    if not grid:
        return jsonify({"error": "could not extract grid"}), 422
    return jsonify({"grid": grid})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # on Render, $PORT will be injected
    app.run(host="0.0.0.0", port=port)
