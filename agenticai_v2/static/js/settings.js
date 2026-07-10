const PROVIDER_GUIDE_IMAGES = {
  openrouter: "how-to-get-openrouter-api-key.png",
  gemini: "how-to-get-gemini-api-key.png",
  openai: "how-to-get-openai-api-key.png",
  openai_compatible: null,
};

const providerSelect = document.getElementById("provider-select");
const modelInput = document.getElementById("model-input");
const apiKeyInput = document.getElementById("api-key-input");
const apiKeyBadgeEl = document.getElementById("api-key-badge");
const howToBtn = document.getElementById("how-to-get-key-btn");
const baseUrlField = document.getElementById("base-url-field");
const baseUrlInput = document.getElementById("base-url-input");
const saveBtn = document.getElementById("save-settings-btn");
const statusEl = document.getElementById("settings-status");
const mcpNameEl = document.getElementById("mcp-name");
const mcpUrlEl = document.getElementById("mcp-url");
const fetchToolsBtn = document.getElementById("fetch-tools-btn");
const toolListEl = document.getElementById("tool-list");
const apiKeyModal = document.getElementById("api-key-modal");
const modalTitle = document.getElementById("modal-title");
const modalImage = document.getElementById("modal-image");
const modalCloseBtn = document.getElementById("modal-close-btn");

let currentSettings = null;

function applyProviderView() {
  const provider = providerSelect.value;
  apiKeyInput.value = "";
  const info = currentSettings?.api_keys?.[provider];
  if (info && info.has_value) {
    apiKeyInput.placeholder = info.masked;
    apiKeyBadgeEl.textContent = "มีค่าอยู่แล้ว (จาก .env หรือที่บันทึกไว้) — พิมพ์ใหม่เพื่อเปลี่ยน ปล่อยว่างเพื่อคงค่าเดิม";
  } else {
    apiKeyInput.placeholder = "ยังไม่ได้ตั้งค่า";
    apiKeyBadgeEl.textContent = "";
  }

  baseUrlField.style.display = provider === "openai_compatible" ? "flex" : "none";
  if (provider === "openai_compatible") {
    baseUrlInput.value = currentSettings?.openai_compatible_base_url || "";
  }

  const guideImage = PROVIDER_GUIDE_IMAGES[provider];
  if (guideImage) {
    howToBtn.textContent = `📖 วิธีขอ API Key (${provider})`;
    howToBtn.style.display = "inline-flex";
  } else {
    howToBtn.style.display = "none";
  }
}

async function loadSettings() {
  const res = await fetch("/api/settings");
  currentSettings = await res.json();
  providerSelect.value = currentSettings.provider;
  modelInput.value = currentSettings.model;
  applyProviderView();
}

providerSelect.addEventListener("change", applyProviderView);

howToBtn.addEventListener("click", () => {
  const provider = providerSelect.value;
  const guideImage = PROVIDER_GUIDE_IMAGES[provider];
  if (!guideImage) return;
  modalTitle.textContent = `วิธีขอ API Key: ${provider}`;
  modalImage.src = `/assets/${guideImage}`;
  apiKeyModal.classList.remove("hidden");
});

function closeModal() {
  apiKeyModal.classList.add("hidden");
}

modalCloseBtn.addEventListener("click", closeModal);
apiKeyModal.addEventListener("click", (e) => {
  if (e.target === apiKeyModal) closeModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

saveBtn.addEventListener("click", async () => {
  statusEl.textContent = "กำลังบันทึก...";
  const body = {
    provider: providerSelect.value,
    model: modelInput.value.trim(),
  };
  if (apiKeyInput.value.trim()) body.api_key = apiKeyInput.value.trim();
  if (providerSelect.value === "openai_compatible" && baseUrlInput.value.trim()) {
    body.openai_compatible_base_url = baseUrlInput.value.trim();
  }

  const res = await fetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.ok) {
    statusEl.textContent = "";
    alert("บันทึกแล้ว ✓ ใช้ตั้งแต่ข้อความถัดไปทันที");
    window.location.href = "/";
  } else {
    const err = await res.json().catch(() => ({}));
    statusEl.textContent = "เกิดข้อผิดพลาด: " + (err.detail || res.statusText);
  }
});

fetchToolsBtn.addEventListener("click", async () => {
  toolListEl.textContent = "กำลังโหลด...";
  try {
    const res = await fetch("/api/mcp/tools");
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    mcpNameEl.textContent = "ชื่อ MCP: " + data.mcp_name;
    mcpUrlEl.textContent = "เชื่อมต่อกับ: " + data.mcp_url;
    toolListEl.innerHTML = "";
    for (const tool of data.tools) {
      const item = document.createElement("div");
      item.className = "tool-item";
      const name = document.createElement("div");
      name.className = "tool-name";
      name.textContent = tool.name;
      const desc = document.createElement("div");
      desc.className = "tool-desc";
      desc.textContent = tool.description.split("\n")[0];
      item.appendChild(name);
      item.appendChild(desc);
      toolListEl.appendChild(item);
    }
  } catch (e) {
    toolListEl.textContent = "ดึงรายการ tools ไม่สำเร็จ: " + e.message;
  }
});

loadSettings();
