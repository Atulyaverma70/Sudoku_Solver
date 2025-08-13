# ocr_processing.py
# Cross-platform Sudoku OCR: no hardcoded tesseract path.

import os
import cv2
import numpy as np
import pytesseract
from typing import List, Optional, Tuple

# Optional: allow override via environment without forcing a path in code
# e.g., export TESSERACT_CMD=/usr/bin/tesseract
_env_cmd = os.environ.get("TESSERACT_CMD")
if _env_cmd:
    pytesseract.pytesseract.tesseract_cmd = _env_cmd

def _order_points(pts: np.ndarray) -> np.ndarray:
    # orders four points as [top-left, top-right, bottom-right, bottom-left]
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

    dst = np.array(
        [[0, 0], [maxW - 1, 0], [maxW - 1, maxH - 1], [0, maxH - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxW, maxH))
    return warped

def _find_puzzle_contour(edged: np.ndarray) -> Optional[np.ndarray]:
    cnts, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2).astype("float32")
    return None

def _prepare_for_ocr(cell: np.ndarray) -> np.ndarray:
    # Resize, binarize, and clean noise from a single cell
    h, w = cell.shape[:2]
    scale = max(1, int(28 / min(h, w)))
    cell = cv2.resize(cell, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY) if cell.ndim == 3 else cell
    # adaptive threshold helps with varied lighting; invert for tesseract’s digit model bias
    bw = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )

    # remove thin lines (grid residue)
    kernel = np.ones((2, 2), np.uint8)
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)

    # center big component (digit) by clearing small noise
    nlabels, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    if nlabels > 1:
        sizes = stats[1:, cv2.CC_STAT_AREA]
        max_label = 1 + int(np.argmax(sizes)) if sizes.size else 0
        mask = np.zeros_like(bw)
        mask[labels == max_label] = 255
        bw = mask

    # invert back so digit is black on white if preferred; tesseract works either way with correct psm
    bw = cv2.bitwise_not(bw)
    return bw

def _ocr_digit(img: np.ndarray) -> int:
    # Use Tesseract with single-character assumption
    config = "--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789"
    txt = pytesseract.image_to_string(img, config=config).strip()
    # Handle cases where OCR returns empty or non-digit
    if len(txt) == 0:
        return 0
    # If multiple chars due to noise, keep first digit
    for ch in txt:
        if ch.isdigit():
            # treat 0 as empty cell
            return int(ch) if ch != "0" else 0
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
            # crop a small margin to avoid grid lines
            mh, mw = max(1, cell.shape[0] // 12), max(1, cell.shape[1] // 12)
            cell = cell[mh:-mh or None, mw:-mw or None]
            row.append(cell)
        cells.append(row)
    return cells

def extract_sudoku_grid(image_path: str) -> Optional[List[List[int]]]:
    """
    Reads an image file, detects the Sudoku board, warps it top-down,
    OCRs each cell, and returns a 9x9 grid with 0 for blanks.
    Returns None if detection fails.
    """
    image = cv2.imread(image_path)
    if image is None:
        return None

    ratio = 900.0 / max(image.shape[:2])
    if ratio < 1.0:
        image = cv2.resize(
            image,
            (int(image.shape[1] * ratio), int(image.shape[0] * ratio)),
            interpolation=cv2.INTER_AREA,
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    # emphasize grid lines
    edged = cv2.Canny(blur, 50, 150)
    edged = cv2.dilate(edged, np.ones((3, 3), np.uint8), iterations=1)

    quad = _find_puzzle_contour(edged)
    if quad is None:
        # try threshold-based fallback
        th = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        th = cv2.bitwise_not(th)
        th = cv2.dilate(th, np.ones((3, 3), np.uint8), iterations=1)
        quad = _find_puzzle_contour(th)
        if quad is None:
            return None

    warped = _four_point_transform(image, quad)

    # Make warped roughly square to minimize skew across cells
    side = min(warped.shape[:2])
    warped = cv2.resize(warped, (side, side), interpolation=cv2.INTER_CUBIC)

    cells = _extract_cells(warped, grid_size=9)
    grid: List[List[int]] = []
    for r in range(9):
        row_vals = []
        for c in range(9):
            cell = _prepare_for_ocr(cells[r][c])
            digit = _ocr_digit(cell)
            row_vals.append(digit)
        grid.append(row_vals)

    return grid

# Optional quick test
if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_processing.py <image_path>")
        sys.exit(1)
    g = extract_sudoku_grid(sys.argv[1])
    print(json.dumps(g) if g else "Detection failed")
