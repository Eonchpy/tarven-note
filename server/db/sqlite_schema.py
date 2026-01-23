"""
SQLite schema definitions for tarven-note.
包含实体表、别名表、对话表的DDL定义。
"""
from server.db.sqlite import get_cursor


# ============================================================
# 实体表 - 存储所有实体的详细属性
# 使用单表 + JSON 字段存储不同类型实体的属性
# ============================================================
ENTITIES_TABLE = """
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT UNIQUE NOT NULL,
    campaign_id TEXT NOT NULL,
    type TEXT NOT NULL,
    name TEXT NOT NULL,

    -- 通用属性 (所有实体类型共享)
    description TEXT,

    -- Character 类型属性
    occupation TEXT,
    age INTEGER,
    gender TEXT,
    appearance TEXT,
    personality TEXT,
    background TEXT,

    -- Location 类型属性
    location_type TEXT,
    address TEXT,

    -- Item 类型属性
    item_type TEXT,
    rarity TEXT,

    -- Event 类型属性
    event_time TEXT,
    participants TEXT,  -- JSON array

    -- Organization 类型属性
    org_type TEXT,
    members TEXT,  -- JSON array

    -- 扩展属性 (JSON格式，用于存储规则系统特定属性)
    -- 如 COC 的技能值、DND 的属性值等
    attributes TEXT,  -- JSON object

    -- 列表类型字段 (追加而非覆盖)
    aliases TEXT,     -- JSON array: 别名列表
    used_names TEXT,  -- JSON array: 曾用名
    notes TEXT,       -- JSON array: 备注列表

    -- 元数据
    metadata TEXT,    -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    UNIQUE(campaign_id, name)
)
"""

ENTITIES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_entities_campaign ON entities(campaign_id)",
    "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)",
    "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)",
]


# ============================================================
# 别名表 - 用于快速查找实体的稳定别名
# ============================================================
ALIASES_TABLE = """
CREATE TABLE IF NOT EXISTS entity_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(campaign_id, alias),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id) ON DELETE CASCADE
)
"""

ALIASES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_aliases_campaign ON entity_aliases(campaign_id)",
    "CREATE INDEX IF NOT EXISTS idx_aliases_entity ON entity_aliases(entity_id)",
]


# ============================================================
# 对话表 - 存储对话历史用于双路召回
# ============================================================
MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    campaign_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    entity_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

MESSAGES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_messages_campaign ON messages(campaign_id)",
    "CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)",
]


# ============================================================
# 向量嵌入表 - 存储实体和消息的向量表示
# ============================================================
EMBEDDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref_type TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    embedding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ref_type, ref_id)
)
"""

EMBEDDINGS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_embeddings_ref ON embeddings(ref_type, ref_id)",
]


# ============================================================
# Schema 应用函数
# ============================================================
ALL_TABLES = [
    ENTITIES_TABLE,
    ALIASES_TABLE,
    MESSAGES_TABLE,
    EMBEDDINGS_TABLE,
]

ALL_INDEXES = (
    ENTITIES_INDEXES +
    ALIASES_INDEXES +
    MESSAGES_INDEXES +
    EMBEDDINGS_INDEXES
)


def apply_sqlite_schema() -> None:
    """应用所有SQLite表和索引"""
    with get_cursor() as cursor:
        for table_ddl in ALL_TABLES:
            cursor.execute(table_ddl)
        for index_ddl in ALL_INDEXES:
            cursor.execute(index_ddl)
