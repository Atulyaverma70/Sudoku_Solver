import React, { useState } from "react";
import SudokuGrid from "./SudokuGrid";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [grid, setGrid] = useState(Array(9).fill(Array(9).fill(0)));

  const API = ""; // Flask backend (same origin)

  const handleSolve = async () => {
    setMessage("Solving...");
    try {
      const resp = await fetch(`${API}/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grid }),
      });
      const data = await resp.json();
      if (resp.ok && data.solution) {
        setGrid(data.solution);
        setMessage("Sudoku solved!");
      } else {
        setMessage(data.error || "Failed to solve");
      }
    } catch (err) {
      setMessage("Connection error: " + err.message);
    }
  };

  const handleClear = () => {
    setGrid(Array(9).fill(Array(9).fill(0)));
    setMessage("");
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setMessage("Processing image...");
    const formData = new FormData();
    formData.append("image", file);

    try {
      const resp = await fetch(`${API}/ocr`, { method: "POST", body: formData });
      const data = await resp.json();
      if (resp.ok && data.grid) {
        setGrid(data.grid);
        setMessage("Grid extracted from image!");
      } else {
        setMessage(data.error || "Image processing failed");
      }
    } catch (err) {
      setMessage("Upload failed: " + err.message);
    }
  };

  return (
    <div className="container">
      <h1>Sudoku Solver (OCR)</h1>
      <div className="controls">
        <input type="file" accept="image/*" onChange={handleImageUpload} />
        <button className="btn solve-btn" onClick={handleSolve}>Solve Sudoku</button>
        <button className="btn clear-btn" onClick={handleClear}>Clear</button>
      </div>
      <div className={`message ${message.includes("error") ? "error" : message.includes("solved") ? "success" : "info"}`}>
        {message}
      </div>
      <SudokuGrid grid={grid} setGrid={setGrid} />
    </div>
  );
}

export default App;
