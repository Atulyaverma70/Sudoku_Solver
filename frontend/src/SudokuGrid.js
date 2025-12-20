import React from "react";

function SudokuGrid({ grid, setGrid }) {
  const handleChange = (r, c, value) => {
    const newGrid = grid.map(row => [...row]);
    newGrid[r][c] = value ? Math.min(9, Math.max(0, parseInt(value))) : 0;
    setGrid(newGrid);
  };

  return (
    <table id="sudokuGrid">
      <tbody>
        {grid.map((row, r) => (
          <tr key={r}>
            {row.map((val, c) => (
              <td key={c} className={`${c % 3 === 2 ? "thick-right" : ""} ${r % 3 === 2 ? "thick-bottom" : ""}`}>
                <input
                  type="number"
                  min="0"
                  max="9"
                  value={val || ""}
                  onChange={(e) => handleChange(r, c, e.target.value)}
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default SudokuGrid;
