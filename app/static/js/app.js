/**
 * Comic Voice Agent - Main Application JavaScript
 * Accessible, voice-enabled comic book reader
 */

// ==========================================
// Global State
// ==========================================
const state = {
  sessionId: Math.random().toString(36).substring(2, 15),
  websocket: null,
  isAudioEnabled: true,
  isRecording: false,
  comicLoaded: false,
  currentPage: 1,
  totalPages: 0,
  comicTitle: "",
  settings: {
    speechRate: 1.0,
    voice: "Puck",
    childMode: false,
    autoAdvance: false,
    highContrast: false,
  },
};

// ==========================================
// DOM Elements
// ==========================================
const elements = {
  // Upload
  dropZone: document.getElementById("drop-zone"),
  fileInput: document.getElementById("file-input"),
  uploadProgress: document.getElementById("upload-progress"),
  progressFill: document.getElementById("progress-fill"),
  progressText: document.getElementById("progress-text"),
  uploadSection: document.getElementById("upload-section"),

  // Reader
  readerSection: document.getElementById("reader-section"),
  comicTitle: document.getElementById("comic-title"),
  comicAuthor: document.getElementById("comic-author"),
  currentPage: document.getElementById("current-page"),
  totalPages: document.getElementById("total-pages"),

  // Messages
  messages: document.getElementById("messages"),
  typingIndicator: document.getElementById("typing-indicator"),

  // Navigation
  prevPageBtn: document.getElementById("prev-page-btn"),
  nextPageBtn: document.getElementById("next-page-btn"),
  readBtn: document.getElementById("read-btn"),

  // Input
  messageForm: document.getElementById("message-form"),
  messageInput: document.getElementById("message-input"),
  sendBtn: document.getElementById("send-btn"),

  // Voice
  startVoiceBtn: document.getElementById("start-voice-btn"),
  stopVoiceBtn: document.getElementById("stop-voice-btn"),
  recordingIndicator: document.getElementById("recording-indicator"),

  // Status
  statusDot: document.getElementById("status-dot"),
  connectionStatus: document.getElementById("connection-status"),

  // Modals
  settingsModal: document.getElementById("settings-modal"),
  helpModal: document.getElementById("help-modal"),

  // Buttons
  helpBtn: document.getElementById("help-btn"),
  settingsBtn: document.getElementById("settings-btn"),
  highContrastBtn: document.getElementById("high-contrast-btn"),
  closeSettings: document.getElementById("close-settings"),
  closeHelp: document.getElementById("close-help"),

  // Settings inputs
  speechRate: document.getElementById("speech-rate"),
  speechRateValue: document.getElementById("speech-rate-value"),
  voiceSelect: document.getElementById("voice-select"),
  childMode: document.getElementById("child-mode"),
  autoAdvance: document.getElementById("auto-advance"),

  // Screen reader announcer
  srAnnouncer: document.getElementById("sr-announcer"),
};

// ==========================================
// Audio Processing (from reference project)
// ==========================================
let audioContext = null;
let audioPlayerNode = null;
let audioRecorderNode = null;
let mediaStream = null;

async function initAudio() {
  try {
    audioContext = new AudioContext({ sampleRate: 24000 });

    // Load audio worklet processors
    await audioContext.audioWorklet.addModule(
      "/static/js/pcm-player-processor.js"
    );
    await audioContext.audioWorklet.addModule(
      "/static/js/pcm-recorder-processor.js"
    );

    // Create player node
    audioPlayerNode = new AudioWorkletNode(
      audioContext,
      "pcm-player-processor"
    );
    audioPlayerNode.connect(audioContext.destination);

    console.log("Audio initialized successfully");
  } catch (error) {
    console.error("Error initializing audio:", error);
    state.isAudioEnabled = false;
  }
}

async function startRecording() {
  if (!state.isAudioEnabled || state.isRecording) return;

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const source = audioContext.createMediaStreamSource(mediaStream);

    audioRecorderNode = new AudioWorkletNode(
      audioContext,
      "pcm-recorder-processor"
    );
    audioRecorderNode.port.onmessage = (event) => {
      if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
        const audioData = event.data;
        const base64Audio = arrayBufferToBase64(audioData);
        sendToServer({
          mime_type: "audio/pcm",
          data: base64Audio,
          role: "user",
        });
      }
    };

    source.connect(audioRecorderNode);
    audioRecorderNode.connect(audioContext.destination);

    state.isRecording = true;
    updateRecordingUI(true);
    announce("Recording started. Speak your command.");
  } catch (error) {
    console.error("Error starting recording:", error);
    announce("Could not access microphone. Please check permissions.");
  }
}

function stopRecording() {
  if (!state.isRecording) return;

  if (audioRecorderNode) {
    audioRecorderNode.disconnect();
    audioRecorderNode = null;
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }

  state.isRecording = false;
  updateRecordingUI(false);
  announce("Recording stopped.");
}

function updateRecordingUI(isRecording) {
  elements.startVoiceBtn.hidden = isRecording;
  elements.stopVoiceBtn.hidden = !isRecording;
  elements.recordingIndicator.hidden = !isRecording;
}

// ==========================================
// WebSocket Connection
// ==========================================
function connectWebSocket() {
  const wsUrl = `ws://${window.location.host}/ws/${state.sessionId}?is_audio=${state.isAudioEnabled}`;
  state.websocket = new WebSocket(wsUrl);

  state.websocket.onopen = () => {
    console.log("WebSocket connected");
    elements.connectionStatus.textContent = "Connected";
    elements.statusDot.classList.add("connected");
    elements.sendBtn.disabled = false;
    announce("Connected to server. Ready to use.");
  };

  state.websocket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleServerMessage(message);
  };

  state.websocket.onclose = () => {
    console.log("WebSocket disconnected");
    elements.connectionStatus.textContent = "Disconnected. Reconnecting...";
    elements.statusDot.classList.remove("connected");
    elements.sendBtn.disabled = true;

    // Reconnect after delay
    setTimeout(connectWebSocket, 3000);
  };

  state.websocket.onerror = (error) => {
    console.error("WebSocket error:", error);
    elements.connectionStatus.textContent = "Connection error";
  };
}

function sendToServer(message) {
  if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
    state.websocket.send(JSON.stringify(message));
  }
}

function handleServerMessage(message) {
  console.log("Server message:", message);

  // Hide typing indicator when turn is complete
  if (message.turn_complete) {
    elements.typingIndicator.classList.remove("visible");
    return;
  }

  // Handle audio
  if (message.mime_type === "audio/pcm" && audioPlayerNode) {
    const audioData = base64ToArrayBuffer(message.data);
    audioPlayerNode.port.postMessage(audioData);
  }

  // Handle text
  if (message.mime_type === "text/plain") {
    elements.typingIndicator.classList.remove("visible");
    addMessage(message.data, "agent");
  }

  // Handle comic data updates
  if (message.comic_loaded) {
    handleComicLoaded(message);
  }

  // Handle page navigation
  if (message.page_changed) {
    updatePageDisplay(message.current_page, message.total_pages);
  }
}

// ==========================================
// File Upload
// ==========================================
function setupUpload() {
  // Click to upload
  elements.dropZone.addEventListener("click", () => {
    elements.fileInput.click();
  });

  // Keyboard accessibility
  elements.dropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      elements.fileInput.click();
    }
  });

  // File input change
  elements.fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) uploadFile(file);
  });

  // Drag and drop
  elements.dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    elements.dropZone.classList.add("drag-over");
  });

  elements.dropZone.addEventListener("dragleave", () => {
    elements.dropZone.classList.remove("drag-over");
  });

  elements.dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    elements.dropZone.classList.remove("drag-over");

    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      uploadFile(file);
    } else {
      announce("Please upload a PDF file.");
    }
  });
}

async function uploadFile(file) {
  if (!file || file.type !== "application/pdf") {
    announce("Please select a valid PDF file.");
    return;
  }

  announce(`Uploading ${file.name}. Please wait.`);

  // Show progress
  elements.uploadProgress.setAttribute("aria-hidden", "false");
  elements.uploadProgress.style.display = "block";
  elements.progressFill.style.width = "0%";
  elements.progressText.textContent = "Uploading...";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Upload failed");
    }

    // Update progress
    elements.progressFill.style.width = "50%";
    elements.progressText.textContent = "Processing comic...";

    const result = await response.json();

    // Complete progress
    elements.progressFill.style.width = "100%";
    elements.progressText.textContent = "Complete!";

    // Handle success
    setTimeout(() => {
      handleComicLoaded(result);
      elements.uploadProgress.style.display = "none";
    }, 500);
  } catch (error) {
    console.error("Upload error:", error);
    elements.progressText.textContent = "Upload failed. Please try again.";
    announce("Upload failed. Please try again.");
  }
}

function handleComicLoaded(data) {
  state.comicLoaded = true;
  state.currentPage = 1;
  state.totalPages = data.page_count || data.total_pages || 1;
  state.comicTitle = data.title || "Comic Book";

  // Update UI
  elements.comicTitle.textContent = data.title || "Comic Book";
  elements.comicAuthor.textContent = data.author ? `by ${data.author}` : "";
  updatePageDisplay(1, state.totalPages);

  // Show reader section, hide upload
  elements.uploadSection.hidden = true;
  elements.readerSection.hidden = false;

  // Add welcome message
  const welcomeMsg = `Welcome! "${state.comicTitle}" is ready with ${state.totalPages} pages. Say "read" to start, or "help" for commands.`;
  addMessage(welcomeMsg, "agent");
  announce(welcomeMsg);

  // Focus on read button for accessibility
  elements.readBtn.focus();
}

// ==========================================
// Navigation
// ==========================================
function setupNavigation() {
  elements.prevPageBtn.addEventListener("click", () => navigatePage(-1));
  elements.nextPageBtn.addEventListener("click", () => navigatePage(1));
  elements.readBtn.addEventListener("click", readCurrentPage);
}

function navigatePage(direction) {
  const newPage = state.currentPage + direction;

  if (newPage < 1 || newPage > state.totalPages) {
    announce(
      direction < 0 ? "Already on first page." : "Already on last page."
    );
    return;
  }

  state.currentPage = newPage;
  updatePageDisplay(newPage, state.totalPages);

  // Send navigation command to server
  sendToServer({
    mime_type: "text/plain",
    data: direction > 0 ? "next page" : "previous page",
    role: "user",
  });

  showTypingIndicator();
}

function updatePageDisplay(current, total) {
  state.currentPage = current;
  state.totalPages = total;

  elements.currentPage.textContent = current;
  elements.totalPages.textContent = total;

  // Update button states
  elements.prevPageBtn.disabled = current <= 1;
  elements.nextPageBtn.disabled = current >= total;

  // Update ARIA
  const pageInfo = `Page ${current} of ${total}`;
  document
    .getElementById("page-indicator")
    .setAttribute("aria-label", pageInfo);
}

function readCurrentPage() {
  sendToServer({
    mime_type: "text/plain",
    data: "read this page",
    role: "user",
  });
  showTypingIndicator();
  addMessage("Read this page", "user");
}

// ==========================================
// Messages
// ==========================================
function setupMessageForm() {
  elements.messageForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = elements.messageInput.value.trim();
    if (message) {
      sendMessage(message);
      elements.messageInput.value = "";
    }
  });
}

function sendMessage(text) {
  addMessage(text, "user");
  sendToServer({
    mime_type: "text/plain",
    data: text,
    role: "user",
  });
  showTypingIndicator();
}

function addMessage(text, sender) {
  const messageEl = document.createElement("p");
  messageEl.textContent = text;
  messageEl.className = sender === "user" ? "user-message" : "agent-message";

  // Add ARIA attributes for screen readers
  messageEl.setAttribute("role", "article");
  messageEl.setAttribute(
    "aria-label",
    `${sender === "user" ? "You said" : "Agent says"}: ${text}`
  );

  elements.messages.appendChild(messageEl);
  elements.messages.scrollTop = elements.messages.scrollHeight;

  // Announce to screen readers if it's an agent message
  if (sender === "agent") {
    announce(text);
  }
}

function showTypingIndicator() {
  elements.typingIndicator.classList.add("visible");
}

// ==========================================
// Accessibility
// ==========================================
function announce(message) {
  // Use ARIA live region to announce to screen readers
  elements.srAnnouncer.textContent = "";
  setTimeout(() => {
    elements.srAnnouncer.textContent = message;
  }, 100);
}

function setupKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Don't trigger if user is typing in an input
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
      return;
    }

    // Don't trigger if modal is open
    if (
      elements.settingsModal.getAttribute("aria-hidden") === "false" ||
      elements.helpModal.getAttribute("aria-hidden") === "false"
    ) {
      if (e.key === "Escape") {
        closeAllModals();
      }
      return;
    }

    switch (e.key) {
      case " ":
        e.preventDefault();
        readCurrentPage();
        break;
      case "ArrowRight":
        e.preventDefault();
        navigatePage(1);
        break;
      case "ArrowLeft":
        e.preventDefault();
        navigatePage(-1);
        break;
      case "r":
      case "R":
        e.preventDefault();
        sendMessage("repeat");
        break;
      case "d":
      case "D":
        e.preventDefault();
        sendMessage("describe this");
        break;
      case "h":
      case "H":
        e.preventDefault();
        openModal(elements.helpModal);
        break;
      case "Escape":
        stopRecording();
        break;
    }
  });
}

// ==========================================
// Modals
// ==========================================
function setupModals() {
  // Help button
  elements.helpBtn.addEventListener("click", () => {
    openModal(elements.helpModal);
  });

  // Settings button
  elements.settingsBtn.addEventListener("click", () => {
    openModal(elements.settingsModal);
  });

  // Close buttons
  elements.closeHelp.addEventListener("click", () => {
    closeModal(elements.helpModal);
  });

  elements.closeSettings.addEventListener("click", () => {
    saveSettings();
    closeModal(elements.settingsModal);
  });

  // Close on backdrop click
  [elements.helpModal, elements.settingsModal].forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        closeModal(modal);
      }
    });
  });

  // Settings controls
  elements.speechRate.addEventListener("input", (e) => {
    elements.speechRateValue.textContent = `${e.target.value}x`;
  });

  // High contrast toggle
  elements.highContrastBtn.addEventListener("click", toggleHighContrast);
}

function openModal(modal) {
  modal.setAttribute("aria-hidden", "false");
  modal.querySelector("button, input, select").focus();
  document.body.style.overflow = "hidden";
}

function closeModal(modal) {
  modal.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

function closeAllModals() {
  closeModal(elements.helpModal);
  closeModal(elements.settingsModal);
}

function saveSettings() {
  state.settings.speechRate = parseFloat(elements.speechRate.value);
  state.settings.voice = elements.voiceSelect.value;
  state.settings.childMode = elements.childMode.checked;
  state.settings.autoAdvance = elements.autoAdvance.checked;

  // Send settings to server
  sendToServer({
    mime_type: "application/json",
    data: JSON.stringify({ type: "settings", settings: state.settings }),
    role: "system",
  });

  announce("Settings saved.");
}

function toggleHighContrast() {
  state.settings.highContrast = !state.settings.highContrast;
  document.body.classList.toggle("high-contrast", state.settings.highContrast);
  announce(
    state.settings.highContrast
      ? "High contrast mode enabled."
      : "High contrast mode disabled."
  );
}

// ==========================================
// Voice Controls
// ==========================================
function setupVoiceControls() {
  elements.startVoiceBtn.addEventListener("click", startRecording);
  elements.stopVoiceBtn.addEventListener("click", stopRecording);
}

// ==========================================
// Utility Functions
// ==========================================
function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

// ==========================================
// Initialize Application
// ==========================================
async function init() {
  console.log("Initializing Comic Voice Agent...");

  // Setup UI components
  setupUpload();
  setupNavigation();
  setupMessageForm();
  setupModals();
  setupVoiceControls();
  setupKeyboardShortcuts();

  // Initialize audio
  await initAudio();

  // Connect WebSocket
  connectWebSocket();

  // Initial announcement
  announce("Comic Voice Agent loaded. Upload a comic book to begin.");

  console.log("Initialization complete.");
}

// Start the application when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
