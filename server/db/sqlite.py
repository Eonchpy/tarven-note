"""
SQLite database connection module for tarven-note.
Provides connection management and basic utilities for SQLite + sqlite-vss.
"""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from server.core.config import settings


# 数据库文件路径
_db_path: Optional[Path] = None
_connection: Optional[sqlite3.Connection] = None


def get_db_path() -> Path:
    """获取数据库文件路径"""
    global _db_path
    if _db_path is None:
        _db_path = Path(settings.sqlite_db_path)
        _db_path.parent.mkdir(parents=True, exist_ok=True)
    return _db_path


def get_connection() -> sqlite3.Connection:
    """获取SQLite连接（单例模式）"""
    global _connection
    if _connection is None:
        db_path = get_db_path()
        _connection = sqlite3.connect(str(db_path), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        # 启用外键约束
        _connection.execute("PRAGMA foreign_keys = ON")
    return _connection


@contextmanager
def get_cursor():
    """获取数据库游标的上下文管理器"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def close_connection():
    """关闭数据库连接"""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


def ping() -> dict:
    """检查数据库连接状态"""
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT 1 AS ok")
            row = cursor.fetchone()
        return {"ok": bool(row and row["ok"] == 1)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
