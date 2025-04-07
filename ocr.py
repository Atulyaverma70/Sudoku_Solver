import cv2
import pytesseract
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_sudoku_grid(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None

    # Apply preprocessing
    img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Find contours to detect the outermost Sudoku grid
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)

    # Approximate grid shape and extract ROI (Region of Interest)
    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    if len(approx) != 4:
        return None  # Grid should have 4 corner points

    # Apply perspective transform to get a top-down view
    pts = np.array([point[0] for point in approx], dtype="float32")
    side = max(np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[1] - pts[2]))
    dst = np.array([[0, 0], [side-1, 0], [side-1, side-1], [0, side-1]], dtype="float32")
    matrix = cv2.getPerspectiveTransform(pts, dst)
    warped = cv2.warpPerspective(img, matrix, (int(side), int(side)))

    # Split the warped image into 9x9 grid cells
    cell_size = int(side) // 9
    grid = []

    for i in range(9):
        row = []
        for j in range(9):
            x, y = j * cell_size, i * cell_size
            cell = warped[y:y+cell_size, x:x+cell_size]

            # Apply OCR to extract numbers (using --psm 10 for single character)
            digit = pytesseract.image_to_string(cell, config='--psm 10 outputbase digits').strip()
            row.append(int(digit) if digit.isdigit() else 0)

        grid.append(row)

    return grid
