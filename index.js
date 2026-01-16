import { renderExtensionTemplateAsync } from '../../../extensions.js';

const MODULE_NAME = "tarven-note";
const TEMPLATE_PATH = "third-party/tarven-note";

const STORAGE_KEYS = {
  backendUrl: "tarven_note_backend_url",
  enableTools: "tarven_note_enable_tools"
};

let backendUrl = "http://localhost:8000";
let enableTools = true;
let currentCampaignId = null;
let currentCampaignName = null;

function loadSettings() {
  const storedUrl = localStorage.getItem(STORAGE_KEYS.backendUrl);
  const storedEnable = localStorage.getItem(STORAGE_KEYS.enableTools);
  if (storedUrl) {
    backendUrl = storedUrl;
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
      <div id="tarven_graph_info" class="tarven-graph-info"></div>
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
    #tarven_graph_canvas { flex: 1; min-height: 0; }
    .tarven-graph-info {
      padding: 10px 15px; border-top: 1px solid #444;
      max-height: 120px; overflow-y: auto; font-size: 13px;
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
  Unknown: "#95a5a6"
};

async function fetchSubgraph(entityName, depth = 2) {
  if (!currentCampaignId) return null;
  const url = `${backendUrl}/api/campaigns/${currentCampaignId}/subgraph?name=${encodeURIComponent(entityName)}&depth=${depth}`;
  const response = await fetch(url);
  return response.json();
}

async function fetchAllEntities() {
  if (!currentCampaignId) return [];
  const url = `${backendUrl}/api/campaigns/${currentCampaignId}/entities`;
  const response = await fetch(url);
  return response.json();
}

let networkInstance = null;

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

  networkInstance.on("click", (params) => {
    const infoDiv = document.getElementById("tarven_graph_info");
    if (params.nodes.length > 0) {
      const node = nodes.get(params.nodes[0]);
      const props = node._data.properties || {};
      infoDiv.innerHTML = `<b>${node._data.type}: ${node.label}</b><br>` +
        Object.entries(props).map(([k, v]) => `${k}: ${v}`).join("<br>");
    } else if (params.edges.length > 0) {
      const edge = edges.get(params.edges[0]);
      const props = edge._data.properties || {};
      infoDiv.innerHTML = `<b>关系: ${edge.label}</b><br>` +
        Object.entries(props).map(([k, v]) => `${k}: ${v}`).join("<br>");
    } else {
      infoDiv.innerHTML = "";
    }
  });
}

async function fetchCampaigns() {
  const url = `${backendUrl}/api/campaigns`;
  const response = await fetch(url);
  return response.json();
}

async function selectCampaign() {
  const campaigns = await fetchCampaigns();
  if (!campaigns || campaigns.length === 0) {
    alert("暂无战役，请先通过对话创建战役");
    return false;
  }
  const options = campaigns.map((c, i) => `${i + 1}. ${c.name}`).join("\n");
  const choice = prompt(`请选择战役:\n${options}\n\n输入序号:`);
  if (!choice) return false;
  const index = parseInt(choice) - 1;
  if (index >= 0 && index < campaigns.length) {
    currentCampaignId = campaigns[index].campaign_id;
    currentCampaignName = campaigns[index].name;
    return true;
  } else {
    alert("无效选择");
    return false;
  }
}

async function openGraphModal() {
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
              enum: ["Character", "Location", "Event", "Clue", "Item", "Organization"],
              description: "Entity type - MUST use one of these exact values"
            },
            name: { type: "string" },
            properties: { type: "object" },
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
    description: "Store or update entities and relationships. Supports upsert - same entity/relationship will be updated.",
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
      depth: { type: "number", description: "子图深度" }
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
          if (entityId) {
            url += `/subgraph?entity_id=${encodeURIComponent(entityId)}&depth=${depth}`;
          } else {
            url += `/subgraph?name=${encodeURIComponent(entityName)}&depth=${depth}`;
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
