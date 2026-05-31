const roomEl = document.getElementById("current-room");
const roomItemEl = document.getElementById("room-item");
const inventoryListEl = document.getElementById("inventory-list");
const exitsEl = document.getElementById("exit-buttons");
const lastMessageEl = document.getElementById("last-message");
const eventLogEl = document.getElementById("event-log");

const pickupBtn = document.getElementById("pickup-btn");
const refreshBtn = document.getElementById("refresh-btn");
const resetBtn = document.getElementById("reset-btn");
const routeBtn = document.getElementById("route-btn");
const saveBtn = document.getElementById("save-btn");
const loadBtn = document.getElementById("load-btn");
const sendCommandBtn = document.getElementById("send-command-btn");

const routeInput = document.getElementById("route-room");
const saveSlotInput = document.getElementById("save-slot");
const commandInput = document.getElementById("command-input");

let lastKnownState = {
  current_room: "",
  inventory: [],
  room_item: null,
  exits: {},
};

function addLog(message) {
  const entry = document.createElement("li");
  const timestamp = new Date().toLocaleTimeString();
  entry.textContent = `[${timestamp}] ${message}`;
  eventLogEl.prepend(entry);

  while (eventLogEl.children.length > 25) {
    eventLogEl.removeChild(eventLogEl.lastChild);
  }
}

function setMessage(message) {
  lastMessageEl.textContent = message;
  addLog(message);
}

function renderState(state) {
  lastKnownState = state;
  roomEl.textContent = state.current_room || "Unknown";

  if (state.room_item) {
    roomItemEl.textContent = `Item in room: ${state.room_item}`;
    pickupBtn.disabled = false;
  } else {
    roomItemEl.textContent = "No item in room.";
    pickupBtn.disabled = true;
  }

  inventoryListEl.innerHTML = "";
  if (!state.inventory || state.inventory.length === 0) {
    const item = document.createElement("li");
    item.className = "tag empty";
    item.textContent = "Empty";
    inventoryListEl.appendChild(item);
  } else {
    state.inventory.forEach((invItem) => {
      const item = document.createElement("li");
      item.className = "tag";
      item.textContent = invItem;
      inventoryListEl.appendChild(item);
    });
  }

  exitsEl.innerHTML = "";
  const exits = state.exits || {};
  const directions = Object.keys(exits);

  if (directions.length === 0) {
    const noExit = document.createElement("p");
    noExit.textContent = "No exits available.";
    exitsEl.appendChild(noExit);
    return;
  }

  directions.forEach((direction) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn";
    btn.textContent = `Go ${direction}`;
    btn.addEventListener("click", () => sendCommand(`go ${direction}`));
    exitsEl.appendChild(btn);
  });
}

async function getState() {
  const response = await fetch("/state");
  if (!response.ok) {
    throw new Error("Failed to get game state.");
  }
  const state = await response.json();
  renderState(state);
}

async function sendCommand(command) {
  const response = await fetch("/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command }),
  });

  const data = await response.json();
  if (!response.ok) {
    setMessage(data.error || "Command failed.");
    return;
  }

  setMessage(data.message || "Action complete.");
  await getState();
}

async function saveGame(slot) {
  const response = await fetch(`/save/${encodeURIComponent(slot)}`, { method: "POST" });
  const data = await response.json();
  setMessage(data.message || "Save action finished.");
}

async function loadGame(slot) {
  await sendCommand(`load ${slot}`);
}

async function resetGame() {
  const response = await fetch("/reset", { method: "POST" });
  const data = await response.json();
  setMessage(data.message || "Game reset.");
  await getState();
}

refreshBtn.addEventListener("click", async () => {
  try {
    await getState();
    setMessage("State refreshed.");
  } catch (error) {
    setMessage(String(error));
  }
});

resetBtn.addEventListener("click", async () => {
  try {
    await resetGame();
  } catch (error) {
    setMessage(String(error));
  }
});

pickupBtn.addEventListener("click", async () => {
  if (!lastKnownState.room_item) {
    setMessage("There is no item to pick up.");
    return;
  }

  try {
    await sendCommand(`get ${lastKnownState.room_item}`);
  } catch (error) {
    setMessage(String(error));
  }
});

routeBtn.addEventListener("click", async () => {
  const roomName = routeInput.value.trim();
  if (!roomName) {
    setMessage("Enter a room name first.");
    return;
  }

  try {
    await sendCommand(`route ${roomName}`);
  } catch (error) {
    setMessage(String(error));
  }
});

saveBtn.addEventListener("click", async () => {
  const slot = saveSlotInput.value.trim() || "default";
  try {
    await saveGame(slot);
  } catch (error) {
    setMessage(String(error));
  }
});

loadBtn.addEventListener("click", async () => {
  const slot = saveSlotInput.value.trim() || "default";
  try {
    await loadGame(slot);
  } catch (error) {
    setMessage(String(error));
  }
});

sendCommandBtn.addEventListener("click", async () => {
  const command = commandInput.value.trim();
  if (!command) {
    setMessage("Enter a command first.");
    return;
  }

  try {
    await sendCommand(command);
    commandInput.value = "";
  } catch (error) {
    setMessage(String(error));
  }
});

commandInput.addEventListener("keydown", async (event) => {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  sendCommandBtn.click();
});

(async function bootstrap() {
  try {
    await getState();
    setMessage("Web UI ready. Explore the mansion.");
  } catch (error) {
    setMessage(`Startup failed: ${String(error)}`);
  }
})();
