import { renderExtensionTemplateAsync } from '../../../extensions.js';

const MODULE_NAME = "tarven-note";
const TEMPLATE_PATH = "third-party/tarven-note";

const STORAGE_KEYS = {
  backendUrl: "tarven_note_backend_url",
  enableTools: "tarven_note_enable_tools"
};

let backendUrl = "";  // 动态设置
let enableTools = true;
let currentCampaignId = null;
let currentCampaignName = null;

function getDefaultBackendUrl() {
  // tarven-note 后端固定在 8001 端口
  if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
    // 局域网访问：使用同一 IP，但端口改为 8001
    return `http://${window.location.hostname}:8001`;
  }
  return "http://localhost:8001";
}

function loadSettings() {
  const storedUrl = localStorage.getItem(STORAGE_KEYS.backendUrl);
  const storedEnable = localStorage.getItem(STORAGE_KEYS.enableTools);
  if (storedUrl) {
    backendUrl = storedUrl;
  } else {
    backendUrl = getDefaultBackendUrl();
  }
  if (storedEnable !== null) {
    enableTools = storedEnable === "true";
  }
}

function saveSettings() {
  localStorage.setItem(STORAGE_KEYS.backendUrl, backendUrl);
  localStorage.setItem(STORAGE_KEYS.enableTools, String(enableTools));
}

let visLoaded = false;

async function loadVisJs() {
  if (visLoaded) return;
  return new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/vis-network@9.1.9/dist/dist/vis-network.min.css";
    document.head.appendChild(link);

    const script = document.createElement("script");
    script.src = "https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js";
    script.onload = () => {
      visLoaded = true;
      resolve();
    };
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

function createGraphModal() {
  const existing = document.getElementById("tarven_graph_modal");
  if (existing) return existing;

  const modal = document.createElement("div");
  modal.id = "tarven_graph_modal";
  modal.innerHTML = `
    <div class="tarven-graph-overlay"></div>
    <div class="tarven-graph-container">
      <div class="tarven-graph-header">
        <div class="tarven-graph-title">
          <span>知识图谱</span>
          <span id="tarven_campaign_name" class="tarven-campaign-name"></span>
          <button id="tarven_switch_campaign" class="menu_button">切换战役</button>
        </div>
        <button id="tarven_graph_close" class="menu_button">×</button>
      </div>
      <div class="tarven-graph-controls">
        <input id="tarven_graph_search" type="text" placeholder="输入实体名称搜索..." class="text_pole">
        <button id="tarven_graph_search_btn" class="menu_button">搜索</button>
        <button id="tarven_graph_full_btn" class="menu_button">全图</button>
      </div>
      <div id="tarven_graph_canvas"></div>
      <div id="tarven_graph_side_panel" class="tarven-graph-side-panel">
        <div class="tarven-graph-side-panel-header">
          <span>实体详情</span>
          <button id="tarven_side_panel_close" class="menu_button">×</button>
        </div>
        <div id="tarven_side_panel_content" class="tarven-graph-side-panel-content"></div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  addGraphStyles();
  return modal;
}

function addGraphStyles() {
  if (document.getElementById("tarven_graph_styles")) return;
  const style = document.createElement("style");
  style.id = "tarven_graph_styles";
  style.textContent = `
    #tarven_graph_modal { display: none; }
    #tarven_graph_modal.active { display: block; }
    .tarven-graph-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.7); z-index: 9998;
    }
    .tarven-graph-container {
      position: fixed; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      width: 80vw; height: 80vh;
      background: var(--SmartThemeBlurTintColor, #1a1a1a);
      border-radius: 10px; z-index: 9999;
      display: flex; flex-direction: column;
      overflow: hidden;
    }
    .tarven-graph-header {
      display: flex; justify-content: space-between; align-items: center;
      padding: 10px 15px; border-bottom: 1px solid #444;
    }
    .tarven-graph-title {
      display: flex; flex-direction: row; align-items: center; gap: 10px;
    }
    .tarven-graph-title > span:first-child { font-size: 16px; font-weight: bold; }
    .tarven-campaign-name {
      font-size: 14px; font-weight: normal; color: #aaa;
    }
    .tarven-graph-controls {
      display: flex; flex-direction: row; gap: 10px; padding: 10px 15px;
    }
    .tarven-graph-controls input { flex: 1; }
    #tarven_graph_modal .menu_button {
      display: inline-flex !important;
      flex-direction: row !important;
      align-items: center !important;
      white-space: nowrap !important;
      writing-mode: horizontal-tb !important;
    }
    #tarven_graph_canvas {
      flex: 1; min-height: 0;
    }
    .tarven-graph-side-panel {
      position: absolute;
      top: 0;
      right: -350px;
      width: 350px;
      height: 100%;
      background: var(--SmartThemeBlurTintColor, #1a1a1a);
      border-left: 1px solid #444;
      transition: right 0.3s ease;
      z-index: 10;
      display: flex;
      flex-direction: column;
    }
    .tarven-graph-side-panel.active {
      right: 0;
    }
    .tarven-graph-side-panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 15px;
      border-bottom: 1px solid #444;
      font-weight: bold;
    }
    .tarven-graph-side-panel-content {
      flex: 1;
      overflow-y: auto;
      padding: 15px;
      font-size: 13px;
    }
    .tarven-campaign-selector {
      position: fixed;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      background: var(--SmartThemeBlurTintColor, #1a1a1a);
      border-radius: 10px;
      padding: 20px;
      z-index: 10001;
      min-width: 280px;
      max-width: 90vw;
      max-height: 80vh;
      overflow-y: auto;
    }
    .tarven-campaign-selector-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.7);
      z-index: 10000;
    }
    .tarven-campaign-selector h3 {
      margin: 0 0 15px 0;
      font-size: 16px;
    }
    .tarven-campaign-item {
      padding: 12px 15px;
      margin: 8px 0;
      background: rgba(255,255,255,0.1);
      border-radius: 5px;
      cursor: pointer;
      transition: background 0.2s;
    }
    .tarven-campaign-item:hover {
      background: rgba(255,255,255,0.2);
    }
    .tarven-campaign-item-name {
      font-weight: bold;
      margin-bottom: 4px;
    }
    .tarven-campaign-item-date {
      font-size: 11px;
      color: #888;
    }
    .tarven-entity-name {
      font-size: 16px;
      font-weight: bold;
      margin-bottom: 10px;
      color: #fff;
    }
    .tarven-entity-type {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 3px;
      font-size: 11px;
      margin-bottom: 15px;
    }
    .tarven-property-group {
      margin-bottom: 15px;
    }
    .tarven-property-label {
      color: #888;
      font-size: 11px;
      text-transform: uppercase;
      margin-bottom: 5px;
    }
    .tarven-property-value {
      color: #ddd;
      margin-bottom: 8px;
    }
    .tarven-property-list {
      list-style: none;
      padding-left: 0;
    }
    .tarven-property-list li {
      padding: 4px 0;
      color: #ddd;
    }
    .tarven-property-list li:before {
      content: "• ";
      color: #666;
      margin-right: 5px;
    }
    @media (max-width: 768px) {
      .tarven-graph-container {
        position: fixed;
        top: 5vh;
        left: 2.5vw;
        transform: none;
        width: 95vw;
        height: 90vh;
        border-radius: 5px;
      }
      .tarven-campaign-selector {
        position: fixed;
        top: 10vh;
        left: 5vw;
        transform: none;
        width: 90vw;
        max-height: 80vh;
        padding: 15px;
      }
      .tarven-graph-side-panel {
        width: 100%;
        right: -100%;
      }
      .tarven-graph-side-panel.active {
        right: 0;
      }
      .tarven-graph-header {
        flex-wrap: wrap; gap: 5px;
        padding: 8px 10px;
      }
      .tarven-graph-title {
        flex-wrap: wrap; gap: 5px;
        width: 100%;
      }
      .tarven-graph-title > span:first-child { font-size: 14px; }
      .tarven-campaign-name { font-size: 12px; }
      .tarven-graph-controls {
        flex-wrap: wrap; gap: 5px;
        padding: 8px 10px;
      }
      .tarven-graph-controls input {
        flex: 1 1 100%; min-width: 0;
      }
      .tarven-graph-info {
        max-height: 80px; font-size: 12px;
        padding: 8px 10px;
      }
    }
  `;
  document.head.appendChild(style);
}

const NODE_COLORS = {
  Character: "#e74c3c",
  Location: "#3498db",
  Event: "#9b59b6",
  Clue: "#f39c12",
  Item: "#2ecc71",
  Organization: "#1abc9c",
  Skill: "#e91e63",
  Unknown: "#95a5a6"
};

async function fetchSubgraph(entityName, depth = 2) {
  if (!currentCampaignId) return null;
  const url = `${backendUrl}/api/campaigns/${currentCampaignId}/subgraph?name=${encodeURIComponent(entityName)}&depth=${depth}`;
  const response = await fetch(url);
  return response.json();
}

async function fetchEntityDetails(entityId) {
  if (!currentCampaignId) return null;
  const url = `${backendUrl}/api/campaigns/${currentCampaignId}/entities/${entityId}`;
  const response = await fetch(url);
  if (!response.ok) return null;
  return response.json();
}

async function fetchAllEntities() {
  if (!currentCampaignId) return [];
  const url = `${backendUrl}/api/campaigns/${currentCampaignId}/entities`;
  const response = await fetch(url);
  return response.json();
}

let networkInstance = null;

function formatValue(value, depth = 0) {
  if (value === null || value === undefined) {
    return '';
  }
  if (Array.isArray(value)) {
    // 数组中的元素也可能是对象
    return value.map(item => {
      if (typeof item === 'object' && item !== null) {
        return formatValue(item, depth + 1);
      }
      return item;
    }).join(', ');
  }
  if (typeof value === 'object') {
    const indent = depth * 15;
    let html = `<div style="margin-left: ${indent}px;">`;
    for (const [k, v] of Object.entries(value)) {
      const formattedV = formatValue(v, depth + 1);
      html += `<div style="margin: 3px 0;"><span style="color: #888;">${k}:</span> ${formattedV}</div>`;
    }
    html += '</div>';
    return html;
  }
  return value;
}

function formatEntityDetails(node) {
  const props = node._data.properties || {};
  const typeColor = NODE_COLORS[node._data.type] || NODE_COLORS.Unknown;

  let html = `
    <div class="tarven-entity-name">${node.label}</div>
    <div class="tarven-entity-type" style="background-color: ${typeColor};">${node._data.type}</div>
  `;

  // List fields that should be displayed as lists
  const listFields = ['alias', 'used_name', 'note'];

  // Separate list fields from regular fields
  const regularProps = {};
  const listProps = {};

  for (const [key, value] of Object.entries(props)) {
    if (listFields.includes(key)) {
      listProps[key] = value;
    } else {
      regularProps[key] = value;
    }
  }

  // Display regular properties
  if (Object.keys(regularProps).length > 0) {
    html += '<div class="tarven-property-group">';
    html += '<div class="tarven-property-label">属性</div>';
    for (const [key, value] of Object.entries(regularProps)) {
      html += `<div class="tarven-property-value"><strong>${key}:</strong> ${formatValue(value)}</div>`;
    }
    html += '</div>';
  }

  // Display list properties
  for (const [key, value] of Object.entries(listProps)) {
    html += '<div class="tarven-property-group">';
    html += `<div class="tarven-property-label">${key}</div>`;

    if (Array.isArray(value)) {
      html += '<ul class="tarven-property-list">';
      value.forEach(item => {
        html += `<li>${item}</li>`;
      });
      html += '</ul>';
    } else {
      html += `<div class="tarven-property-value">${value}</div>`;
    }
    html += '</div>';
  }

  return html;
}

function formatRelationshipDetails(edge) {
  const props = edge._data.properties || {};

  let html = `
    <div class="tarven-entity-name">关系: ${edge.label}</div>
  `;

  if (Object.keys(props).length > 0) {
    html += '<div class="tarven-property-group">';
    html += '<div class="tarven-property-label">属性</div>';
    for (const [key, value] of Object.entries(props)) {
      html += `<div class="tarven-property-value"><strong>${key}:</strong> ${value}</div>`;
    }
    html += '</div>';
  }

  return html;
}

function renderGraph(data, container) {
  console.log("renderGraph called, container:", container);
  // 清理旧实例和DOM
  if (networkInstance) {
    networkInstance.destroy();
    networkInstance = null;
  }
  container.innerHTML = "";

  // 去重节点
  const seenNodeIds = new Set();
  const uniqueNodes = data.nodes.filter(n => {
    if (seenNodeIds.has(n.id)) return false;
    seenNodeIds.add(n.id);
    return true;
  });

  // 去重边
  const seenEdgeIds = new Set();
  const uniqueEdges = data.edges.filter(e => {
    if (seenEdgeIds.has(e.id)) return false;
    seenEdgeIds.add(e.id);
    return true;
  });

  console.log("Creating nodes DataSet...");
  const nodes = new vis.DataSet(
    uniqueNodes.map(n => ({
      id: n.id,
      label: n.label,
      title: `${n.type}: ${n.label}`,
      color: NODE_COLORS[n.type] || NODE_COLORS.Unknown,
      _data: n
    }))
  );
  console.log("Nodes created:", nodes.length);

  console.log("Creating edges DataSet...");
  const edges = new vis.DataSet(
    uniqueEdges.map(e => ({
      id: e.id,
      from: e.from_id,
      to: e.to_id,
      label: e.type,
      arrows: "to",
      _data: e
    }))
  );
  console.log("Edges created:", edges.length);

  const options = {
    nodes: {
      shape: "dot",
      size: 20,
      font: { size: 14, color: "#fff" }
    },
    edges: {
      font: { size: 11, color: "#aaa", strokeWidth: 0 },
      color: { color: "#666", highlight: "#fff" }
    },
    physics: {
      stabilization: { iterations: 100 }
    }
  };

  if (networkInstance) {
    networkInstance.destroy();
  }
  networkInstance = new vis.Network(container, { nodes, edges }, options);

  networkInstance.on("click", async (params) => {
    const sidePanel = document.getElementById("tarven_graph_side_panel");
    const sidePanelContent = document.getElementById("tarven_side_panel_content");

    if (params.nodes.length > 0) {
      const node = nodes.get(params.nodes[0]);
      sidePanelContent.innerHTML = '<div style="padding: 20px; color: #888;">加载中...</div>';
      sidePanel.classList.add("active");

      // 从API获取完整实体详情
      const entityId = node._data.entity_id || node._data.id || node.id;
      const entityDetails = await fetchEntityDetails(entityId);
      if (entityDetails) {
        node._data.properties = entityDetails.properties || {};
      }
      sidePanelContent.innerHTML = formatEntityDetails(node);
    } else if (params.edges.length > 0) {
      const edge = edges.get(params.edges[0]);
      sidePanelContent.innerHTML = formatRelationshipDetails(edge);
      sidePanel.classList.add("active");
    } else {
      sidePanel.classList.remove("active");
    }
  });
}

async function fetchCampaigns() {
  const url = `${backendUrl}/api/campaigns`;
  console.log("fetchCampaigns: url=", url);
  try {
    const response = await fetch(url);
    console.log("fetchCampaigns: status=", response.status);
    if (!response.ok) {
      const text = await response.text();
      console.error("fetchCampaigns: error response=", text);
      throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
    }
    return response.json();
  } catch (error) {
    console.error("fetchCampaigns: fetch error=", error);
    throw error;
  }
}

async function selectCampaign() {
  try {
    console.log("selectCampaign: fetching campaigns...");
    const campaigns = await fetchCampaigns();
    console.log("selectCampaign: campaigns=", campaigns);

    if (!campaigns || campaigns.length === 0) {
      alert("暂无战役，请先通过对话创建战役");
      return false;
    }

    return new Promise((resolve) => {
      // 创建选择弹窗
      const overlay = document.createElement("div");
      overlay.className = "tarven-campaign-selector-overlay";

      const selector = document.createElement("div");
      selector.className = "tarven-campaign-selector";
      selector.innerHTML = `<h3>选择战役</h3>`;

      campaigns.forEach((c, i) => {
        const date = c.created_at ? new Date(c.created_at).toLocaleString() : "";
        const item = document.createElement("div");
        item.className = "tarven-campaign-item";
        item.innerHTML = `
          <div class="tarven-campaign-item-name">${c.name}</div>
          <div class="tarven-campaign-item-date">${date}</div>
        `;
        item.onclick = () => {
          currentCampaignId = c.campaign_id;
          currentCampaignName = c.name;
          cleanup();
          resolve(true);
        };
        selector.appendChild(item);
      });

      const cleanup = () => {
        overlay.remove();
        selector.remove();
      };

      overlay.onclick = () => {
        cleanup();
        resolve(false);
      };

      document.body.appendChild(overlay);
      document.body.appendChild(selector);
      console.log("selectCampaign: modal created");
    });
  } catch (error) {
    console.error("selectCampaign error:", error);
    alert("获取战役列表失败: " + error.message);
    return false;
  }
}

async function openGraphModal() {
  // 确保样式已加载
  addGraphStyles();

  // 如果没有当前战役，尝试获取战役列表让用户选择
  if (!currentCampaignId) {
    const selected = await selectCampaign();
    if (!selected) return;
  }

  await loadVisJs();
  const modal = createGraphModal();
  modal.classList.add("active");

  // 显示当前战役名称
  const campaignNameSpan = document.getElementById("tarven_campaign_name");
  if (campaignNameSpan && currentCampaignName) {
    campaignNameSpan.textContent = `- ${currentCampaignName}`;
  }

  const canvas = document.getElementById("tarven_graph_canvas");
  const searchInput = document.getElementById("tarven_graph_search");
  const searchBtn = document.getElementById("tarven_graph_search_btn");
  const fullBtn = document.getElementById("tarven_graph_full_btn");
  const closeBtn = document.getElementById("tarven_graph_close");
  const switchBtn = document.getElementById("tarven_switch_campaign");
  const overlay = modal.querySelector(".tarven-graph-overlay");

  const closeModal = () => modal.classList.remove("active");
  closeBtn.onclick = closeModal;
  overlay.onclick = closeModal;

  // 侧边面板关闭按钮
  const sidePanelCloseBtn = document.getElementById("tarven_side_panel_close");
  if (sidePanelCloseBtn) {
    sidePanelCloseBtn.onclick = (e) => {
      e.stopPropagation();
      const sidePanel = document.getElementById("tarven_graph_side_panel");
      sidePanel.classList.remove("active");
    };
  }

  // 切换战役
  switchBtn.onclick = async () => {
    const selected = await selectCampaign();
    if (selected) {
      campaignNameSpan.textContent = `- ${currentCampaignName}`;
      fullBtn.click();
    }
  };

  searchBtn.onclick = async () => {
    const name = searchInput.value.trim();
    if (!name) return;
    console.log("Searching for:", name);
    const data = await fetchSubgraph(name, 2);
    console.log("Subgraph data:", data);
    if (data && data.nodes?.length > 0) {
      console.log("Rendering graph with", data.nodes.length, "nodes and", data.edges?.length, "edges");
      renderGraph(data, canvas);
    } else {
      alert("未找到该实体");
    }
  };

  fullBtn.onclick = async () => {
    const entities = await fetchAllEntities();
    if (entities.length === 0) {
      alert("暂无数据");
      return;
    }
    const data = await fetchSubgraph(entities[0].name, 4);
    if (data) renderGraph(data, canvas);
  };

  fullBtn.click();
}

async function setupSettingsUI() {
  const settingsHtml = await renderExtensionTemplateAsync(TEMPLATE_PATH, "settings");
  const settingsContainer = document.getElementById("extensions_settings2");
  if (!settingsContainer) {
    return;
  }

  $(settingsContainer).append(settingsHtml);

  const urlInput = document.getElementById("tarven_backend_url");
  const enableToggle = document.getElementById("tarven_enable_tools");
  const saveButton = document.getElementById("tarven_save_settings");
  if (!urlInput || !enableToggle || !saveButton) {
    return;
  }

  urlInput.value = backendUrl;
  enableToggle.checked = enableTools;

  saveButton.addEventListener("click", () => {
    backendUrl = urlInput.value.trim() || "http://localhost:8000";
    enableTools = enableToggle.checked;
    saveSettings();
    registerTarvenNoteTools();
  });
}

async function setupExtensionMenu() {
  const buttonHtml = await renderExtensionTemplateAsync(TEMPLATE_PATH, "button");
  const extensionsMenu = document.getElementById("extensionsMenu");
  if (!extensionsMenu) {
    return;
  }

  $(extensionsMenu).append(buttonHtml);

  const viewGraphBtn = document.getElementById("tarven_view_graph_btn");
  if (viewGraphBtn) {
    viewGraphBtn.addEventListener("click", openGraphModal);
  }
}

function registerTarvenNoteTools() {
  const context = globalThis.SillyTavern?.getContext?.();
  const registerFunctionTool = context?.registerFunctionTool;
  const unregisterFunctionTool = context?.unregisterFunctionTool;
  if (!registerFunctionTool || !unregisterFunctionTool) {
    console.warn("SillyTavern function tool API not available");
    return;
  }

  const toolNames = [
    "tarven_create_campaign",
    "tarven_delete_campaign",
    "tarven_store_entities",
    "tarven_query"
  ];
  toolNames.forEach((name) => unregisterFunctionTool(name));

  if (!enableTools) {
    console.log("tarven-note tools disabled");
    return;
  }

  const createCampaignSchema = Object.freeze({
    $schema: "http://json-schema.org/draft-04/schema#",
    type: "object",
    properties: {
      name: { type: "string", description: "战役名称" },
      system: { type: "string", description: "规则系统 (COC7, DND5e, Cyberpunk等)" },
      description: { type: "string", description: "战役描述" },
      metadata: { type: "object", description: "元数据" }
    },
    required: ["name", "system"]
  });

  registerFunctionTool({
    name: "tarven_create_campaign",
    displayName: "Tarven Create Campaign",
    description: "创建新的 TRPG 战役",
    parameters: createCampaignSchema,
    action: async (params) => {
      try {
        const response = await fetch(`${backendUrl}/api/campaigns`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params)
        });
        const data = await response.json();
        currentCampaignId = data.campaign_id;
        return JSON.stringify({
          success: true,
          campaign_id: data.campaign_id,
          message: `战役 \"${params.name}\" 创建成功`
        });
      } catch (error) {
        return JSON.stringify({ success: false, error: error.message });
      }
    },
    formatMessage: () => ""
  });

  const deleteCampaignSchema = Object.freeze({
    $schema: "http://json-schema.org/draft-04/schema#",
    type: "object",
    properties: {
      campaign_id: { type: "string", description: "要删除的战役ID" }
    },
    required: ["campaign_id"]
  });

  registerFunctionTool({
    name: "tarven_delete_campaign",
    displayName: "Tarven Delete Campaign",
    description: "Delete a campaign and all its entities/relationships. Use when campaign is finished or no longer needed.",
    parameters: deleteCampaignSchema,
    action: async (params) => {
      try {
        const response = await fetch(`${backendUrl}/api/campaigns/${params.campaign_id}`, {
          method: "DELETE"
        });
        if (!response.ok) {
          return JSON.stringify({ success: false, error: "Campaign not found" });
        }
        if (currentCampaignId === params.campaign_id) {
          currentCampaignId = null;
        }
        return JSON.stringify({ success: true, message: "战役已删除" });
      } catch (error) {
        return JSON.stringify({ success: false, error: error.message });
      }
    },
    formatMessage: () => ""
  });

  const storeEntitiesSchema = Object.freeze({
    $schema: "http://json-schema.org/draft-04/schema#",
    type: "object",
    properties: {
      entities: {
        type: "array",
        description: "实体列表",
        items: {
          type: "object",
          properties: {
            type: {
              type: "string",
              enum: ["Character", "Location", "Event", "Clue", "Item", "Organization", "Skill"],
              description: "Entity type - MUST use one of these exact values. Note: For character skills (技能值), use properties field (e.g., properties.skills = {斧头: 60}). Skill entity type is for creating independent skill nodes."
            },
            name: { type: "string" },
            properties: {
              type: "object",
              description: "实体属性，key已钉死，请严格按照定义的字段存储",
              properties: {
                // 通用字段
                description: { type: "string", description: "描述" },
                // 列表字段（追加而非覆盖）
                aliases: { type: "array", items: { type: "string" }, description: "别名列表" },
                used_names: { type: "array", items: { type: "string" }, description: "曾用名" },
                notes: { type: "array", items: { type: "string" }, description: "备注" },
                // Character字段
                occupation: { type: "string", description: "职业" },
                age: { type: "integer", description: "年龄" },
                gender: { type: "string", description: "性别" },
                appearance: { type: "string", description: "外貌" },
                personality: { type: "string", description: "性格" },
                background: { type: "string", description: "背景" },
                // Location字段
                location_type: { type: "string", description: "地点类型" },
                address: { type: "string", description: "地址" },
                // Item字段
                item_type: { type: "string", description: "物品类型" },
                rarity: { type: "string", description: "稀有度" },
                // Event字段
                event_time: { type: "string", description: "事件时间" },
                participants: { type: "array", items: { type: "string" }, description: "参与者" },
                // Organization字段
                org_type: { type: "string", description: "组织类型" },
                members: { type: "array", items: { type: "string" }, description: "成员" },
                // 规则系统属性
                attributes: {
                  type: "object",
                  description: "规则系统属性（COC/DND等）",
                  properties: {
                    stats: { type: "object", description: "基础属性 {STR:50, CON:60...}" },
                    skills: { type: "object", description: "技能值 {侦查:60, 图书馆使用:40...}" },
                    hp: { type: "integer", description: "生命值" },
                    mp: { type: "integer", description: "魔法值" },
                    san: { type: "integer", description: "理智值(COC)" },
                    luck: { type: "integer", description: "幸运值" },
                    level: { type: "integer", description: "等级(DND)" },
                    class: { type: "string", description: "职业(DND)" },
                    race: { type: "string", description: "种族" },
                    ext: { type: "object", description: "扩展字段" }
                  }
                }
              }
            },
            metadata: { type: "object" }
          }
        }
      },
      relationships: {
        type: "array",
        description: "关系列表",
        items: {
          type: "object",
          properties: {
            from_entity_name: { type: "string" },
            to_entity_name: { type: "string" },
            type: {
              type: "string",
              enum: ["KNOWS", "TRUSTS", "FEARS", "LOVES", "HATES", "LOCATED_AT", "WORKS_AT", "LIVES_AT", "PARTICIPATED_IN", "WITNESSED", "CAUSED", "OWNS", "USED", "FOUND", "BELONGS_TO", "CONNECTED_TO"],
              description: "Relationship type. Prefer English enum values for Neo4j label. Chinese types (接触, 知晓) will be stored in properties.type"
            },
            bidirectional: {
              type: "boolean",
              description: "是否双向关系。如果为true，会自动创建反向关系。例如'A和B是朋友'应设为true",
              default: false
            },
            reverse_type: {
              type: "string",
              enum: ["KNOWS", "TRUSTS", "FEARS", "LOVES", "HATES", "LOCATED_AT", "WORKS_AT", "LIVES_AT", "PARTICIPATED_IN", "WITNESSED", "CAUSED", "OWNS", "USED", "FOUND", "BELONGS_TO", "CONNECTED_TO"],
              description: "反向关系类型。仅当bidirectional=true时有效。如A憎恨B，B恐惧A，则type=HATES, reverse_type=FEARS。如果不填则默认与type相同"
            },
            properties: { type: "object" }
          }
        }
      }
    },
    required: ["entities", "relationships"]
  });

  registerFunctionTool({
    name: "tarven_store_entities",
    displayName: "Tarven Store Entities",
    description: "Store or update entities and relationships. Supports upsert - same entity/relationship will be updated. List fields (alias, used_name, note) append values; other fields overwrite.",
    parameters: storeEntitiesSchema,
    action: async (params) => {
      if (!currentCampaignId) {
        return JSON.stringify({ success: false, error: "No active campaign" });
      }
      try {
        const response = await fetch(
          `${backendUrl}/api/campaigns/${currentCampaignId}/ingest`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(params)
          }
        );
        const data = await response.json();
        return JSON.stringify({ success: true, data });
      } catch (error) {
        return JSON.stringify({ success: false, error: error.message });
      }
    },
    formatMessage: () => ""
  });

  const querySchema = Object.freeze({
    $schema: "http://json-schema.org/draft-04/schema#",
    type: "object",
    properties: {
      query_type: {
        type: "string",
        enum: ["entity", "relationship", "path", "subgraph"],
        description: "查询类型"
      },
      entity_name: { type: "string", description: "实体名称" },
      entity_type: { type: "string", description: "实体类型过滤" },
      from_entity_id: { type: "string", description: "关系起点实体 ID" },
      to_entity_id: { type: "string", description: "关系终点实体 ID" },
      relationship_type: { type: "string", description: "关系类型过滤" },
      from_name: { type: "string", description: "路径起点名称" },
      to_name: { type: "string", description: "路径终点名称" },
      max_hops: { type: "number", description: "最大跳数" },
      entity_id: { type: "string", description: "子图中心实体 ID (或用 entity_name)" },
      depth: { type: "number", description: "子图深度" },
      detail_level: {
        type: "string",
        enum: ["skeleton", "summary", "full"],
        description: "详情级别: skeleton(仅ID和名称), summary(含description), full(完整属性)"
      }
    },
    required: ["query_type"]
  });

  registerFunctionTool({
    name: "tarven_query",
    displayName: "Tarven Query",
    description: "Query knowledge graph. Types: entity (by name/type), relationship (by entity IDs), path (between two entities), subgraph (around one entity).",
    parameters: querySchema,
    action: async (params) => {
      if (!currentCampaignId) {
        return JSON.stringify({ success: false, error: "No active campaign" });
      }
      try {
        let url = `${backendUrl}/api/campaigns/${currentCampaignId}`;
        if (params.query_type === "entity") {
          url += `/entities?`;
          if (params.entity_name) {
            url += `name=${encodeURIComponent(params.entity_name)}&`;
          }
          if (params.entity_type) {
            url += `type=${encodeURIComponent(params.entity_type)}`;
          }
        }
        if (params.query_type === "relationship") {
          url += `/relationships?`;
          if (params.from_entity_id) {
            url += `from_entity_id=${encodeURIComponent(params.from_entity_id)}&`;
          }
          if (params.to_entity_id) {
            url += `to_entity_id=${encodeURIComponent(params.to_entity_id)}&`;
          }
          if (params.relationship_type) {
            url += `type=${encodeURIComponent(params.relationship_type)}`;
          }
        }
        if (params.query_type === "path") {
          const fromName = params.from_name ?? "";
          const toName = params.to_name ?? "";
          if (!fromName || !toName) {
            return JSON.stringify({ success: false, error: "from_name/to_name required" });
          }
          const maxHops = params.max_hops ?? 3;
          url += `/paths?from=${encodeURIComponent(fromName)}&to=${encodeURIComponent(toName)}&max_hops=${maxHops}`;
        }
        if (params.query_type === "subgraph") {
          const entityId = params.entity_id ?? "";
          const entityName = params.entity_name ?? "";
          if (!entityId && !entityName) {
            return JSON.stringify({ success: false, error: "entity_id or entity_name required" });
          }
          const depth = params.depth ?? 2;
          const detailLevel = params.detail_level ?? "skeleton";
          if (entityId) {
            url += `/subgraph?entity_id=${encodeURIComponent(entityId)}&depth=${depth}&detail_level=${detailLevel}`;
          } else {
            url += `/subgraph?name=${encodeURIComponent(entityName)}&depth=${depth}&detail_level=${detailLevel}`;
          }
        }
        const response = await fetch(url);
        const data = await response.json();
        return JSON.stringify({ success: true, data });
      } catch (error) {
        return JSON.stringify({ success: false, error: error.message });
      }
    },
    formatMessage: () => ""
  });
}

jQuery(async () => {
  loadSettings();
  await setupSettingsUI();
  await setupExtensionMenu();
  registerTarvenNoteTools();
  console.log("tarven-note tools registered");
});
