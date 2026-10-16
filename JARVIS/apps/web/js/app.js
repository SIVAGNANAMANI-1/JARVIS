/**
 * JARVIS AI — Client Application Engine
 * Handles WebSocket events, REST dispatch, Web Speech API voice control, and UI reactivity.
 */

// Configuration endpoints
let AGENT_API_URL = "http://127.0.0.1:8765";
let CLOUD_API_URL = "http://127.0.0.1:8000";
let activeMode = "local"; // "local" or "cloud"
let selectedDeviceId = "local";
let activeTaskId = null;
let ws = null;
let recognition = null;
let isListening = false;
let isSpeaking = false;

// DOM Elements
const commandInput = document.getElementById("commandInput");
const commandForm = document.getElementById("commandForm");
const sendBtn = document.getElementById("sendBtn");
const voiceOrbBtn = document.getElementById("voiceOrbBtn");
const micToggleBtn = document.getElementById("micToggleBtn");
const orbIcon = document.getElementById("orbIcon");
const voiceStatusText = document.getElementById("voiceStatusText");
const voiceSubtitleText = document.getElementById("voiceSubtitleText");
const audioVisualizer = document.getElementById("audioVisualizer");
const taskListStream = document.getElementById("taskListStream");
const activeTasksCount = document.getElementById("activeTasksCount");
const memoryListContainer = document.getElementById("memoryListContainer");
const memoryCountBadge = document.getElementById("memoryCountBadge");
const newMemoryInput = document.getElementById("newMemoryInput");
const saveMemoryBtn = document.getElementById("saveMemoryBtn");
const emergencyStopBtn = document.getElementById("emergencyStopBtn");
const modeToggleBtn = document.getElementById("modeToggleBtn");
const toggleModeLabel = document.getElementById("toggleModeLabel");
const agentStatusText = document.getElementById("agentStatusText");
const agentStatusDot = document.getElementById("agentStatusDot");
const deviceItems = document.querySelectorAll(".device-item");
const quickChips = document.querySelectorAll(".quick-chip");
const approvalModal = document.getElementById("approvalModal");
const approvalActionDetails = document.getElementById("approvalActionDetails");
const approveActionBtn = document.getElementById("approveActionBtn");
const rejectApprovalBtn = document.getElementById("rejectApprovalBtn");

// 1. Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initWebSocket();
  initSpeechRecognition();
  loadInitialData();
  attachEventListeners();
});

// 2. WebSocket Real-Time Connection
function initWebSocket() {
  const wsUrl = AGENT_API_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws";
  
  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[JARVIS WS] Connected to local edge agent.");
      agentStatusText.textContent = "EDGE CONNECTED (127.0.0.1:8765)";
      agentStatusDot.style.background = "var(--emerald-neon)";
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleServerEvent(payload);
      } catch (e) {
        console.warn("[JARVIS WS] Non-JSON payload:", event.data);
      }
    };

    ws.onerror = (err) => {
      console.warn("[JARVIS WS] Connection error:", err);
      agentStatusText.textContent = "EDGE DISCONNECTED (OFFLINE)";
      agentStatusDot.style.background = "var(--rose-neon)";
    };

    ws.onclose = () => {
      console.log("[JARVIS WS] Reconnecting in 3s...");
      setTimeout(initWebSocket, 3000);
    };
  } catch (err) {
    console.error("[JARVIS WS] Init failed:", err);
  }
}

function handleServerEvent(eventData) {
  const { event, data } = eventData;
  console.log(`[JARVIS Event: ${event}]`, data);

  if (event === "task_created" || event === "task_running" || event === "task_updated") {
    renderTaskCard(data);
    updateActiveTaskBadge();
    if (data.status === "COMPLETED") {
      setOrbState("idle", "Ready for next command.");
      speakResponse(`Task complete. ${data.result_summary || ''}`);
    } else if (data.status === "FAILED") {
      setOrbState("idle", "Task encountered an issue.");
      speakResponse(`Task failed: ${data.error_message || 'Unknown error'}`);
    }
  } else if (event === "task_cancelled") {
    renderTaskCard(data);
    updateActiveTaskBadge();
    setOrbState("idle", "Task cancelled by emergency stop.");
    speakResponse("Task has been cancelled.");
  }
}

// 3. Web Speech API (Voice Recognition & Synthesis)
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("Speech Recognition not supported in this browser.");
    micToggleBtn.style.opacity = "0.5";
    micToggleBtn.title = "Speech recognition unavailable in browser";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    isListening = true;
    setOrbState("listening", "Listening to your voice...");
    animateVisualizer(true);
  };

  recognition.onresult = (e) => {
    const transcript = Array.from(e.results)
      .map(r => r[0].transcript)
      .join("");
    commandInput.value = transcript;
    voiceSubtitleText.textContent = `"${transcript}"`;
  };

  recognition.onerror = (e) => {
    console.warn("Speech recognition error:", e.error);
    isListening = false;
    setOrbState("idle", "Voice recognition stopped.");
    animateVisualizer(false);
  };

  recognition.onend = () => {
    isListening = false;
    animateVisualizer(false);
    const cmd = commandInput.value.trim();
    if (cmd) {
      executeCommand(cmd);
    } else {
      setOrbState("idle", "Ready for your instruction.");
    }
  };
}

function toggleListening() {
  if (!recognition) {
    alert("Speech recognition is not supported in this browser. Please use the text input.");
    return;
  }

  if (isListening) {
    recognition.stop();
  } else {
    window.speechSynthesis.cancel(); // Stop speaking if assistant was talking
    try {
      recognition.start();
    } catch (e) {
      console.warn("Recognition already active", e);
    }
  }
}

function speakResponse(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();

  // Strip excessive markdown or hashes from speech
  const cleanText = text.replace(/[*_#`[\]()]/g, "").slice(0, 200);
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.05;
  utterance.pitch = 0.95;

  utterance.onstart = () => {
    isSpeaking = true;
    setOrbState("speaking", "JARVIS speaking...");
    animateVisualizer(true);
  };

  utterance.onend = () => {
    isSpeaking = false;
    setOrbState("idle", "Ready for instruction.");
    animateVisualizer(false);
  };

  window.speechSynthesis.speak(utterance);
}

function setOrbState(state, statusText) {
  const heroCard = document.getElementById("heroReactorCard");
  heroCard.classList.remove("orb-state-listening", "orb-state-thinking", "orb-state-speaking");

  if (state === "listening") {
    heroCard.classList.add("orb-state-listening");
    orbIcon.textContent = "🎙️";
  } else if (state === "thinking") {
    heroCard.classList.add("orb-state-thinking");
    orbIcon.textContent = "⚙️";
  } else if (state === "speaking") {
    heroCard.classList.add("orb-state-speaking");
    orbIcon.textContent = "🔊";
  } else {
    orbIcon.textContent = "🎙️";
  }

  if (statusText) {
    voiceStatusText.textContent = statusText;
  }
}

function animateVisualizer(active) {
  const bars = audioVisualizer.querySelectorAll(".visualizer-bar");
  bars.forEach((bar, idx) => {
    if (active) {
      bar.classList.add("active");
      bar.style.animationDelay = `${(idx * 0.08)}s`;
    } else {
      bar.classList.remove("active");
    }
  });
}

// 4. Command Submission & Execution
async function executeCommand(commandText) {
  if (!commandText || !commandText.trim()) return;
  const cmd = commandText.trim();
  commandInput.value = "";

  setOrbState("thinking", "Analyzing and planning execution...");
  animateVisualizer(true);

  const payload = {
    command: cmd,
    target_device_id: selectedDeviceId,
    user_id: "default_user"
  };

  try {
    const endpoint = activeMode === "local" 
      ? `${AGENT_API_URL}/tasks/execute`
      : `${CLOUD_API_URL}/api/v1/tasks`;

    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Execution request failed with status: ${response.status}`);
    }

    const taskResult = await response.json();
    activeTaskId = taskResult.task_id;
    renderTaskCard(taskResult);
    updateActiveTaskBadge();

    // Check if task is a general question answer vs a web navigation redirect
    const qaStep = taskResult.steps?.find(s => s.tool_name === "answer_question");
    const targetUrl = extractTaskUrl(taskResult);

    if (qaStep && qaStep.output) {
      const ans = qaStep.output.answer || taskResult.result_summary;
      setOrbState("speaking", "Here is what I found:");
      speakResponse(ans);
    } else if (targetUrl) {
      setOrbState("speaking", "Redirecting to requested page...");
      speakResponse("Redirecting you now.");
      openDestinationUrl(targetUrl);
    } else if (taskResult.status === "COMPLETED") {
      setOrbState("idle", "Task completed.");
      speakResponse(taskResult.result_summary || "Done.");
    }

  } catch (err) {
    console.error("Execute error:", err);
    setOrbState("idle", "Error occurred.");
    alert(`Could not execute task: ${err.message}. Ensure the local agent is running at ${AGENT_API_URL}.`);
  } finally {
    animateVisualizer(false);
  }
}

let redirectTimer = null;
function extractTaskUrl(task) {
  if (!task || !task.steps) return null;
  // If this task answered a question, do not redirect
  if (task.steps.some(s => s.tool_name === "answer_question")) {
    return null;
  }
  for (const step of task.steps) {
    if (step.output && step.output.url) {
      return step.output.url;
    }
  }
  return null;
}

function openDestinationUrl(url) {
  if (!url) return;
  console.log("[JARVIS Web] Directing user to destination:", url);
  
  const toast = document.getElementById("redirectToast");
  const toastUrl = document.getElementById("redirectToastUrl");
  const nowBtn = document.getElementById("redirectNowBtn");
  const cancelBtn = document.getElementById("cancelRedirectBtn");

  if (toast && toastUrl) {
    toastUrl.textContent = url;
    toast.style.display = "flex";

    if (redirectTimer) clearTimeout(redirectTimer);
    redirectTimer = setTimeout(() => {
      window.location.href = url;
    }, 1200);

    if (nowBtn) {
      nowBtn.onclick = () => {
        if (redirectTimer) clearTimeout(redirectTimer);
        window.location.href = url;
      };
    }

    if (cancelBtn) {
      cancelBtn.onclick = () => {
        if (redirectTimer) clearTimeout(redirectTimer);
        toast.style.display = "none";
      };
    }
  } else {
    // Direct immediate fallback
    setTimeout(() => {
      window.location.href = url;
    }, 800);
  }
}

// 5. Render Task Stream & Steps
function renderTaskCard(task) {
  let card = document.getElementById(`task-${task.task_id}`);
  const statusClass = (task.status || "RUNNING").toLowerCase();
  const targetUrl = extractTaskUrl(task);
  const qaStep = task.steps?.find(s => s.tool_name === "answer_question");

  const statusBadge = `<span class="task-status-pill status-pill-${statusClass}">${task.status}</span>`;

  // Render dedicated AI Answer box if this was a question
  let qaHtml = "";
  if (qaStep && qaStep.output) {
    const ans = qaStep.output.answer || task.result_summary;
    const src = qaStep.output.source || "JARVIS AI Knowledge";
    qaHtml = `
      <div style="background: rgba(0, 240, 255, 0.08); border: 1px solid var(--cyan-neon); border-radius: var(--radius-sm); padding: 1.1rem; margin-top: 0.6rem; box-shadow: 0 0 25px rgba(0, 240, 255, 0.2);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
          <span style="font-weight: 800; color: var(--cyan-neon); font-size: 0.85rem; letter-spacing: 0.1em; text-transform: uppercase; display: flex; align-items: center; gap: 0.4rem;">
            <span>🧠</span> JARVIS Answer
          </span>
          <span style="font-size: 0.72rem; color: #a0aec0; font-family: var(--font-mono); background: rgba(255,255,255,0.06); padding: 0.15rem 0.5rem; border-radius: 4px;">
            ${escapeHtml(src)}
          </span>
        </div>
        <div style="font-size: 0.98rem; line-height: 1.6; color: #ffffff;">
          ${escapeHtml(ans)}
        </div>
        ${qaStep.output?.url ? `<div style="margin-top:0.5rem; font-size:0.75rem;"><a href="${qaStep.output.url}" target="_blank" style="color:var(--cyan-neon); text-decoration:underline;">Source Reference: ${escapeHtml(qaStep.output.url)}</a></div>` : ''}
      </div>
    `;
    if (voiceSubtitleText) {
      voiceSubtitleText.textContent = ans;
    }
  }

  let stepsHtml = "";
  if (task.steps && task.steps.length > 0 && !qaStep) {
    stepsHtml = `
      <div class="task-steps-accordion">
        ${task.steps.map((s, idx) => `
          <div class="step-row">
            <div class="step-indicator">${s.verified ? '✓' : idx + 1}</div>
            <div class="step-content">
              <div>
                <span class="step-tool">${s.tool_name}</span>
                <span class="step-desc">${s.action_description}</span>
                ${s.verified ? '<span style="color:var(--emerald-neon); font-size:0.7rem; margin-left:0.4rem;">[VERIFIED]</span>' : ''}
              </div>
              ${s.output?.url ? `<div style="margin-top:0.35rem; font-size:0.8rem;"><span style="color:var(--cyan-neon);">URL:</span> <a href="${s.output.url}" target="_blank" style="color:#00f0ff; text-decoration:underline;">${escapeHtml(s.output.url)}</a></div>` : ''}
              ${s.output?.stdout ? `<div style="margin-top:0.35rem; font-size:0.75rem; color:var(--emerald-neon); font-family:var(--font-mono);"><strong>Output:</strong> ${escapeHtml(s.output.stdout)}</div>` : ''}
              ${s.output ? `<pre class="step-output-box">${JSON.stringify(s.output, null, 2)}</pre>` : ''}
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  const urlButtonHtml = targetUrl ? `
    <div style="margin-top: 0.65rem;">
      <a href="${targetUrl}" class="hud-btn hud-btn-primary" style="display:inline-flex; align-items:center; gap:0.5rem; text-decoration:none; padding:0.6rem 1.1rem; font-weight:700; box-shadow:0 0 15px rgba(0, 240, 255, 0.4);">
        <span>🚀</span> Redirecting to: ${escapeHtml(targetUrl)} ➔
      </a>
    </div>
  ` : '';

  const summaryHtml = (task.result_summary && !qaStep) ? `
    <div class="task-summary-banner">
      <strong>Summary:</strong> ${escapeHtml(task.result_summary)}
    </div>
  ` : '';

  const cardContent = `
    <div class="task-header-row">
      <div class="task-command-text">⚡ ${escapeHtml(task.command)}</div>
      ${statusBadge}
    </div>
    <div style="font-size:0.75rem; color:var(--text-dim); font-family:var(--font-mono); display:flex; justify-content:space-between;">
      <span>ID: ${task.task_id}</span>
      <span>Target: ${task.target_device_id || 'local'}</span>
    </div>
    ${qaHtml}
    ${stepsHtml}
    ${urlButtonHtml}
    ${summaryHtml}
  `;


  if (card) {
    card.className = `task-card ${statusClass}`;
    card.innerHTML = cardContent;
  } else {
    // Clear initial empty state placeholder if present
    if (taskListStream.querySelector("div[style*='text-align: center']")) {
      taskListStream.innerHTML = "";
    }

    card = document.createElement("div");
    card.id = `task-${task.task_id}`;
    card.className = `task-card ${statusClass}`;
    card.innerHTML = cardContent;
    taskListStream.prepend(card);
  }
}

function updateActiveTaskBadge() {
  const running = document.querySelectorAll(".task-card.running, .task-card.submitted").length;
  activeTasksCount.textContent = `${running} Running`;
}

// 6. Memory Vault
async function loadMemories() {
  try {
    const res = await fetch(`${AGENT_API_URL}/memory`);
    if (!res.ok) return;
    const memories = await res.json();
    memoryCountBadge.textContent = memories.length;

    if (memories.length === 0) {
      memoryListContainer.innerHTML = `<div style="font-size: 0.78rem; color: var(--text-dim); text-align: center; padding: 1rem 0;">No memories recorded yet.</div>`;
      return;
    }

    memoryListContainer.innerHTML = memories.map(m => `
      <div class="memory-item" id="mem-${m.memory_id}">
        <div>
          <div class="memory-key">${escapeHtml(m.key || m.category)}</div>
          <div class="memory-val">${escapeHtml(m.value)}</div>
        </div>
        <button class="delete-mem-btn" onclick="deleteMemory('${m.memory_id}')" title="Delete Memory">✕</button>
      </div>
    `).join("");
  } catch (e) {
    console.warn("Could not load memories:", e);
  }
}

async function saveMemory() {
  const val = newMemoryInput.value.trim();
  if (!val) return;
  newMemoryInput.value = "";

  try {
    const payload = {
      user_id: "default_user",
      category: "preference",
      key: "user_note",
      value: val
    };

    const res = await fetch(`${AGENT_API_URL}/memory`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      loadMemories();
    }
  } catch (e) {
    console.error("Save memory error:", e);
  }
}

window.deleteMemory = async function(memoryId) {
  try {
    const res = await fetch(`${AGENT_API_URL}/memory/${memoryId}`, { method: "DELETE" });
    if (res.ok) {
      const el = document.getElementById(`mem-${memoryId}`);
      if (el) el.remove();
      loadMemories();
    }
  } catch (e) {
    console.error("Delete memory error:", e);
  }
};

// 7. Initial Data Loader
async function loadInitialData() {
  try {
    // 1. Health & Device check
    const healthRes = await fetch(`${AGENT_API_URL}/health`);
    if (healthRes.ok) {
      const data = await healthRes.json();
      document.getElementById("statPlatform").textContent = data.platform || "Windows";
      document.getElementById("sandboxPathDisplay").textContent = data.workspace_root || "JARVIS/workspaces/";
    }

    // 2. Recent Tasks
    const tasksRes = await fetch(`${AGENT_API_URL}/tasks/recent`);
    if (tasksRes.ok) {
      const tasks = await tasksRes.json();
      if (tasks && tasks.length > 0) {
        taskListStream.innerHTML = "";
        tasks.slice(0, 5).forEach(renderTaskCard);
        updateActiveTaskBadge();
      }
    }

    // 3. Memories
    loadMemories();
  } catch (e) {
    console.warn("Initial data load encountered agent offline:", e);
  }
}

// 8. Event Listeners
function attachEventListeners() {
  // Command form submission
  commandForm.addEventListener("submit", (e) => {
    e.preventDefault();
    executeCommand(commandInput.value);
  });

  // Voice orb & mic button
  voiceOrbBtn.addEventListener("click", toggleListening);
  micToggleBtn.addEventListener("click", toggleListening);

  // Quick chips
  quickChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const cmd = chip.getAttribute("data-cmd");
      commandInput.value = cmd;
      executeCommand(cmd);
    });
  });

  // Device switcher
  deviceItems.forEach(item => {
    item.addEventListener("click", () => {
      deviceItems.forEach(d => d.classList.remove("active"));
      item.classList.add("active");
      selectedDeviceId = item.getAttribute("data-device-id");
      console.log(`Target device set to: ${selectedDeviceId}`);
    });
  });

  // Memory save button & enter key
  saveMemoryBtn.addEventListener("click", saveMemory);
  newMemoryInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") saveMemory();
  });

  // Emergency stop
  emergencyStopBtn.addEventListener("click", async () => {
    if (!activeTaskId) {
      alert("No active running task to cancel.");
      return;
    }
    try {
      const res = await fetch(`${AGENT_API_URL}/tasks/${activeTaskId}/cancel`, { method: "POST" });
      if (res.ok) {
        console.log("Emergency stop initiated for:", activeTaskId);
      }
    } catch (e) {
      console.error("Cancel failed:", e);
    }
  });

  // Mode toggle (Local Edge vs AWS Cloud)
  modeToggleBtn.addEventListener("click", () => {
    if (activeMode === "local") {
      activeMode = "cloud";
      toggleModeLabel.textContent = "Mode: AWS Cloud";
      modeToggleBtn.classList.add("hud-btn-primary");
    } else {
      activeMode = "local";
      toggleModeLabel.textContent = "Mode: Local Edge";
      modeToggleBtn.classList.remove("hud-btn-primary");
    }
  });

  // Keyboard shortcut: Space (when not typing) to speak
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && e.target !== commandInput && e.target !== newMemoryInput) {
      e.preventDefault();
      toggleListening();
    }
    if (e.code === "Escape") {
      emergencyStopBtn.click();
    }
  });
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
