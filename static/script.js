const gridDiv = document.getElementById("grid");

for (let i = 0; i < 81; i++) {
    const input = document.createElement("input");
    input.type = "number";
    input.min = 1;
    input.max = 9;
    gridDiv.appendChild(input);
}

function getGrid() {
    const inputs = document.querySelectorAll("#grid input");
    const grid = [];

    for (let i = 0; i < 9; i++) {
        const row = [];
        for (let j = 0; j < 9; j++) {
            const value = inputs[i * 9 + j].value;
            row.push(value ? parseInt(value) : 0);
        }
        grid.push(row);
    }
    return grid;
}

function setGrid(grid) {
    const inputs = document.querySelectorAll("#grid input");
    grid.flat().forEach((val, i) => {
        inputs[i].value = val || "";
    });
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
        alert("Unable to solve Sudoku");
    }
}

async function uploadImage() {
    const fileInput = document.getElementById("imageInput");
    if (!fileInput.files.length) {
        alert("Select an image first");
        return;
    }

    const formData = new FormData();
    formData.append("image", fileInput.files[0]);

    const response = await fetch("/ocr", {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    if (data.grid) {
        setGrid(data.grid);
    } else {
        alert("OCR failed");
    }
}
