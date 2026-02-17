from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app import database
from app.repositories.common import accumulate_upsert_result, build_where_clause, execute_paginated_query


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
            inserted, updated = accumulate_upsert_result(result, inserted=inserted, updated=updated)

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
        where.append("published_at < (CAST(:date_to AS date) + INTERVAL '1 day')")
        params["date_to"] = date_to

    where_sql = build_where_clause(where)

    list_sql = f"""
        SELECT
            id, source, title, url, published_at, author, summary, keywords, created_at, updated_at
        FROM news_articles
        {where_sql}
        ORDER BY COALESCE(published_at, created_at) DESC, id DESC
        LIMIT :limit OFFSET :offset
        """

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM news_articles
        {where_sql}
        """

    return execute_paginated_query(list_sql=list_sql, count_sql=count_sql, params=params, page=page, size=size)


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
