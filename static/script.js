document.addEventListener("DOMContentLoaded", () => {

    const gridDiv = document.getElementById("grid");
    const solveBtn = document.getElementById("solveBtn");
    const clearBtn = document.getElementById("clearBtn");
    const imageInput = document.getElementById("imageInput");

    if (!gridDiv) {
        console.error("Grid container not found");
        return;
    }

    const cells = [];

    // Create 9x9 grid
    for (let i = 0; i < 81; i++) {
        const input = document.createElement("input");
        input.type = "number";
        input.min = 1;
        input.max = 9;

        input.addEventListener("input", () => {
            if (input.value < 1 || input.value > 9) {
                input.value = "";
            }
        });

        gridDiv.appendChild(input);
        cells.push(input);
    }

    function getGrid() {
        const grid = [];
        for (let r = 0; r < 9; r++) {
            const row = [];
            for (let c = 0; c < 9; c++) {
                const val = cells[r * 9 + c].value;
                row.push(val ? parseInt(val) : 0);
            }
            grid.push(row);
        }
        return grid;
    }

    function setGrid(grid) {
        grid.flat().forEach((val, i) => {
            cells[i].value = val === 0 ? "" : val;
        });
    }

    function clearGrid() {
        cells.forEach(cell => cell.value = "");
    }

    async function solveSudoku() {
        const response = await fetch("/solve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ grid: getGrid() })
        });

        const data = await response.json();
        if (data.solution) {
            setGrid(data.solution);
        } else {
            alert(data.error || "Unable to solve Sudoku");
        }
    }

    // OCR → ONLY auto-fill grid (NO auto-solve)
    imageInput.addEventListener("change", async () => {
        if (!imageInput.files.length) return;

        const formData = new FormData();
        formData.append("image", imageInput.files[0]);

        const response = await fetch("/ocr", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (!data.grid) {
            alert("OCR failed");
            return;
        }

        setGrid(data.grid);
    });

    solveBtn.addEventListener("click", solveSudoku);
    clearBtn.addEventListener("click", clearGrid);
});
