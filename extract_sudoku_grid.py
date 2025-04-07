import cv2
import pytesseract
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_sudoku_grid(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        return None

    # Preprocessing: Noise reduction & thresholding
    img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Find contours to detect grid
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) < 81:
        return None  # Ensure at least 81 cells are detected

    # OCR with digit extraction
    sudoku_text = pytesseract.image_to_string(img, config='--psm 6 outputbase digits')

    # Convert OCR output into a 9x9 grid
    lines = [line.strip() for line in sudoku_text.split("\n") if line.strip()]
    grid = []

    for line in lines:
        row = [int(char) if char.isdigit() else 0 for char in line]
        
        # Ensure row has exactly 9 elements
        while len(row) < 9:
            row.append(0)
        while len(row) > 9:
            row = row[:9]
        
        grid.append(row)

    # Ensure grid has exactly 9 rows
    while len(grid) < 9:
        grid.append([0] * 9)
    grid = grid[:9]

    return grid if len(grid) == 9 else None
