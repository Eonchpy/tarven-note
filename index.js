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
    description: "Store entities and relationships to knowledge graph.",
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
      entity_id: { type: "string", description: "子图中心实体 ID" },
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
          if (!entityId) {
            return JSON.stringify({ success: false, error: "entity_id required" });
          }
          const depth = params.depth ?? 2;
          url += `/subgraph?entity_id=${encodeURIComponent(entityId)}&depth=${depth}`;
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
  registerTarvenNoteTools();
  console.log("tarven-note tools registered");
});
