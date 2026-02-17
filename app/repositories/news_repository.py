from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app import database


def _accumulate_upsert_result(result, *, inserted: int, updated: int) -> Tuple[int, int]:
    inserted_flag = None

    scalar = getattr(result, "scalar", None)
    if callable(scalar):
        try:
            inserted_flag = scalar()
        except Exception:
            inserted_flag = None

    if inserted_flag is True:
        return inserted + 1, updated
    if inserted_flag is False:
        return inserted, updated + 1

    rowcount = getattr(result, "rowcount", 0)
    if rowcount == 1:
        return inserted + 1, updated
    if rowcount == 2:
        return inserted, updated + 1
    return inserted, updated


def upsert_articles(articles: List[Dict[str, Any]]) -> Tuple[int, int]:
    inserted = 0
    updated = 0

    sql = text(
        """
        INSERT INTO news_articles
          (source, title, url, published_at, author, summary, content, keywords)
        VALUES
          (:source, :title, :url, :published_at, :author, :summary, :content, CAST(:keywords AS jsonb))
        ON CONFLICT (url) DO UPDATE SET
          source = EXCLUDED.source,
          title = EXCLUDED.title,
          published_at = EXCLUDED.published_at,
          author = EXCLUDED.author,
          summary = EXCLUDED.summary,
          content = EXCLUDED.content,
          keywords = EXCLUDED.keywords,
          updated_at = CURRENT_TIMESTAMP
        RETURNING (xmax = 0) AS inserted
        """
    )

    with database.engine.begin() as conn:
        for article in articles:
            params = {
                "source": article.get("source"),
                "title": article.get("title"),
                "url": article.get("url"),
                "published_at": article.get("published_at"),
                "author": article.get("author"),
                "summary": article.get("summary"),
                "content": article.get("content"),
                "keywords": json.dumps(article.get("keywords")) if article.get("keywords") is not None else None,
            }
            result = conn.execute(sql, params)
            inserted, updated = _accumulate_upsert_result(result, inserted=inserted, updated=updated)

    return inserted, updated


def list_articles(
    *,
    q: Optional[str],
    source: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    page: int,
    size: int,
) -> Tuple[List[Dict[str, Any]], int]:
    where = []
    params: Dict[str, Any] = {}

    if q:
        where.append("(title ILIKE :q OR summary ILIKE :q OR content ILIKE :q)")
        params["q"] = f"%{q}%"

    if source:
        where.append("source = :source")
        params["source"] = source

    if date_from:
        where.append("published_at >= :date_from")
        params["date_from"] = date_from

    if date_to:
        where.append("published_at <= :date_to")
        params["date_to"] = date_to

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    list_sql = text(
        f"""
        SELECT
            id, source, title, url, published_at, author, summary, keywords, created_at, updated_at
        FROM news_articles
        {where_sql}
        ORDER BY COALESCE(published_at, created_at) DESC, id DESC
        LIMIT :limit OFFSET :offset
        """
    )

    count_sql = text(
        f"""
        SELECT COUNT(*) AS total
        FROM news_articles
        {where_sql}
        """
    )

    with database.engine.begin() as conn:
        rows = conn.execute(
            list_sql,
            {**params, "limit": size, "offset": (page - 1) * size},
        ).mappings().all()
        total = conn.execute(count_sql, params).scalar() or 0

    return [dict(row) for row in rows], int(total)


def get_article(item_id: int) -> Optional[Dict[str, Any]]:
    sql = text(
        "SELECT id, source, title, url, published_at, author, summary, content, keywords, created_at, updated_at "
        "FROM news_articles WHERE id=:id"
    )

    with database.engine.begin() as conn:
        row = conn.execute(sql, {"id": item_id}).mappings().first()

    return dict(row) if row else None


def delete_article(item_id: int) -> bool:
    with database.engine.begin() as conn:
        result = conn.execute(text("DELETE FROM news_articles WHERE id=:id"), {"id": item_id})

    return result.rowcount > 0
