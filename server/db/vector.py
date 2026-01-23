"""
Vector search module for tarven-note.
提供基于 sqlite-vss 的向量搜索功能。
"""
import json
import struct
from typing import List, Optional, Tuple

from server.db.sqlite import get_cursor, get_connection
from server.core.config import settings


def _serialize_embedding(embedding: List[float]) -> bytes:
    """将浮点数列表序列化为二进制格式"""
    return struct.pack(f'{len(embedding)}f', *embedding)


def _deserialize_embedding(data: bytes) -> List[float]:
    """将二进制数据反序列化为浮点数列表"""
    count = len(data) // 4
    return list(struct.unpack(f'{count}f', data))


def store_embedding(ref_type: str, ref_id: str, embedding: List[float]) -> None:
    """存储向量嵌入"""
    blob = _serialize_embedding(embedding)
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO embeddings (ref_type, ref_id, embedding)
            VALUES (?, ?, ?)
            ON CONFLICT(ref_type, ref_id) DO UPDATE SET
                embedding = excluded.embedding,
                created_at = CURRENT_TIMESTAMP
        """, (ref_type, ref_id, blob))


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_similar(
    query_embedding: List[float],
    ref_type: Optional[str] = None,
    limit: int = 10
) -> List[Tuple[str, str, float]]:
    """
    搜索相似向量
    返回: [(ref_type, ref_id, similarity), ...]
    """
    with get_cursor() as cursor:
        if ref_type:
            cursor.execute(
                "SELECT ref_type, ref_id, embedding FROM embeddings WHERE ref_type = ?",
                (ref_type,)
            )
        else:
            cursor.execute("SELECT ref_type, ref_id, embedding FROM embeddings")

        results = []
        for row in cursor.fetchall():
            emb = _deserialize_embedding(row["embedding"])
            sim = _cosine_similarity(query_embedding, emb)
            results.append((row["ref_type"], row["ref_id"], sim))

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:limit]
