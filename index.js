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
  });
}

function registerTarvenNoteTools() {
  if (!globalThis.SillyTavern?.registerToolFunction) {
    console.warn("SillyTavern tool API not available");
    return;
  }

  if (!enableTools) {
    console.log("tarven-note tools disabled");
    return;
  }

  globalThis.SillyTavern.registerToolFunction({
    name: "tarven_create_campaign",
    description: "创建新的 TRPG 战役",
    parameters: {
      type: "object",
      properties: {
        name: { type: "string", description: "战役名称" },
        system: { type: "string", description: "规则系统 (COC7, DND5e, Cyberpunk等)" },
        description: { type: "string", description: "战役描述" },
        metadata: { type: "object", description: "元数据" }
      },
      required: ["name", "system"]
    },
    handler: async (params) => {
      try {
        const response = await fetch(`${backendUrl}/api/campaigns`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params)
        });
        const data = await response.json();
        currentCampaignId = data.campaign_id;
        return {
          success: true,
          campaign_id: data.campaign_id,
          message: `战役 \"${params.name}\" 创建成功`
        };
      } catch (error) {
        return { success: false, error: error.message };
      }
    }
  });

  globalThis.SillyTavern.registerToolFunction({
    name: "tarven_store_entities",
    description: "存储实体和关系到知识图谱",
    parameters: {
      type: "object",
      properties: {
        entities: {
          type: "array",
          description: "实体列表",
          items: {
            type: "object",
            properties: {
              type: { type: "string" },
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
              type: { type: "string" },
              properties: { type: "object" }
            }
          }
        }
      },
      required: ["entities", "relationships"]
    },
    handler: async (params) => {
      if (!currentCampaignId) {
        return { success: false, error: "No active campaign" };
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
        return { success: true, data };
      } catch (error) {
        return { success: false, error: error.message };
      }
    }
  });

  globalThis.SillyTavern.registerToolFunction({
    name: "tarven_query",
    description: "查询知识图谱中的实体、关系或路径",
    parameters: {
      type: "object",
      properties: {
        query_type: {
          type: "string",
          enum: ["entity", "relationship"],
          description: "查询类型：entity(实体)、relationship(关系)"
        },
        entity_name: { type: "string", description: "实体名称" },
        entity_type: { type: "string", description: "实体类型过滤" },
        from_entity_id: { type: "string", description: "关系起点实体 ID" },
        to_entity_id: { type: "string", description: "关系终点实体 ID" },
        relationship_type: { type: "string", description: "关系类型过滤" }
      },
      required: ["query_type"]
    },
    handler: async (params) => {
      if (!currentCampaignId) {
        return { success: false, error: "No active campaign" };
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
        const response = await fetch(url);
        const data = await response.json();
        return { success: true, data };
      } catch (error) {
        return { success: false, error: error.message };
      }
    }
  });
}

jQuery(async () => {
  loadSettings();
  await setupSettingsUI();
  registerTarvenNoteTools();
  console.log("tarven-note tools registered");
});
