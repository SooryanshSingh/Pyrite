

const cellsContainer = document.getElementById("cellsContainer");
const addCellButton = document.getElementById("addCell");
const markButton = document.getElementById("addMark");

// Load Code Cells
async function loadCells() {
  try {
    const response = await fetch(`/notebook/${notebookId}/cells/`);
    const cells = await response.json();
    cells.forEach(cell => renderCell(cell.cell_id, cell.code || ""));
  } catch (error) {
    console.error("Error loading cells:", error.message);
  }
}

// Load Markdown Cells
async function loadMark() {
  try {
    const response = await fetch(`/notebook/${notebookId}/mark`);
    const cells = await response.json();
    cells.forEach(cell => renderM(cell.cell_id, cell.code || ""));
  } catch (error) {
    console.error("Error loading markdown:", error.message);
  }
}

// Render Code Cell
function renderCell(cellId, code = "") {
  const cellDiv = document.createElement("div");
  cellDiv.id = `cell-${cellId}`;
  cellDiv.innerHTML = `
    <textarea id="code-${cellId}" class="note-content" rows="5" cols="50"
      style="width: 100%; min-height: 100px; padding: 10px; resize: none;" 
      placeholder="Write your code here...">${code}</textarea>
    <button class="save-note" onclick="runCellCode('${notebookId}', '${cellId}')">Run Code</button>
    <button class="delete-note" onclick="deleteCell('${notebookId}', '${cellId}')">Delete Cell</button>
    <div class="output" id="output-${cellId}">Output will appear here...</div>
  `;
  cellsContainer.appendChild(cellDiv);
}

// Render Markdown Cell
function renderM(cellId, code = "") {
  const cellDiv = document.createElement("div");
  cellDiv.id = `cell-${cellId}`;
  cellDiv.innerHTML = `
    <textarea id="code-${cellId}" class="note-content" rows="5" cols="50"
      style="width: 100%; min-height: 100px; padding: 10px; resize: none;" 
      placeholder="Write your markup here...">${code}</textarea>
    <button class="save-note" onclick="runMark('${cellId}')">Run Markup</button>
    <button class="delete-note" onclick="deleteMark('${cellId}')">Delete Cell</button>
    <div class="output" id="outputm-${cellId}">Output will appear here...</div>
  `;
  cellsContainer.appendChild(cellDiv);
}

// Add Code Cell
addCellButton.addEventListener("click", async () => {
  try {
    const response = await fetch(`/notebook/${notebookId}/add_cell/`, {
      method: "POST"
    });
    const result = await response.json();
    if (!result.cell_id) throw new Error("Failed to get cell ID.");
    renderCell(result.cell_id);
  } catch (error) {
    alert("Error adding cell: " + error.message);
  }
});

// Add Markdown Cell
markButton.addEventListener("click", async () => {
  try {
    const response = await fetch(`/notebook/${notebookId}/add_mark`, {
      method: "POST"
    });
    const result = await response.json();
    if (!result.cell_id) throw new Error("Failed to get cell ID.");
    renderM(result.cell_id);
  } catch (error) {
    alert("Error adding markdown cell: " + error.message);
  }
});

// Run Code Cell
function runCellCode(notebookId, cellId) {
  const codeInput = document.getElementById(`code-${cellId}`);
  const outputDiv = document.getElementById(`output-${cellId}`);
  if (!codeInput || !outputDiv) return;

  fetch(`/notebook/${notebookId}/cell/${cellId}/run/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: codeInput.value })
  })
  .then(res => res.json())
  .then(data => outputDiv.innerText = data.output)
  .catch(err => outputDiv.innerText = `Error: ${err.message}`);
}

// Delete Code Cell
function deleteCell(notebookId, cellId) {
  fetch(`/notebook/${notebookId}/cell/${cellId}/delete/`, {
    method: "DELETE"
  })
  .then(res => {
    if (!res.ok) throw new Error("Delete failed");
    return res.json();
  })
  .then(data => {
    alert(data.message || "Deleted");
    const el = document.getElementById(`cell-${cellId}`);
    if (el) el.remove();
  })
  .catch(err => alert("Error: " + err.message));
}

// Run Markdown
function runMark(cellId) {
  const codeInput = document.getElementById(`code-${cellId}`);
  const outputDiv = document.getElementById(`outputm-${cellId}`);
  if (!codeInput || !outputDiv) return;

  fetch(`/notebook/${notebookId}/markup/${cellId}/run/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: codeInput.value })
  })
  .then(res => res.text())
  .then(text => {
    try {
      const data = JSON.parse(text);
      outputDiv.innerHTML = data.rendered_html || "No output.";
    } catch (e) {
      outputDiv.innerText = "Failed to parse response.";
    }
  })
  .catch(err => outputDiv.innerText = `Error: ${err.message}`);
}

// Delete Markdown Cell
function deleteMark(cellId) {
  fetch(`/notebook/${notebookId}/markup/${cellId}/delete/`, {
    method: "DELETE"
  })
  .then(res => {
    if (!res.ok) throw new Error("Delete failed");
    return res.json();
  })
  .then(data => {
    alert(data.message || "Deleted");
    const el = document.getElementById(`cell-${cellId}`);
    if (el) el.remove();
  })
  .catch(err => alert("Error: " + err.message));
}

// Init
checkUser();
loadCells();
loadMark();
