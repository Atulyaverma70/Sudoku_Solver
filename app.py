from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sudoku_solver import solve_sudoku
from ocr_processing import extract_sudoku_grid
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, resources={r"/*": {"origins": "*"}})  # Fix CORS
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def api_solve():
    try:
        data = request.get_json()
        if not data or 'grid' not in data:
            return jsonify({'error': 'Invalid request'}), 400

        grid = data['grid']
        if len(grid) != 9 or any(len(row) != 9 for row in grid):
            return jsonify({'error': 'Invalid grid format'}), 400

        grid_copy = [row.copy() for row in grid]
        if solve_sudoku(grid_copy):
            return jsonify({'solved_grid': grid_copy})
        return jsonify({'error': 'No solution'}), 400

    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty file'}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.jpg')
        file.save(file_path)

        grid = extract_sudoku_grid(file_path)
        if not grid or len(grid) != 9 or any(len(row)!=9 for row in grid):
            return jsonify({'error': 'OCR failed'}), 400

        return jsonify({'grid': grid})

    except Exception as e:
        return jsonify({'error': f'Upload error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 