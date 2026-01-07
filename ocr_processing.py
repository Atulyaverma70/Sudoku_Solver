import os
import cv2
import numpy as np
import pytesseract
from typing import List, Optional

# -------------------------------
# Tesseract configuration
# -------------------------------
pytesseract.pytesseract.tesseract_cmd = os.environ.get(
    "TESSERACT_CMD", "/usr/bin/tesseract"
)

# -------------------------------
# Utility functions
# -------------------------------
def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxW = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxH = int(max(heightA, heightB))

    dst = np.array([
        [0, 0],
        [maxW - 1, 0],
        [maxW - 1, maxH - 1],
        [0, maxH - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxW, maxH))


def _find_puzzle_contour(edged: np.ndarray) -> Optional[np.ndarray]:
    cnts, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None

    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        approx = approx.reshape(-1, 2)

        if approx.shape[0] >= 4:
            return approx[:4].astype("float32")

    return None


def _prepare_for_ocr(cell: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY) if cell.ndim == 3 else cell
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    bw = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )

    kernel = np.ones((2, 2), np.uint8)
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel)

    return bw


def _ocr_digit(img: np.ndarray) -> int:
    # Skip nearly empty cells
    if cv2.countNonZero(img) < 30:
        return 0

    config = "--oem 3 --psm 10 -c tessedit_char_whitelist=123456789"
    text = pytesseract.image_to_string(img, config=config).strip()

    for ch in text:
        if ch in "123456789":
            return int(ch)

    return 0


def _extract_cells(warped: np.ndarray, grid_size: int = 9) -> List[List[np.ndarray]]:
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY) if warped.ndim == 3 else warped
    h, w = gray.shape
    cell_h, cell_w = h // grid_size, w // grid_size

    cells: List[List[np.ndarray]] = []

    for r in range(grid_size):
        row = []
        for c in range(grid_size):
            y1, y2 = r * cell_h, (r + 1) * cell_h
            x1, x2 = c * cell_w, (c + 1) * cell_w
            cell = warped[y1:y2, x1:x2]

            margin_h = max(1, cell.shape[0] // 12)
            margin_w = max(1, cell.shape[1] // 12)
            cell = cell[margin_h:-margin_h, margin_w:-margin_w]

            row.append(cell)
        cells.append(row)

    return cells


# -------------------------------
# Main OCR function
# -------------------------------
def extract_sudoku_grid(image_path: str) -> Optional[List[List[int]]]:
    image = cv2.imread(image_path)
    if image is None:
        return None

    # Resize large images
    ratio = 900.0 / max(image.shape[:2])
    if ratio < 1.0:
        image = cv2.resize(
            image,
            (int(image.shape[1] * ratio), int(image.shape[0] * ratio)),
            interpolation=cv2.INTER_AREA
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    edged = cv2.Canny(blur, 50, 150)
    edged = cv2.dilate(edged, np.ones((3, 3), np.uint8))

    quad = _find_puzzle_contour(edged)

    if quad is None:
        th = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11, 2
        )
        th = cv2.dilate(th, np.ones((3, 3), np.uint8))
        quad = _find_puzzle_contour(th)

        if quad is None:
            return None

    warped = _four_point_transform(image, quad)
    side = min(warped.shape[:2])
    warped = cv2.resize(warped, (side, side), interpolation=cv2.INTER_CUBIC)

    cells = _extract_cells(warped, 9)

    grid: List[List[int]] = []
    for r in range(9):
        row_vals = []
        for c in range(9):
            cell_img = _prepare_for_ocr(cells[r][c])
            digit = _ocr_digit(cell_img)
            row_vals.append(digit)
        grid.append(row_vals)

    return grid
