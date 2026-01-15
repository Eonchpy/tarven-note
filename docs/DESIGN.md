# tarven-note 完整设计方案

## 项目概述

### 项目定位

**项目名称**: tarven-note

**核心价值**:
- 为 SillyTavern TRPG 玩家提供智能记忆管理系统
- 基于知识图谱（GraphRAG）的长期记忆解决方案
- 解决 TRPG 跑团中的遗忘、混淆、幻觉问题

**目标用户**:
- COC/DND 等 TRPG 玩家
- 长期战役的 KP/GM
- 需要智能记忆管理的 SillyTavern 用户

**市场空白**:
- 目前没有专门为 TRPG 设计的 tarven-note 插件
- SillyTavern-MemoryBooks 只是简单的 Lorebook 管理
- 通用 GraphRAG 框架不适配 TRPG 场景

---

## 核心问题与解决方案

### TRPG 跑团中的三大问题

**1. 遗忘问题**
- 现象：随着剧情深入，LLM 忘记之前的重要剧情
- 原因：Context Window 限制，老消息被截断
- 解决：永久存储在知识图谱中，随时检索

**2. 混淆问题**
- 现象：LLM 混淆不同的 NPC、地点、事件
- 原因：信息散落在长对话中，缺乏结构化
- 解决：结构化的实体和关系，清晰区分

**3. 幻觉问题**
- 现象：LLM 编造不存在的剧情
- 原因：没有可靠的事实来源
- 解决：基于图谱的事实回答，不编造信息

---

## Domain 设计：Campaign（战役）

### Campaign 作为天然 Domain

```yaml
Domain = Campaign (战役/世界)

每个 Campaign 是一个独立的 Domain:
  - COC: 克苏鲁的呼唤
  - DND: 龙与地下城
  - 赛博朋克 2077
  - 自定义战役
```

### Campaign 数据结构

```python
class Campaign:
    campaign_id: str          # 唯一标识
    name: str                 # 战役名称
    system: str               # 规则系统（COC7、DND5e、Cyberpunk等）
    world_setting: str        # 世界观设定
    description: str          # 战役描述
    created_at: datetime      # 创建时间
    updated_at: datetime      # 更新时间
    status: str               # active/archived/completed
    metadata: dict            # 其他元数据
```

### Campaign 的优势

**1. 天然隔离**
- 不同战役的信息完全独立
- 避免跨战役的信息混淆
- 例如：COC 战役中的"韦弗夫人"不会和 DND 战役中的"韦弗夫人"混淆

**2. 可复用**
- 同一世界观可以多次使用
- 可以基于模板创建新战役
- 例如：基于"克苏鲁神话"模板创建多个不同的调查故事

**3. 易管理**
- 每个战役独立的知识图谱
- 可以单独备份、恢复、删除
- 战役结束后可以归档

**4. 可分享**
- 导出战役图谱（JSON/GraphML）
- 分享给其他玩家
- 导入他人的战役设定

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    SillyTavern                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         tarven-note Extension (前端)             │  │
│  │  - Campaign 管理 UI                              │  │
│  │  - 实体/关系可视化                               │  │
│  │  - 查询界面                                      │  │
│  └──────────────────┬───────────────────────────────┘  │
└─────────────────────┼───────────────────────────────────┘
                      │ HTTP API
                      ↓
┌─────────────────────────────────────────────────────────┐
│              tarven-note Server (后端)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │              FastAPI Service                     │  │
│  │  - Campaign CRUD                                 │  │
│  │  - Entity/Relationship 管理                      │  │
│  │  - Graph 查询 (Cypher)                           │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                   │
│                     ↓                                   │
│          ┌──────────────────────┐                      │
│          │       Neo4j          │                      │
│          │  (知识图谱 + 元数据) │                      │
│          └──────────────────────┘                      │
└─────────────────────────────────────────────────────────┘
                      ↓
              ┌──────────────┐
              │  LLM Service │
              │  (本地/API)  │
              └──────────────┘
```

### 核心架构模式：Function Calling

**重要发现**: SillyTavern 原生支持 Tool Calling（通过 `TOOL_CALLS_PERFORMED` 事件）

**架构模式**:
```
User → LLM (with registered tools) → Function Call → Extension Handler → tarven-note API
```

**关键优势**:
- ✅ LLM 一次调用完成（生成叙述 + 提取实体）
- ✅ 结构化数据传输（无需解析文本）
- ✅ 用户完全无感知（后台自动执行）
- ✅ Token 消耗更低
- ✅ 实现更可靠

**对比传统拦截模式**:

| 方面 | 拦截模式 | Function Calling |
|------|---------|-----------------|
| LLM 调用次数 | 2次 | 1次 |
| 实现复杂度 | 高 | 低 |
| 可靠性 | 中 | 高 |
| Token 消耗 | 高 | 低 |

### 技术栈

**前端（SillyTavern Extension）**:
- JavaScript/TypeScript
- SillyTavern Extension API
- SillyTavern Tool Calling API
- D3.js / Cytoscape.js（图可视化）

**后端（tarven-note Server）**:
- Python 3.10+
- FastAPI
- Neo4j Python Driver

**数据库**:
- Neo4j 5.x（图数据库，存储所有数据）

**LLM**:
- 本地部署或 API（OpenAI / Anthropic / 本地模型）

---

## Schema 规范化设计

### 问题：类型不规范导致的混乱

**不规范化的后果**:
```cypher
# 糟糕的情况 - 同一概念多种表达
(:Character {role: "PC"})
(:Character {role: "player"})
(:Character {role: "调查员"})
(:Character {role: "玩家角色"})

# 查询时会遗漏数据
MATCH (c:Character {role: "PC"})
// 只能找到 role="PC" 的，其他的都找不到！
```

**导致的问题**:
1. ❌ 查询不完整 - 无法找到所有相关实体
2. ❌ 图谱混乱 - 同一概念被分散存储
3. ❌ 关系断裂 - 无法建立正确的连接
4. ❌ 统计错误 - 无法准确统计实体数量

### 解决方案：三层防护机制

**Layer 1: LLM Prompt 约束**
- 在 System Prompt 中明确规范
- 提供正确和错误的示例
- 要求使用英文标准术语

**Layer 2: 服务端规范化**
- 接收数据时自动映射
- 容错处理（中文 → 英文，变体 → 标准）
- 记录日志（哪些被规范化了）

**Layer 3: 数据库约束**
- Neo4j 中使用 Schema 约束
- 只允许预定义的类型
- 拒绝不规范的数据

### 标准 Schema 定义

#### 实体类型规范 (Entity Types)

```python
class EntityType:
    """实体类型标准"""
    CHARACTER = "Character"      # 角色（人物、生物）
    LOCATION = "Location"        # 地点（城市、建筑、房间）
    EVENT = "Event"              # 事件（发生的事情）
    CLUE = "Clue"                # 线索（调查发现的信息）
    ITEM = "Item"                # 物品（道具、装备）
    ORGANIZATION = "Organization" # 组织（团体、机构）
```

#### 角色类型规范 (Character Role)

```python
class CharacterRole:
    """角色类型标准"""
    PC = "PC"              # Player Character (玩家角色)
    NPC = "NPC"            # Non-Player Character (非玩家角色)
    ENEMY = "Enemy"        # 敌人
    ALLY = "Ally"          # 盟友
    NEUTRAL = "Neutral"    # 中立角色
```

#### 地点类型规范 (Location Type)

```python
class LocationType:
    """地点类型标准"""
    CITY = "city"          # 城市
    BUILDING = "building"  # 建筑
    ROOM = "room"          # 房间
    OUTDOOR = "outdoor"    # 户外
    DUNGEON = "dungeon"    # 地下城
```

#### 关系类型规范 (Relationship Types)

```python
class RelationshipType:
    """关系类型标准"""
    # 角色关系
    KNOWS = "KNOWS"              # 认识
    TRUSTS = "TRUSTS"            # 信任
    FEARS = "FEARS"              # 恐惧
    LOVES = "LOVES"              # 爱
    HATES = "HATES"              # 恨

    # 位置关系
    LOCATED_AT = "LOCATED_AT"    # 位于
    WORKS_AT = "WORKS_AT"        # 工作于
    LIVES_AT = "LIVES_AT"        # 居住于

    # 事件关系
    PARTICIPATED_IN = "PARTICIPATED_IN"  # 参与
    WITNESSED = "WITNESSED"              # 目击
    CAUSED = "CAUSED"                    # 导致

    # 物品关系
    OWNS = "OWNS"                # 拥有
    USED = "USED"                # 使用
    FOUND = "FOUND"              # 发现
```

---

## 数据模型设计

### Neo4j 图模型

#### 节点类型（Node Types）

**1. Campaign（战役）**
```cypher
(:Campaign {
  campaign_id: string,
  name: string,
  system: string,
  world_setting: string,
  status: string,
  created_at: datetime
})
```

**2. Character（角色）**
```cypher
(:Character {
  id: string,
  name: string,
  role: string,              # PC/NPC/Enemy
  description: string,       # 简短描述
  attributes: map,           # {HP: 50, SAN: 60, ...}
  status: string,            # alive/dead/unknown
  campaign_id: string
})
```

**3. Location（地点）**
```cypher
(:Location {
  id: string,
  name: string,
  type: string,              # city/building/room
  description: string,
  campaign_id: string
})
```

**4. Event（事件）**
```cypher
(:Event {
  id: string,
  name: string,
  description: string,
  timestamp: datetime,
  importance: int,           # 1-5
  campaign_id: string
})
```

**5. Clue（线索）**
```cypher
(:Clue {
  id: string,
  name: string,
  description: string,
  discovered_by: string,     # character_id
  discovered_at: datetime,
  campaign_id: string
})
```

**6. Item（物品）**
```cypher
(:Item {
  id: string,
  name: string,
  type: string,              # weapon/tool/document
  description: string,
  campaign_id: string
})
```

**7. Organization（组织）**
```cypher
(:Organization {
  id: string,
  name: string,
  type: string,              # cult/government/guild
  description: string,
  goals: string,
  campaign_id: string
})
```

#### 关系类型（Relationship Types）

```cypher
# 角色关系
(Character)-[:KNOWS]->(Character)
(Character)-[:TRUSTS]->(Character)
(Character)-[:FEARS]->(Character)
(Character)-[:LOVES]->(Character)

# 位置关系
(Character)-[:LOCATED_AT]->(Location)
(Item)-[:LOCATED_AT]->(Location)
(Location)-[:CONNECTED_TO]->(Location)

# 事件关系
(Character)-[:PARTICIPATED_IN]->(Event)
(Event)-[:HAPPENED_AT]->(Location)
(Event)-[:CAUSED_BY]->(Event)
(Event)-[:LEADS_TO]->(Event)

# 线索关系
(Clue)-[:DISCOVERED_BY]->(Character)
(Clue)-[:LEADS_TO]->(Location)
(Clue)-[:LEADS_TO]->(Character)
(Clue)-[:LEADS_TO]->(Event)
(Clue)-[:RELATED_TO]->(Clue)

# 物品关系
(Character)-[:OWNS]->(Item)
(Character)-[:USED]->(Item)

# 组织关系
(Character)-[:BELONGS_TO]->(Organization)
(Character)-[:WORKS_FOR]->(Organization)
(Organization)-[:ALLIED_WITH]->(Organization)
(Organization)-[:ENEMY_OF]->(Organization)

# Campaign 关系
(Character)-[:IN_CAMPAIGN]->(Campaign)
(Location)-[:IN_CAMPAIGN]->(Campaign)
(Event)-[:IN_CAMPAIGN]->(Campaign)
```

---

## 核心功能设计

### 功能 1：Campaign 管理

**创建空白 Campaign**
```python
POST /api/campaigns

{
  "name": "克苏鲁的呼唤：阴影之城",
  "system": "COC7",
  "description": "一群调查员在阿卡姆市调查神秘失踪案件"
}

Response:
{
  "campaign_id": "uuid",
  "status": "created",
  "stats": {
    "entities": 0,
    "relationships": 0
  }
}

# Campaign 创建时是空白的
# 图谱将随着游戏进行自然填充
```

### 功能 2：实时信息提取

**KP 叙述后自动提取**
```python
POST /api/campaigns/{campaign_id}/extract

{
  "content": "你从外套内侧掏出那两本从仓库工作台上拿的神秘学书籍...",
  "speaker": "KP"
}

# 后端处理：
# 1. LLM 提取实体
entities = [
  {"type": "Item", "name": "神秘学书籍", "properties": {...}},
  {"type": "Location", "name": "仓库", "properties": {...}}
]

# 2. LLM 提取关系
relationships = [
  {"from": "玩家", "to": "神秘学书籍", "type": "OWNS"},
  {"from": "神秘学书籍", "to": "仓库", "type": "FOUND_AT"}
]

# 3. 更新 Neo4j
```

### 功能 3：结构化查询

> **设计原则**：LLM 在前端解析用户意图，直接调用结构化 API，后端不做语义解析。

**实体查询**
```python
# 按名称查询实体
GET /api/campaigns/{campaign_id}/entities?name=韦弗夫人

# 按类型查询实体
GET /api/campaigns/{campaign_id}/entities?type=Character&role=NPC

Response:
{
  "entities": [
    {
      "id": "char_002",
      "name": "韦弗夫人",
      "type": "Character",
      "properties": {
        "role": "NPC",
        "occupation": "图书馆管理员"
      }
    }
  ]
}
```

**关系查询**
```python
# 查询某实体的关系
GET /api/campaigns/{campaign_id}/relationships?from=韦弗夫人
GET /api/campaigns/{campaign_id}/relationships?to=韦弗夫人
GET /api/campaigns/{campaign_id}/relationships?from=韦弗夫人&type=KNOWS

Response:
{
  "relationships": [
    {
      "from": {"id": "char_001", "name": "调查员"},
      "to": {"id": "char_002", "name": "韦弗夫人"},
      "type": "KNOWS",
      "properties": {}
    }
  ]
}
```

**路径查询（多跳）**
```python
# 查询两个实体之间的路径
GET /api/campaigns/{campaign_id}/paths?from=调查员&to=组织首领&max_hops=3

Response:
{
  "paths": [
    {
      "nodes": ["调查员", "酒保老约翰", "组织首领"],
      "relationships": ["KNOWS", "WORKS_FOR"],
      "hops": 2
    }
  ]
}
```

### 功能 4：图谱可视化

**获取子图**
```python
GET /api/campaigns/{campaign_id}/subgraph?entity_id={id}&depth=2

# 返回以指定实体为中心的子图
# depth=2 表示 2 跳关系
```

**前端渲染**
- 使用 Cytoscape.js 或 D3.js
- 节点：不同颜色表示不同类型
- 边：不同样式表示不同关系
- 交互：点击节点查看详情

---

## 工作流程

### 核心理念：完全动态构建

**重要洞察**：
- TRPG 开始时，KP 也不确定会出现哪些实体
- World Book 是 KP 的参考资料，不是预先导入的内容
- 图谱应该随着游戏进行自然生长

### 流程 1：创建空白 Campaign

```yaml
1. 开始新游戏:
   - 用户在 SillyTavern 中开始新聊天
   - Extension 自动创建空白 Campaign
   - 只需填写：战役名称、规则系统（COC7/DND5e等）

2. Campaign 初始状态:
   - 图谱为空（0 个实体，0 个关系）
   - 准备接收第一条 KP 叙述
   - World Book 保持在 SillyTavern Lorebook 中（不导入）

3. World Book 的作用:
   - 作为 SillyTavern 的 Lorebook 存在
   - 通过关键词触发，注入到 LLM context
   - 帮助 LLM 生成符合世界观的叙述
   - 不需要预先导入到 tarven-note
```

### 流程 2：游戏过程中（动态构建）

```yaml
1. KP 叙述:
   - KP 在 SillyTavern 中输入叙述
   - 消息发送到 LLM

2. 自动提取（后台）:
   - Extension 拦截消息
   - 调用 tarven-note Server 的 extract API
   - LLM 提取新实体和关系
   - 增量更新 Neo4j

3. 玩家回复:
   - 玩家输入回复
   - 如果需要查询信息，LLM 自动调用 query API

4. LLM 生成回答:
   - 基于图谱查询结果
   - 结合对话历史
   - 生成准确的回答
```

### 流程 3：查询和推理

```yaml
玩家问题: "我能通过谁联系到神秘组织的首领？"

1. 意图识别:
   - LLM 识别这是一个关系查询
   - 需要多跳推理

2. 生成 Cypher:
   MATCH path = (me:Character {name: "调查员"})-[:KNOWS*1..3]-(leader:Character {role: "组织首领"})
   WHERE me.campaign_id = $campaign_id
   RETURN path, length(path) as hops
   ORDER BY hops
   LIMIT 3

3. 执行查询:
   - 返回 3 条最短路径

4. 补充细节（可选）:
   - 查询路径中每个角色的详细信息
   - 查询相关的 Word 实体（话语记录）

5. 生成回答:
   "根据你掌握的信息，有两条可能的路径：
   1. 通过酒保老约翰，他似乎和组织有联系
   2. 通过警探汤姆，他有个线人可能认识首领

   建议先找酒保，因为路径更短，风险可能更小。"
```

---

## API 设计

### Campaign 管理

```python
# 创建 Campaign
POST /api/campaigns
Body: {name, system, world_setting, description}
Response: {campaign_id, status}

# 获取 Campaign 列表
GET /api/campaigns
Response: [{campaign_id, name, system, status, ...}]

# 获取 Campaign 详情
GET /api/campaigns/{campaign_id}
Response: {campaign_id, name, ..., stats: {entities: 50, relationships: 120}}

# 更新 Campaign
PUT /api/campaigns/{campaign_id}
Body: {name, description, status}

# 删除 Campaign
DELETE /api/campaigns/{campaign_id}

# 导出 Campaign
GET /api/campaigns/{campaign_id}/export
Response: {graph: {...}, documents: [...]}
```

### 实体和关系管理

```python
# 提取信息
POST /api/campaigns/{campaign_id}/extract
Body: {content, speaker, timestamp}
Response: {entities: [...], relationships: [...]}

# 获取实体列表
GET /api/campaigns/{campaign_id}/entities?type=Character
Response: [{id, name, type, properties}]

# 获取实体详情
GET /api/campaigns/{campaign_id}/entities/{entity_id}
Response: {id, name, type, properties, relationships: [...]}

# 更新实体
PUT /api/campaigns/{campaign_id}/entities/{entity_id}
Body: {properties: {...}}

# 删除实体
DELETE /api/campaigns/{campaign_id}/entities/{entity_id}
```

### 查询

```python
# 关系查询
GET /api/campaigns/{campaign_id}/relationships?from={name}&to={name}&type={type}
Response: {
  relationships: [{from, to, type, properties}]
}

# 路径查询
GET /api/campaigns/{campaign_id}/paths?from={name}&to={name}&max_hops=3
Response: {
  paths: [{nodes, relationships, hops}]
}

# 获取子图
GET /api/campaigns/{campaign_id}/subgraph?entity_id={id}&depth=2
Response: {
  nodes: [{id, label, type, properties}],
  edges: [{from, to, type, properties}]
}
```

---

## 实现路线图

### Phase 1: MVP（4-6 周）

**Week 1-2: 后端基础**
- [ ] 搭建 FastAPI 项目
- [ ] Neo4j 连接和基础 CRUD
- [ ] Campaign 管理 API（创建空白 Campaign）

**Week 3-4: 核心功能**
- [ ] 实体/关系数据模型
- [ ] 关系识别和图谱构建
- [ ] 动态提取和更新机制
- [ ] 图查询功能

**Week 5-6: 前端集成**
- [ ] SillyTavern Extension 基础框架
- [ ] Campaign 管理 UI
- [ ] Tool 注册和 Function Calling
- [ ] 简单的查询界面

**MVP 功能范围**:
- ✅ 创建空白 Campaign
- ✅ 自动提取实体和关系（动态构建）
- ✅ 图查询
- ✅ 图谱随游戏自然生长
- ❌ 图谱可视化（Phase 2）
- ❌ 高级推理（Phase 2）
- ❌ World Book 导入（不需要）

### Phase 2: 增强功能（4-6 周）

**功能增强**:
- [ ] 图谱可视化（Cytoscape.js）
- [ ] 多跳推理优化
- [ ] 混合查询优化
- [ ] 实体合并和去重
- [ ] 关系权重和置信度

**用户体验**:
- [ ] 更好的 UI/UX
- [ ] 实体编辑界面
- [ ] 查询历史
- [ ] 导出/导入功能

### Phase 3: 高级特性（4-6 周）

**高级功能**:
- [ ] 时间线管理
- [ ] 事件因果链追溯
- [ ] 自动总结和 Brief 生成
- [ ] 多 Campaign 对比
- [ ] 协作功能（多人战役）

**性能优化**:
- [ ] 查询缓存
- [ ] 增量更新优化
- [ ] 大规模图谱性能优化

---

## 技术挑战与解决方案

### 挑战 1：实体提取准确性

**问题**: LLM 可能提取错误或遗漏实体

**解决方案**:
1. 使用专门的 Prompt 模板
2. Few-shot 示例
3. 人工审核机制
4. 实体合并和去重算法

### 挑战 2：关系识别复杂度

**问题**: 关系类型多样，难以准确识别

**解决方案**:
1. 预定义关系类型（可扩展）
2. 关系置信度评分
3. 用户确认机制
4. 关系推理规则

### 挑战 3：性能问题

**问题**: 大规模图谱查询可能很慢

**解决方案**:
1. Neo4j 索引优化
2. 查询缓存
3. 子图限制（depth 限制）
4. 异步处理

---

## 开源计划

### 项目结构

```
tarven-note/
├── README.md
├── LICENSE (MIT)
├── docs/
│   ├── installation.md
│   ├── user-guide.md
│   ├── api-reference.md
│   └── development.md
├── server/                    # 后端
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── models/
│   └── requirements.txt
├── extension/                 # SillyTavern Extension
│   ├── index.js
│   ├── manifest.json
│   └── ui/
├── examples/
│   ├── coc-campaign/
│   └── dnd-campaign/
└── tests/
```

### 发布计划

**1. GitHub 发布**:
- 完整的 README
- 安装文档
- 使用示例
- 贡献指南

**2. 社区推广**:
- SillyTavern Discord
- Reddit r/SillyTavern
- TRPG 社区论坛
- 技术博客文章

**3. 持续维护**:
- Issue 管理
- PR 审核
- 版本发布
- 文档更新

---

## 总结

### 核心价值

1. **解决真实痛点**: TRPG 玩家的长期记忆需求
2. **填补市场空白**: 目前没有类似的专用工具
3. **技术创新**: GraphRAG 在 TRPG 场景的首次应用
4. **开源贡献**: 帮助整个 TRPG 社区

### 成功指标

**技术指标**:
- 实体提取准确率 > 85%
- 关系识别准确率 > 80%
- 查询响应时间 < 2s
- 支持 1000+ 实体的图谱

**用户指标**:
- GitHub Stars > 500
- 活跃用户 > 100
- 社区贡献者 > 10

### 下一步行动

1. **立即开始**: 搭建项目框架
2. **MVP 优先**: 4-6 周完成核心功能
3. **快速迭代**: 基于用户反馈优化
4. **社区驱动**: 开源协作，共同完善

---

**项目开始时间**: 2026-01-11
**预计 MVP 完成**: 2026-02-22
**预计 v1.0 发布**: 2026-04-15

让我们开始吧！🚀

### 规范化映射表

#### 类型映射 (Type Mapping)

```python
TYPE_MAPPING = {
    # 中文 → 英文
    "角色": "Character",
    "人物": "Character",
    "地点": "Location",
    "地方": "Location",
    "事件": "Event",
    "线索": "Clue",
    "物品": "Item",
    "道具": "Item",
    "组织": "Organization",
    
    # 变体 → 标准
    "character": "Character",
    "location": "Location",
    "event": "Event",
}
```

#### 角色类型映射 (Role Mapping)

```python
ROLE_MAPPING = {
    # PC 变体
    "pc": "PC",
    "PC": "PC",
    "player": "PC",
    "玩家": "PC",
    "调查员": "PC",
    "玩家角色": "PC",
    "Player": "PC",
    
    # NPC 变体
    "npc": "NPC",
    "NPC": "NPC",
    "非玩家角色": "NPC",
    "路人": "NPC",
    
    # Enemy 变体
    "enemy": "Enemy",
    "敌人": "Enemy",
    "怪物": "Enemy",
    "邪教徒": "Enemy",
}
```

#### 关系类型映射 (Relationship Mapping)

```python
RELATIONSHIP_MAPPING = {
    # KNOWS 变体
    "knows": "KNOWS",
    "认识": "KNOWS",
    "知道": "KNOWS",
    
    # LOCATED_AT 变体
    "located_at": "LOCATED_AT",
    "位于": "LOCATED_AT",
    "在": "LOCATED_AT",
    
    # OWNS 变体
    "owns": "OWNS",
    "拥有": "OWNS",
    "持有": "OWNS",
}
```

### 规范化实现代码

```python
# server/normalizer.py

class EntityNormalizer:
    """实体规范化器"""
    
    @classmethod
    def normalize_entity(cls, entity: dict) -> dict:
        """规范化实体"""
        # 规范化 type
        if "type" in entity:
            original_type = entity["type"]
            entity["type"] = TYPE_MAPPING.get(
                original_type, 
                original_type
            )
            
            # 记录日志
            if entity["type"] != original_type:
                logger.info(f"Normalized type: {original_type} → {entity['type']}")
        
        # 规范化 role
        if "properties" in entity and "role" in entity["properties"]:
            original_role = entity["properties"]["role"]
            entity["properties"]["role"] = ROLE_MAPPING.get(
                original_role,
                original_role
            )
            
            # 记录日志
            if entity["properties"]["role"] != original_role:
                logger.info(f"Normalized role: {original_role} → {entity['properties']['role']}")
        
        return entity
    
    @classmethod
    def normalize_relationship(cls, rel: dict) -> dict:
        """规范化关系"""
        if "type" in rel:
            original_type = rel["type"]
            rel["type"] = RELATIONSHIP_MAPPING.get(
                original_type,
                original_type
            )
            
            # 记录日志
            if rel["type"] != original_type:
                logger.info(f"Normalized relationship: {original_type} → {rel['type']}")
        
        return rel
```

### API 集成示例

```python
# server/api/campaigns.py

@router.post("/campaigns/{campaign_id}/extract")
async def extract_entities(
    campaign_id: str,
    data: dict
):
    """提取并存储实体和关系"""
    
    # Layer 2: 服务端规范化
    normalized_entities = [
        EntityNormalizer.normalize_entity(e) 
        for e in data["entities"]
    ]
    
    normalized_relationships = [
        EntityNormalizer.normalize_relationship(r)
        for r in data["relationships"]
    ]
    
    # 存储到 Neo4j
    await store_to_neo4j(
        campaign_id,
        normalized_entities,
        normalized_relationships
    )
    
    return {
        "success": True,
        "entities_count": len(normalized_entities),
        "relationships_count": len(normalized_relationships)
    }
```


### Layer 1: LLM System Prompt 约束

```python
# Extension 注册工具时的 System Prompt

SYSTEM_PROMPT = """
你是 COC7 KP，负责主持跑团游戏。

你可以使用以下工具:
- tarven_create_campaign: 创建新战役
- tarven_store_entities: 存储实体和关系到知识图谱
- tarven_query: 查询知识图谱中的信息

## 重要：Schema 规范

当你调用 tarven_store_entities 时，必须严格遵守以下规范：

### 实体类型 (type) - 只能使用以下值：
- Character: 角色（人物、生物）
- Location: 地点（城市、建筑、房间）
- Event: 事件（发生的事情）
- Clue: 线索（调查发现的信息）
- Item: 物品（道具、装备）
- Organization: 组织（团体、机构）

### 角色类型 (role) - 只能使用以下值：
- PC: 玩家角色 (Player Character)
- NPC: 非玩家角色 (Non-Player Character)
- Enemy: 敌人
- Ally: 盟友
- Neutral: 中立角色

### 关系类型 (relationship type) - 只能使用以下值：
- KNOWS: 认识
- TRUSTS: 信任
- FEARS: 恐惧
- LOVES: 爱
- HATES: 恨
- LOCATED_AT: 位于
- WORKS_AT: 工作于
- LIVES_AT: 居住于
- PARTICIPATED_IN: 参与
- WITNESSED: 目击
- CAUSED: 导致
- OWNS: 拥有
- USED: 使用
- FOUND: 发现

## 正确示例：
{
  "entities": [
    {
      "type": "Character",
      "name": "韦弗夫人",
      "properties": {
        "role": "NPC",
        "occupation": "图书馆管理员"
      }
    }
  ],
  "relationships": [
    {
      "from": "韦弗夫人",
      "to": "阿卡姆市图书馆",
      "type": "WORKS_AT"
    }
  ]
}

## 错误示例（禁止使用）：
❌ {type: "角色", role: "玩家"}  // 不要用中文
❌ {type: "character", role: "player"}  // 首字母必须大写
❌ {type: "Character", role: "调查员"}  // role 必须用标准值
❌ {relationship: "认识"}  // 关系类型必须用英文大写

必须使用英文标准术语！

## 重要：查询策略

### 主动查询
当玩家输入简单指令（如"C 潜行"）时，你必须主动查询相关信息：
- 查询当前地点的详细信息
- 查询当前地点有哪些 NPC
- 查询玩家角色的相关属性/技能
- 查询可能影响行动结果的实体

### 联想查询
在推理过程中，如果涉及到其他实体，应主动查询：
- 直接相关：玩家明确提到的实体
- 间接相关：与当前场景/行动相关的实体
- 背景相关：可能影响叙述的实体

### 查询示例
```
场景：玩家说"我去图书馆调查"
你应该查询：
1. tarven_query(query_type="entity", entity_name="图书馆")
2. tarven_query(query_type="relationship", to_entity="图书馆", relationship_type="WORKS_AT")

场景：玩家说"C 潜行"（当前在仓库）
你应该查询：
1. tarven_query(query_type="entity", entity_name="仓库")
2. tarven_query(query_type="relationship", to_entity="仓库", relationship_type="LOCATED_AT")

场景：推理时想到韦弗夫人可能知道线索
你应该查询：
1. tarven_query(query_type="entity", entity_name="韦弗夫人")
2. tarven_query(query_type="relationship", from_entity="韦弗夫人")
```

### 查询原则
1. **宁多勿少**：不确定时，多查询几个相关实体
2. **先查后答**：在生成叙述前，先查询所需信息
3. **避免编造**：如果查询无结果，不要编造信息
"""
```


---

## Function Calling 实现详解

### Extension 工具注册

```javascript
// extension/index.js

// 注册工具函数给 LLM
function registerTarvenNoteTools() {
    
    // 工具 1: 创建 Campaign
    SillyTavern.registerToolFunction({
        name: "tarven_create_campaign",
        description: "创建新的 TRPG 战役",
        parameters: {
            type: "object",
            properties: {
                name: {
                    type: "string",
                    description: "战役名称"
                },
                system: {
                    type: "string",
                    description: "规则系统 (COC7, DND5e, Cyberpunk等)"
                },
                description: {
                    type: "string",
                    description: "战役描述"
                }
            },
            required: ["name", "system"]
        },
        handler: async (params) => {
            try {
                const response = await fetch(`${TARVEN_NOTE_SERVER}/api/campaigns`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
                
                const data = await response.json();
                
                // 保存 campaign_id 到会话
                currentCampaignId = data.campaign_id;
                
                return {
                    success: true,
                    campaign_id: data.campaign_id,
                    message: `战役 "${params.name}" 创建成功`
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    });
    
    // 工具 2: 存储实体和关系
    SillyTavern.registerToolFunction({
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
                            properties: { type: "object" }
                        }
                    }
                },
                relationships: {
                    type: "array",
                    description: "关系列表",
                    items: {
                        type: "object",
                        properties: {
                            from: { type: "string" },
                            to: { type: "string" },
                            type: { type: "string" }
                        }
                    }
                }
            },
            required: ["entities", "relationships"]
        },
        handler: async (params) => {
            if (!currentCampaignId) {
                return {
                    success: false,
                    error: "No active campaign"
                };
            }
            
            try {
                const response = await fetch(
                    `${TARVEN_NOTE_SERVER}/api/campaigns/${currentCampaignId}/extract`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(params)
                    }
                );
                
                const data = await response.json();
                
                return {
                    success: true,
                    entities_count: data.entities_count,
                    relationships_count: data.relationships_count
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    });

    // 工具 3: 查询图谱
    //
    // 使用示例：
    //
    // 1. entity 查询 - 查询实体信息
    //    tarven_query({ query_type: "entity", entity_name: "韦弗夫人" })
    //
    // 2. relationship 查询 - 查询关系
    //    tarven_query({ query_type: "relationship", to_entity: "韦弗夫人", relationship_type: "KNOWS" })
    //    → 返回：谁认识韦弗夫人
    //
    //    tarven_query({ query_type: "relationship", from_entity: "韦弗夫人" })
    //    → 返回：韦弗夫人的所有关系
    //
    // 3. path 查询 - 查询路径（多跳）
    //    tarven_query({ query_type: "path", from_entity: "调查员", to_entity: "组织首领", max_hops: 3 })
    //    → 返回：调查员如何联系到组织首领
    //
    SillyTavern.registerToolFunction({
        name: "tarven_query",
        description: "查询知识图谱中的实体、关系或路径",
        parameters: {
            type: "object",
            properties: {
                query_type: {
                    type: "string",
                    enum: ["entity", "relationship", "path"],
                    description: "查询类型：entity(实体)、relationship(关系)、path(路径)"
                },
                entity_name: {
                    type: "string",
                    description: "实体名称（用于 entity 查询）"
                },
                entity_type: {
                    type: "string",
                    description: "实体类型过滤（可选）"
                },
                from_entity: {
                    type: "string",
                    description: "关系起点实体名称（用于 relationship/path 查询）"
                },
                to_entity: {
                    type: "string",
                    description: "关系终点实体名称（用于 relationship/path 查询）"
                },
                relationship_type: {
                    type: "string",
                    description: "关系类型过滤（可选）"
                },
                max_hops: {
                    type: "number",
                    description: "最大跳数（用于 path 查询，默认3）"
                }
            },
            required: ["query_type"]
        },
        handler: async (params) => {
            if (!currentCampaignId) {
                return { success: false, error: "No active campaign" };
            }

            try {
                let url = `${TARVEN_NOTE_SERVER}/api/campaigns/${currentCampaignId}`;

                // 根据查询类型构建 URL
                switch (params.query_type) {
                    case "entity":
                        url += `/entities?name=${encodeURIComponent(params.entity_name)}`;
                        if (params.entity_type) url += `&type=${params.entity_type}`;
                        break;
                    case "relationship":
                        url += `/relationships?`;
                        if (params.from_entity) url += `from=${encodeURIComponent(params.from_entity)}&`;
                        if (params.to_entity) url += `to=${encodeURIComponent(params.to_entity)}&`;
                        if (params.relationship_type) url += `type=${params.relationship_type}`;
                        break;
                    case "path":
                        url += `/paths?from=${encodeURIComponent(params.from_entity)}`;
                        url += `&to=${encodeURIComponent(params.to_entity)}`;
                        url += `&max_hops=${params.max_hops || 3}`;
                        break;
                }

                const response = await fetch(url);
                const data = await response.json();

                return {
                    success: true,
                    data: data  // 返回 entities/relationships/paths
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    });
}

// Extension 初始化时注册工具
jQuery(async () => {
    registerTarvenNoteTools();
    console.log("tarven-note tools registered");
});
```


### LLM 调用示例

#### 场景 1: 创建 Campaign

```json
// User 输入: "我想开启一个 COC7 的跑团，1920s 阿卡姆背景"

// LLM 输出:
{
  "content": "好的！让我为你创建一个 COC7 战役。",
  "tool_calls": [
    {
      "id": "call_001",
      "type": "function",
      "function": {
        "name": "tarven_create_campaign",
        "arguments": {
          "name": "阿卡姆调查",
          "system": "COC7",
          "description": "1920s 阿卡姆背景的克苏鲁调查"
        }
      }
    }
  ]
}

// Extension Handler 自动执行
// 返回: { success: true, campaign_id: "uuid-xxx" }

// LLM 继续生成:
{
  "content": "战役创建成功！1920年的阿卡姆市，秋风萧瑟。你是一名私家侦探...",
  "tool_calls": [
    {
      "id": "call_002",
      "type": "function",
      "function": {
        "name": "tarven_store_entities",
        "arguments": {
          "entities": [
            {
              "type": "Location",
              "name": "阿卡姆市",
              "properties": {
                "type": "city",
                "era": "1920s"
              }
            },
            {
              "type": "Character",
              "name": "调查员",
              "properties": {
                "role": "PC",
                "occupation": "私家侦探"
              }
            }
          ],
          "relationships": [
            {
              "from": "调查员",
              "to": "阿卡姆市",
              "type": "LOCATED_AT"
            }
          ]
        }
      }
    }
  ]
}
```


#### 场景 2: 游戏进行中 - 自动提取实体

```json
// User 输入: "我去图书馆调查"

// LLM 输出:
{
  "content": "你来到了阿卡姆市图书馆，管理员韦弗夫人正在整理书籍...",
  "tool_calls": [
    {
      "id": "call_003",
      "type": "function",
      "function": {
        "name": "tarven_store_entities",
        "arguments": {
          "entities": [
            {
              "type": "Location",
              "name": "阿卡姆市图书馆",
              "properties": {
                "type": "building",
                "description": "阿卡姆市的公共图书馆"
              }
            },
            {
              "type": "Character",
              "name": "韦弗夫人",
              "properties": {
                "role": "NPC",
                "occupation": "图书馆管理员",
                "status": "alive"
              }
            }
          ],
          "relationships": [
            {
              "from": "韦弗夫人",
              "to": "阿卡姆市图书馆",
              "type": "WORKS_AT"
            },
            {
              "from": "调查员",
              "to": "阿卡姆市图书馆",
              "type": "LOCATED_AT"
            }
          ]
        }
      }
    }
  ]
}

// 用户只看到叙述，完全不知道后台在构建图谱！
```

#### 场景 3: 玩家查询

```json
// User 输入: "谁认识韦弗夫人？"

// LLM 输出:
{
  "content": "让我查询一下...",
  "tool_calls": [
    {
      "id": "call_004",
      "type": "function",
      "function": {
        "name": "tarven_query",
        "arguments": {
          "question": "谁认识韦弗夫人？",
          "query_type": "graph"
        }
      }
    }
  ]
}

// Extension Handler 执行查询
// 返回: { 
//   success: true, 
//   results: [{ name: "调查员", relationship: "KNOWS" }],
//   reasoning: "根据图谱，调查员认识韦弗夫人"
// }

// LLM 基于查询结果生成回答:
{
  "content": "根据你掌握的信息，你（调查员）认识韦弗夫人。她是阿卡姆市图书馆的管理员。"
}
```

