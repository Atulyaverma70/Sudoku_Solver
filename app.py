from flask import Flask, request, jsonify
import subprocess
import numpy as np
import cv2
import pytesseract

app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_sudoku_grid(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    sudoku_text = pytesseract.image_to_string(img, config='--psm 6 digits')
    grid = [[int(ch) if ch.isdigit() else 0 for ch in line] for line in sudoku_text.split("\n") if line]

    while len(grid) < 9:
        grid.append([0] * 9)
    grid = [row[:9] + [0] * (9 - len(row)) for row in grid]

    return grid if len(grid) == 9 else None

@app.route("/solve", methods=["POST"])
def solve():
    try:
        data = request.get_json()
        grid = data.get("grid")

        if not grid or len(grid) != 9 or any(len(row) != 9 for row in grid):
            return jsonify({"error": "Invalid grid format"}), 400

        input_str = "\n".join(" ".join(map(str, row)) for row in grid)
        result = subprocess.run(["./sudoku_solver"], input=input_str, text=True, capture_output=True, check=True)

        solved_grid = [list(map(int, line.split())) for line in result.stdout.strip().split("\n")]
        
        if all(-1 in row for row in solved_grid):
            return jsonify({"error": "No solution found"}), 400

        return jsonify({"solved_grid": solved_grid})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Solver execution failed", "details": e.stderr}), 500

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = "uploaded_sudoku.jpg"
    file.save(file_path)

    grid = extract_sudoku_grid(file_path)
    if grid is None:
        return jsonify({"error": "Could not extract Sudoku grid"}), 400

    return jsonify({"grid": grid})

if __name__ == "__main__":
    app.run(debug=True)
