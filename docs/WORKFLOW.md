# tarven-note 完整工作流程

## 场景说明

**用户操作**:
1. User 在 SillyTavern 中点击 "New Chat"
2. User 输入: "我想开启一个 COC7 的跑团，1920s 阿卡姆背景"
3. KP (LLM) 开始叙述，游戏正式开始

---

## 核心架构：Function Calling 模式

**关键发现**: SillyTavern 支持 Tool Calling（通过 `TOOL_CALLS_PERFORMED` 事件）

**架构模式**:
```
User → LLM (with registered tools) → Function Call → Extension Handler → tarven-note API
```

---

## Phase 1: Campaign 创建与初始化

### 1.1 用户创建新聊天

```
┌─────────────────────────────────────────────────────────────┐
│ User Action                                                  │
│                                                              │
│  1. 打开 SillyTavern                                         │
│  2. 点击 "New Chat"                                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ tarven-note Extension (自动触发)                                │
│                                                              │
│  1. 检测到新聊天创建事件                                     │
│  2. 弹出 Campaign 配置对话框                                 │
│     ┌──────────────────────────────────────┐               │
│     │ 创建新战役                            │               │
│     │                                       │               │
│     │ Campaign Name: [____________]         │               │
│     │ System: [COC7 ▼]                     │               │
│     │ Description: [____________]           │               │
│     │                                       │               │
│     │        [稍后创建]  [立即创建]         │               │
│     └──────────────────────────────────────┘               │
│                                                              │
│  3. 用户选择 "稍后创建"（延迟到第一条消息）                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Extension 状态                                               │
│                                                              │
│  - campaign_id: null (待创建)                                │
│  - 等待用户第一条消息                                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Extension 注册 Tool Functions

```
┌─────────────────────────────────────────────────────────────┐
│ tarven-note Extension 初始化                                    │
│                                                              │
│  注册以下 Tool Functions 给 LLM:                             │
│                                                              │
│  1. tarven_create_campaign(name, system, description)      │
│     - 创建新战役                                             │
│                                                              │
│  2. tarven_store_entities(entities, relationships)         │
│     - 存储实体和关系                                         │
│                                                              │
│  3. tarven_query(question, query_type)                     │
│     - 查询图谱信息                                           │
│                                                              │
│  这些函数会被 LLM 自动调用（Function Calling）              │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 2: 用户第一条消息 - Campaign 创建

### 2.1 用户输入战役信息

```
┌─────────────────────────────────────────────────────────────┐
│ SillyTavern UI                                               │
│                                                              │
│  User 输入: "我想开启一个 COC7 的跑团，1920s 阿卡姆背景"     │
│  点击发送                                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 消息发送到 LLM
                          ↓
```

### 2.2 LLM 处理 - 识别意图并调用工具

```
┌─────────────────────────────────────────────────────────────┐
│ LLM Service (Qwen3-next-80B MoE)                             │
│                                                              │
│  System Prompt:                                              │
│  "你是 COC7 KP，负责主持跑团游戏。                           │
│   你可以使用以下工具:                                        │
│   - tarven_create_campaign: 创建新战役                     │
│   - tarven_store_entities: 存储实体和关系                  │
│   - tarven_query: 查询信息"                                │
│                                                              │
│  User Message:                                               │
│  "我想开启一个 COC7 的跑团，1920s 阿卡姆背景"                │
│                                                              │
│  ─────────────────────────────────────────                  │
│                                                              │
│  LLM 分析:                                                   │
│  1. 识别意图: 用户想创建新战役                               │
│  2. 提取参数:                                                │
│     - system: "COC7"                                         │
│     - setting: "1920s 阿卡姆"                                │
│  3. 决定调用 tarven_create_campaign                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Function Call
                          ↓
```


### 2.3 Extension Handler 执行 - 创建 Campaign

```
┌─────────────────────────────────────────────────────────────┐
│ tarven-note Extension Handler                                   │
│                                                              │
│  Function: tarven_create_campaign                          │
│  Parameters: {                                               │
│    name: "阿卡姆调查",                                       │
│    system: "COC7",                                           │
│    description: "1920s 阿卡姆背景"                           │
│  }                                                           │
│                                                              │
│  执行:                                                       │
│  1. 调用 tarven-note Server API                                 │
│  2. 保存返回的 campaign_id                                   │
│  3. 返回成功状态给 LLM                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ POST /api/campaigns
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ tarven-note Server                                          │
│                                                             │
│  1. 生成 campaign_id (UUID)                                 │
│  2. Neo4j 操作:                                             │
│                                                             │
│     CREATE (:Campaign {                                     │
│       campaign_id: "xxx",                                   │
│       name: "阿卡姆调查",                                   │
│       system: "COC7",                                       │
│       description: "...",                                   │
│       status: "active"                                      │
│     })                                                      │
│                                                             │
│     空图谱: 0 个实体, 0 个关系                              │
│                                                             │
│  3. 返回: { campaign_id: "uuid-xxx", status: "created" }    │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Response
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Extension Handler                                            │
│                                                              │
│  1. 保存 campaign_id 到会话状态                              │
│  2. 返回成功给 LLM: { success: true, campaign_id: "xxx" }   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Tool Call Result
                          ↓
```

### 2.4 LLM 生成开场叙述

```
┌─────────────────────────────────────────────────────────────┐
│ LLM Service                                                  │
│                                                              │
│  收到 Tool Call 结果: { success: true }                      │
│                                                              │
│  生成开场叙述:                                               │
│  "1920年的阿卡姆市，秋风萧瑟。你是一名私家侦探，            │
│   最近接到了一个神秘的委托..."                               │
│                                                              │
│  同时调用 tarven_store_entities:                           │
│  {                                                           │
│    entities: [                                               │
│      {                                                       │
│        type: "Location",                                     │
│        name: "阿卡姆市",                                     │
│        properties: {                                         │
│          type: "city",                                       │
│          era: "1920s",                                       │
│          description: "新英格兰的神秘小城"                   │
│        }                                                     │
│      },                                                      │
│      {                                                       │
│        type: "Character",                                    │
│        name: "调查员",                                       │
│        properties: {                                         │
│          role: "PC",                                         │
│          occupation: "私家侦探",                             │
│          status: "alive"                                     │
│        }                                                     │
│      }                                                       │
│    ],                                                        │
│    relationships: [                                          │
│      {                                                       │
│        from: "调查员",                                       │
│        to: "阿卡姆市",                                       │
│        type: "LOCATED_AT"                                    │
│      }                                                       │
│    ]                                                         │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Function Call
                          ↓
```


### 2.5 Extension 存储实体到 GraphRAG

```
┌─────────────────────────────────────────────────────────────┐
│ Extension Handler: tarven_store_entities                   │
│                                                              │
│  1. 接收 entities 和 relationships                           │
│  2. 调用 tarven-note Server API                                 │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ POST /api/campaigns/{id}/extract
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ tarven-note Server                                          │
│                                                             │
│  Neo4j 操作:                                                │
│                                                             │
│  CREATE (:Location {                                        │
│    id: "loc_001",                                           │
│    name: "阿卡姆市",                                        │
│    type: "city",                                            │
│    campaign_id: "xxx"                                       │
│  })                                                         │
│                                                             │
│  CREATE (:Character {                                       │
│    id: "char_001",                                          │
│    name: "调查员",                                          │
│    role: "PC",                                              │
│    campaign_id: "xxx"                                       │
│  })                                                         │
│                                                             │
│  CREATE (char_001)-[:LOCATED_AT]->(loc_001)                 │
│                                                             │
│  图谱状态: 2 个实体, 1 个关系                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Response: { success: true }
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Extension Handler                                            │
│                                                              │
│  返回成功给 LLM                                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
```

### 2.6 用户看到开场叙述

```
┌─────────────────────────────────────────────────────────────┐
│ SillyTavern UI                                               │
│                                                              │
│  显示 KP 的开场叙述:                                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ KP:                                                  │   │
│  │                                                      │   │
│  │ 1920年的阿卡姆市，秋风萧瑟。你是一名私家侦探，      │   │
│  │ 最近接到了一个神秘的委托...                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  用户完全不知道后台发生了:                                   │
│  - Campaign 创建                                             │
│  - 实体提取                                                  │
│  - 图谱构建                                                  │
│                                                              │
│  一切都是透明的！                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 3: 持续游戏 - KP 叙述与实体提取

### 3.1 KP 继续叙述

```
┌─────────────────────────────────────────────────────────────┐
│ 游戏进行中...                                                │
│                                                              │
│  User: "我去图书馆调查"                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LLM Service                                                  │
│                                                              │
│  生成叙述:                                                   │
│  "你来到了阿卡姆市图书馆，管理员韦弗夫人正在整理书籍..."    │
│                                                              │
│  同时调用 tarven_store_entities:                           │
│  {                                                           │
│    entities: [                                               │
│      {                                                       │
│        type: "Location",                                     │
│        name: "阿卡姆市图书馆",                               │
│        properties: {                                         │
│          type: "building",                                   │
│          description: "阿卡姆市的公共图书馆"                 │
│        }                                                     │
│      },                                                      │
│      {                                                       │
│        type: "Character",                                    │
│        name: "韦弗夫人",                                     │
│        properties: {                                         │
│          role: "NPC",                                        │
│          occupation: "图书馆管理员",                         │
│          status: "alive"                                     │
│        }                                                     │
│      }                                                       │
│    ],                                                        │
│    relationships: [                                          │
│      {                                                       │
│        from: "韦弗夫人",                                     │
│        to: "阿卡姆市图书馆",                                 │
│        type: "WORKS_AT"                                      │
│      },                                                      │
│      {                                                       │
│        from: "调查员",                                       │
│        to: "阿卡姆市图书馆",                                 │
│        type: "LOCATED_AT"                                    │
│      }                                                       │
│    ]                                                         │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Function Call (后台自动执行)
                          ↓
```


### 3.2 图谱持续增长

```
┌─────────────────────────────────────────────────────────────┐
│ Neo4j 图谱状态（游戏进行中）                                 │
│                                                              │
│  实体数量: 4                                                 │
│  关系数量: 3                                                 │
│                                                              │
│  (调查员)-[:LOCATED_AT]->(阿卡姆市图书馆)                    │
│  (韦弗夫人)-[:WORKS_AT]->(阿卡姆市图书馆)                    │
│  (阿卡姆市图书馆)-[:IN_CAMPAIGN]->(Campaign)                 │
│                                                              │
│  图谱随着游戏自然生长！                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 4: 玩家查询 - 图谱检索

### 4.1 玩家提问

```
┌─────────────────────────────────────────────────────────────┐
│ SillyTavern UI                                               │
│                                                              │
│  User: "谁认识韦弗夫人？"                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LLM Service                                                  │
│                                                              │
│  识别意图: 这是一个关系查询                                  │
│                                                              │
│  调用 tarven_query:                                        │
│  {                                                           │
│    question: "谁认识韦弗夫人？",                             │
│    query_type: "graph"                                       │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Function Call
                          ↓
```

### 4.2 Extension 执行查询

```
┌─────────────────────────────────────────────────────────────┐
│ Extension Handler: tarven_query                            │
│                                                              │
│  调用 tarven-note Server API                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ POST /api/campaigns/{id}/query
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ tarven-note Server                                              │
│                                                              │
│  1. LLM 生成 Cypher 查询:                                    │
│     MATCH (c:Character)-[r:KNOWS]->(w:Character)             │
│     WHERE w.name = "韦弗夫人"                                │
│       AND c.campaign_id = $campaign_id                       │
│     RETURN c.name, r.type                                    │
│                                                              │
│  2. 执行 Neo4j 查询                                          │
│                                                              │
│  3. 返回结果:                                                │
│     {                                                        │
│       results: [                                             │
│         { name: "调查员", relationship: "KNOWS" }            │
│       ],                                                     │
│       reasoning: "根据图谱，调查员认识韦弗夫人"              │
│     }                                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Response
                          ↓
```

### 4.3 LLM 生成回答

```
┌─────────────────────────────────────────────────────────────┐
│ LLM Service                                                  │
│                                                              │
│  收到查询结果: { results: [...] }                            │
│                                                              │
│  生成自然语言回答:                                           │
│  "根据你掌握的信息，你（调查员）认识韦弗夫人。              │
│   她是阿卡姆市图书馆的管理员。"                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ SillyTavern UI                                               │
│                                                              │
│  显示 KP 的回答（基于图谱事实，不会幻觉）                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 完整流程总结

### 关键技术点

**1. Function Calling 模式**
```javascript
// Extension 注册的工具函数
const tools = [
  {
    name: "tarven_create_campaign",
    description: "创建新的 TRPG 战役",
    parameters: { name, system, description }
  },
  {
    name: "tarven_store_entities",
    description: "存储实体和关系到知识图谱",
    parameters: { entities, relationships }
  },
  {
    name: "tarven_query",
    description: "查询知识图谱中的信息",
    parameters: { question, query_type }
  }
];

// LLM 自动调用这些工具
// Extension Handler 自动执行
// 用户完全无感知
```

**2. 数据流向**

```
User Input
    ↓
LLM (识别意图)
    ↓
Function Call (自动)
    ↓
Extension Handler (执行)
    ↓
tarven-note Server (存储/查询)
    ↓
Neo4j (持久化)
    ↓
Response (返回给 LLM)
    ↓
LLM (生成自然语言)
    ↓
User Output (显示给用户)
```

**3. 用户体验**

- ✅ 用户只需正常聊天
- ✅ 不需要手动触发任何操作
- ✅ Campaign 自动创建
- ✅ 实体自动提取
- ✅ 图谱自动构建
- ✅ 查询自动执行
- ✅ 完全透明，无感知

**4. 与原设计的对比**

| 方面 | 原设计（拦截模式） | 新设计（Function Calling） |
|------|-------------------|---------------------------|
| LLM 调用次数 | 2次（生成 + 提取） | 1次（同时完成） |
| 实现复杂度 | 高（需要解析文本） | 低（标准 API） |
| 可靠性 | 中（解析可能出错） | 高（结构化数据） |
| 用户体验 | 一般 | 优秀（完全透明） |
| Token 消耗 | 高 | 低 |

---

## 实现优先级

### MVP (Phase 1)

1. ✅ Extension 注册 Tool Functions
2. ✅ Campaign 创建工具
3. ✅ 实体存储工具
4. ✅ 基础查询工具
5. ✅ tarven-note Server API

### Phase 2

1. 图谱可视化
2. 高级查询（多跳推理）
3. 实体合并和去重
4. 查询历史

### Phase 3

1. 时间线管理
2. 事件因果链
3. 协作功能
4. 性能优化

---

## 技术栈确认

**前端 (Extension)**:
- JavaScript/TypeScript
- SillyTavern Extension API
- Function Calling API

**后端 (tarven-note Server)**:
- Python 3.10+
- FastAPI
- Neo4j Python Driver

**数据库**:
- Neo4j 5.x (图数据库，存储所有数据)

**LLM**:
- 本地部署或 API (OpenAI / Anthropic / 本地模型)

---

**文档创建时间**: 2026-01-11
**最后更新**: 2026-01-11

