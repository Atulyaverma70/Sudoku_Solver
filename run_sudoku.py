image_path = "_uploaded_sudoku.jpg"  # Change this to your image file
grid = extract_sudoku_grid(image_path)

if grid:
    print("Extracted Sudoku Grid:")
    for row in grid:
        print(row)
else:
    print("Failed to extract grid.")
