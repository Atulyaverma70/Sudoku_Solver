import cv2
import pytesseract
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]      # Top-left
    rect[2] = pts[np.argmax(s)]      # Bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]   # Top-right
    rect[3] = pts[np.argmax(diff)]   # Bottom-left
    return rect

def extract_sudoku_grid(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("Could not read image.")
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)

    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    if len(approx) != 4:
        print("Couldn't find a proper Sudoku grid.")
        return None

    pts = np.array([point[0] for point in approx], dtype="float32")
    pts = order_points(pts)

    side = max(
        np.linalg.norm(pts[0] - pts[1]),
        np.linalg.norm(pts[1] - pts[2]),
        np.linalg.norm(pts[2] - pts[3]),
        np.linalg.norm(pts[3] - pts[0])
    )
    dst = np.array([[0, 0], [side - 1, 0], [side - 1, side - 1], [0, side - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(pts, dst)
    warp = cv2.warpPerspective(gray, M, (int(side), int(side)))

    cell_size = int(side // 9)
    grid = []

    for i in range(9):
        row = []
        for j in range(9):
            x, y = j * cell_size, i * cell_size
            cell = warp[y:y + cell_size, x:x + cell_size]

            cell = cv2.resize(cell, (28, 28))
            _, cell = cv2.threshold(cell, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            digit = pytesseract.image_to_string(cell, config='--psm 10 -c tessedit_char_whitelist=0123456789').strip()

            row.append(int(digit) if digit.isdigit() else 0)
        grid.append(row)

    return grid
