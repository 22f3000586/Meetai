function allowDrop(ev) {
  ev.preventDefault();
}

function drag(ev) {
  ev.dataTransfer.setData("text", ev.target.dataset.taskIndex);
}

async function drop(ev, newStatus, meetingId) {
  ev.preventDefault();

  const taskIndex = ev.dataTransfer.getData("text");
  const card = document.querySelector(`[data-task-index='${taskIndex}']`);
  if (!card) return;

  // move card in UI
  ev.currentTarget.querySelector(".kanban-list").appendChild(card);

  // ✅ instantly update dropdown in editable table
  const dropdown = document.querySelector(`select[name="status_${taskIndex}"]`);
  if (dropdown) {
    dropdown.value = newStatus;
  }

  // save to backend
  const res = await fetch(`/api/task/status/${meetingId}/${taskIndex}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: newStatus })
  });

  if (!res.ok) {
    alert("❌ Failed to update status. Reloading...");
    location.reload();
  }
}
async function addTask(meetingId) {
  const task = document.getElementById("newTask").value.trim();
  const owner = document.getElementById("newOwner").value.trim();
  const due_date = document.getElementById("newDueDate").value;
  const priority = document.getElementById("newPriority").value;
  const status = document.getElementById("newStatus").value;

  if (!task) {
    alert("Task is required!");
    return;
  }

  const res = await fetch(`/api/task/add/${meetingId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task, owner, due_date, priority, status })
  });

  if (!res.ok) {
    alert("Failed to add task");
    return;
  }

  // Close modal and refresh
  location.reload();
}
