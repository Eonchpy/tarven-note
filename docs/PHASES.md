# tarven-note 开发路线图

## 项目概述

tarven-note 是一个基于知识图谱的 SillyTavern 记忆管理扩展，专为 TRPG 玩家设计。

---

## Phase 0: 项目初始化

### 目标
搭建项目基础结构和开发环境

### 任务清单
- [ ] 创建项目目录结构
- [ ] 配置 Extension（package.json, manifest.json）
- [ ] 配置 Server（pyproject.toml, requirements.txt）
- [ ] 编写 README.md
- [ ] 配置 .gitignore
- [ ] 配置开发环境文档

### 交付物
```
tarven-note/
├── docs/
├── extension/
│   ├── package.json
│   └── manifest.json
├── server/
│   ├── pyproject.toml
│   └── requirements.txt
├── README.md
└── .gitignore
```

---

## Phase 1: 后端基础架构

### 目标
搭建 FastAPI 后端框架和数据库连接

### 任务清单
- [ ] FastAPI 项目框架
- [ ] Neo4j 连接层
- [ ] Campaign 数据模型
- [ ] Campaign CRUD API
- [ ] 健康检查接口

### 交付物
- 可运行的 FastAPI 服务
- Campaign 增删改查 API
- 数据库连接测试通过

### API 端点
```
POST   /api/campaigns          # 创建 Campaign
GET    /api/campaigns          # 列表
GET    /api/campaigns/{id}     # 详情
PUT    /api/campaigns/{id}     # 更新
DELETE /api/campaigns/{id}     # 删除
GET    /health                 # 健康检查
```

---

## Phase 2: 实体与关系管理

### 目标
实现实体和关系的 CRUD 及 Schema 规范化

### 任务清单
- [ ] 实体数据模型（Character, Location, Event, Clue, Item, Organization）
- [ ] 实体 CRUD API
- [ ] 关系数据模型
- [ ] 关系 CRUD API
- [ ] Schema 规范化器（三层防护）
- [ ] Neo4j 图操作封装

### 交付物
- 实体管理 API
- 关系管理 API
- 规范化映射表

### API 端点
```
POST   /api/campaigns/{id}/entities           # 创建实体
GET    /api/campaigns/{id}/entities           # 列表
GET    /api/campaigns/{id}/entities/{eid}     # 详情
PUT    /api/campaigns/{id}/entities/{eid}     # 更新
DELETE /api/campaigns/{id}/entities/{eid}     # 删除

POST   /api/campaigns/{id}/relationships      # 创建关系
GET    /api/campaigns/{id}/relationships      # 列表
DELETE /api/campaigns/{id}/relationships/{rid} # 删除
```

---

## Phase 3: 查询系统

### 目标
实现图查询功能

### 任务清单
- [ ] Cypher 查询生成器
- [ ] 图查询 API
- [ ] 子图获取 API

### 交付物
- 图查询可用
- 查询结果格式化

### API 端点
```
POST /api/campaigns/{id}/query     # 智能查询
GET  /api/campaigns/{id}/subgraph  # 获取子图
```

---

## Phase 4: Extension 基础

### 目标
搭建 SillyTavern Extension 框架

### 任务清单
- [ ] Extension 入口文件（index.js）
- [ ] 配置管理（settings）
- [ ] 后端通信层（API client）
- [ ] Tool 注册框架
- [ ] 事件监听（TOOL_CALLS_PERFORMED）

### 交付物
- 可加载的 SillyTavern Extension
- 与后端通信成功

---

## Phase 5: Function Calling 集成

### 目标
实现三个核心 Tool 并完成端到端集成

### 任务清单
- [ ] graphrag_create_campaign Tool
- [ ] graphrag_store_entities Tool
- [ ] graphrag_query Tool
- [ ] System Prompt 模板
- [ ] 端到端测试

### 交付物
- 三个 Tool 可被 LLM 调用
- 完整的游戏流程测试

### Tool 定义
```javascript
graphrag_create_campaign  // 创建战役
graphrag_store_entities   // 存储实体和关系
graphrag_query            // 查询图谱
```

---

## Phase 6: UI（可选）

### 目标
提供可视化管理界面

### 任务清单
- [ ] Campaign 管理面板
- [ ] 实体列表视图
- [ ] 图谱可视化（Cytoscape.js）
- [ ] 查询界面

### 交付物
- Extension 设置面板
- 图谱可视化组件

---

## 里程碑

| Phase | 名称 | 状态 |
|-------|------|------|
| 0 | 项目初始化 | 🔲 待开始 |
| 1 | 后端基础架构 | 🔲 待开始 |
| 2 | 实体与关系管理 | 🔲 待开始 |
| 3 | 查询系统 | 🔲 待开始 |
| 4 | Extension 基础 | 🔲 待开始 |
| 5 | Function Calling | 🔲 待开始 |
| 6 | UI | 🔲 可选 |

---

## 技术栈

### Extension（前端）
- JavaScript/TypeScript
- SillyTavern Extension API
- Cytoscape.js（图可视化）

### Server（后端）
- Python 3.10+
- FastAPI
- Neo4j Python Driver

### 数据库
- Neo4j 5.x（图数据库，存储所有数据）

---

*创建时间: 2026-01-14*
