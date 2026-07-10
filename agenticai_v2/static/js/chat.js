const EMOJIS = [
  "😀", "😄", "😁", "😊", "🙂", "😉", "😍", "🤔", "😅", "😂",
  "👍", "👎", "🙏", "👏", "🤝", "💪", "✅", "❌", "⚠️", "❓",
  "💰", "💵", "📈", "📉", "📊", "🏦", "📄", "📅", "⏰", "🔍",
  "😢", "😡", "😴", "🎉", "🔥", "⭐", "❤️", "💡", "📌", "🚀",
];

const SIDEBAR_COLLAPSED_KEY = "loanqa.sidebarCollapsed";

let sessions = [];
let currentSessionId = null;

const sidebarEl = document.getElementById("sidebar");
const sidebarToggleBtn = document.getElementById("sidebar-toggle");
const searchInput = document.getElementById("search-input");
const sessionListEl = document.getElementById("session-list");
const chatMainEl = document.getElementById("chat-main");
const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const newChatBtn = document.getElementById("new-chat-btn");
const emojiBtn = document.getElementById("emoji-btn");
const emojiPanel = document.getElementById("emoji-panel");
const suggestionChipsEl = document.getElementById("suggestion-chips");
const setupModal = document.getElementById("setup-modal");
const setupModalTitle = document.getElementById("setup-modal-title");
const setupModalMessage = document.getElementById("setup-modal-message");
const setupModalCloseBtn = document.getElementById("setup-modal-close-btn");
const setupModalDismissBtn = document.getElementById("setup-modal-dismiss-btn");

function renderMarkdown(text) {
  const html = marked.parse(text ?? "");
  return DOMPurify.sanitize(html);
}

function setEmptyState(isEmpty) {
  chatMainEl.classList.toggle("is-empty", isEmpty);
}

function renderSessionList() {
  const query = (searchInput.value || "").trim().toLowerCase();
  const filtered = query
    ? sessions.filter((s) => (s.title || "").toLowerCase().includes(query))
    : sessions;

  sessionListEl.innerHTML = "";
  for (const s of filtered) {
    const item = document.createElement("div");
    item.className = "session-item" + (s.id === currentSessionId ? " active" : "");
    item.textContent = s.title || "แชทใหม่";
    item.addEventListener("click", () => selectSession(s.id));
    sessionListEl.appendChild(item);
  }
}

function addBubble(role, contentHtmlOrText, { markdown = false, pending = false } = {}) {
  const row = document.createElement("div");
  row.className = "bubble-row " + role;
  const col = document.createElement("div");
  col.className = "bubble-col";
  const bubble = document.createElement("div");
  bubble.className = "bubble" + (pending ? " pending" : "");
  bubble.innerHTML = markdown ? renderMarkdown(contentHtmlOrText) : escapeHtml(contentHtmlOrText);
  col.appendChild(bubble);
  row.appendChild(col);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

function attachMeta(bubbleEl, meta) {
  if (!meta) return;
  const tags = [];
  for (const tool of meta.tools_used || []) tags.push(`🔧 ${tool}`);
  if (meta.model) tags.push(`🤖 ${meta.model}`);
  if (meta.duration_seconds != null) tags.push(`⏱ ${meta.duration_seconds.toFixed(1)}s`);
  if (meta.tokens_per_second != null) tags.push(`⚡ ${meta.tokens_per_second.toFixed(1)} tok/s`);
  if (!tags.length) return;

  const metaEl = document.createElement("div");
  metaEl.className = "msg-meta";
  for (const tag of tags) {
    const span = document.createElement("span");
    span.className = "meta-tag";
    span.textContent = tag;
    metaEl.appendChild(span);
  }
  bubbleEl.parentElement.appendChild(metaEl);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showSetupModal(title, message) {
  setupModalTitle.textContent = title || "ต้องตั้งค่าระบบก่อนใช้งาน";
  setupModalMessage.textContent = message || "กรุณาตรวจสอบ provider, model และ API key ในหน้า Settings";
  setupModal.classList.remove("hidden");
}

function closeSetupModal() {
  setupModal.classList.add("hidden");
}

function parseSetupError(detail) {
  if (detail && typeof detail === "object") {
    return {
      title: detail.title || "ตั้งค่าระบบไม่สมบูรณ์",
      message: detail.message || "กรุณาตรวจสอบ provider, model และ API key ในหน้า Settings",
      canOpenSettings: detail.action === "settings" || detail.code,
    };
  }
  if (typeof detail === "string") {
    return { title: "เกิดข้อผิดพลาด", message: detail, canOpenSettings: false };
  }
  return null;
}

async function fetchSessions() {
  const res = await fetch("/api/sessions");
  sessions = await res.json();
}

async function createSession() {
  const res = await fetch("/api/sessions", { method: "POST" });
  const session = await res.json();
  sessions.unshift(session);
  return session;
}

async function selectSession(sessionId) {
  currentSessionId = sessionId;
  renderSessionList();
  messagesEl.innerHTML = "";

  const res = await fetch(`/api/sessions/${sessionId}`);
  if (!res.ok) return;
  const detail = await res.json();

  setEmptyState(detail.messages.length === 0);

  for (const msg of detail.messages) {
    const bubble = addBubble(msg.role, msg.content, { markdown: msg.role === "assistant" });
    if (msg.role === "assistant") attachMeta(bubble, msg);
  }
}

async function init() {
  if (localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1") {
    sidebarEl.classList.add("collapsed");
  }

  checkSetupStatus();

  await fetchSessions();
  if (sessions.length === 0) {
    const session = await createSession();
    await selectSession(session.id);
  } else {
    renderSessionList();
    await selectSession(sessions[0].id);
  }
}

newChatBtn.addEventListener("click", async () => {
  const session = await createSession();
  renderSessionList();
  await selectSession(session.id);
});

sidebarToggleBtn.addEventListener("click", () => {
  const collapsed = sidebarEl.classList.toggle("collapsed");
  localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
});

searchInput.addEventListener("input", renderSessionList);

for (const chip of suggestionChipsEl.querySelectorAll(".chip")) {
  chip.addEventListener("click", () => {
    chatInput.value = chip.dataset.text || "";
    autoResize();
    chatInput.focus();
  });
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = chatInput.value.trim();
  if (!question || !currentSessionId) return;

  chatInput.value = "";
  autoResize();
  setEmptyState(false);
  addBubble("user", question);
  const pendingBubble = addBubble("assistant", "กำลังคิด...", { pending: true });

  const res = await fetch(`/api/sessions/${currentSessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  const sessionIndex = sessions.findIndex((s) => s.id === currentSessionId);

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const setupError = parseSetupError(err.detail);
    if (setupError?.canOpenSettings) {
      pendingBubble.textContent = setupError.message;
      showSetupModal(setupError.title, setupError.message);
    } else {
      pendingBubble.textContent = "เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง";
    }
    pendingBubble.classList.remove("pending");
    return;
  }

  const data = await res.json();
  pendingBubble.classList.remove("pending");
  pendingBubble.innerHTML = renderMarkdown(data.content);
  attachMeta(pendingBubble, data);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  if (sessionIndex !== -1 && sessions[sessionIndex].message_count === 0) {
    sessions[sessionIndex].title = question.slice(0, 40) + (question.length > 40 ? "…" : "");
  }
  if (sessionIndex !== -1) sessions[sessionIndex].message_count += 2;
  renderSessionList();
});

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

chatInput.addEventListener("input", autoResize);

function autoResize() {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + "px";
}

emojiBtn.addEventListener("click", () => {
  emojiPanel.classList.toggle("hidden");
});

setupModalCloseBtn.addEventListener("click", closeSetupModal);
setupModalDismissBtn.addEventListener("click", closeSetupModal);

document.addEventListener("click", (e) => {
  if (!emojiPanel.contains(e.target) && e.target !== emojiBtn) {
    emojiPanel.classList.add("hidden");
  }
  if (e.target === setupModal) {
    closeSetupModal();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeSetupModal();
  }
});

for (const emoji of EMOJIS) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = emoji;
  btn.addEventListener("click", () => {
    insertAtCursor(chatInput, emoji);
    emojiPanel.classList.add("hidden");
    chatInput.focus();
  });
  emojiPanel.appendChild(btn);
}

function insertAtCursor(textarea, text) {
  const start = textarea.selectionStart ?? textarea.value.length;
  const end = textarea.selectionEnd ?? textarea.value.length;
  textarea.value = textarea.value.slice(0, start) + text + textarea.value.slice(end);
  textarea.selectionStart = textarea.selectionEnd = start + text.length;
  autoResize();
}

async function checkSetupStatus() {
  try {
    const res = await fetch("/api/setup-status");
    if (!res.ok) return;
    const data = await res.json();
    if (!data.ok) {
      showSetupModal(data.title, data.message);
    }
  } catch (e) {
    // Setup status is helpful but should not block chat page rendering.
  }
}

init();
