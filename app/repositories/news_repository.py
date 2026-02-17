from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.ports.repositories import NewsRepositoryPort
from app.repositories.common import build_where_clause, dedupe_rows_by_key, execute_paginated_query, to_json_recordset
from app.repositories.session_provider import ConnectionProvider, open_connection_scope


def upsert_articles(
    articles: list[dict[str, Any]],
    *,
    connection_provider: ConnectionProvider,
) -> tuple[int, int]:
    if not articles:
        return 0, 0

    payload_rows = [
        {
            "source": article.get("source"),
            "title": article.get("title"),
            "url": article.get("url"),
            "published_at": article.get("published_at"),
            "author": article.get("author"),
            "summary": article.get("summary"),
            "content": article.get("content"),
            "keywords": article.get("keywords"),
        }
        for article in articles
    ]
    payload_rows = dedupe_rows_by_key(payload_rows, key="url")

    sql = text(
        """
        WITH payload AS (
            SELECT *
            FROM jsonb_to_recordset(CAST(:items AS jsonb))
              AS p(
                source text,
                title text,
                url text,
                published_at timestamptz,
                author text,
                summary text,
                content text,
                keywords jsonb
              )
        ),
        upserted AS (
            INSERT INTO news_articles
              (source, title, url, published_at, author, summary, content, keywords)
            SELECT
              source, title, url, published_at, author, summary, content, keywords
            FROM payload
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
        )
        SELECT
          COALESCE(SUM(CASE WHEN inserted THEN 1 ELSE 0 END), 0) AS inserted,
          COALESCE(SUM(CASE WHEN NOT inserted THEN 1 ELSE 0 END), 0) AS updated
        FROM upserted
        """
    )

    with open_connection_scope(connection_provider) as conn:
        row = conn.execute(sql, {"items": to_json_recordset(payload_rows)}).mappings().first() or {}

    return int(row.get("inserted") or 0), int(row.get("updated") or 0)


def list_articles(
    *,
    q: str | None,
    source: str | None,
    date_from: str | None,
    date_to: str | None,
    page: int,
    size: int,
    connection_provider: ConnectionProvider,
) -> tuple[list[dict[str, Any]], int]:
    where = []
    params: dict[str, Any] = {}

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

    return execute_paginated_query(
        list_sql=list_sql,
        count_sql=count_sql,
        params=params,
        page=page,
        size=size,
        connection_provider=connection_provider,
    )


def get_article(
    item_id: int,
    *,
    connection_provider: ConnectionProvider,
) -> dict[str, Any] | None:
    sql = text(
        "SELECT id, source, title, url, published_at, author, summary, content, keywords, created_at, updated_at "
        "FROM news_articles WHERE id=:id"
    )

    with open_connection_scope(connection_provider) as conn:
        row = conn.execute(sql, {"id": item_id}).mappings().first()

    return dict(row) if row else None


def delete_article(
    item_id: int,
    *,
    connection_provider: ConnectionProvider,
) -> bool:
    with open_connection_scope(connection_provider) as conn:
        result = conn.execute(text("DELETE FROM news_articles WHERE id=:id"), {"id": item_id})

    return result.rowcount > 0


class NewsRepository(NewsRepositoryPort):
    def __init__(self, *, connection_provider: ConnectionProvider) -> None:
        self._connection_provider = connection_provider

    def upsert_articles(self, articles: list[dict[str, Any]]) -> tuple[int, int]:
        return upsert_articles(articles, connection_provider=self._connection_provider)

    def list_articles(
        self,
        *,
        q: str | None,
        source: str | None,
        date_from: str | None,
        date_to: str | None,
        page: int,
        size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        return list_articles(
            q=q,
            source=source,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size,
            connection_provider=self._connection_provider,
        )

    def get_article(self, item_id: int) -> dict[str, Any] | None:
        return get_article(item_id, connection_provider=self._connection_provider)

    def delete_article(self, item_id: int) -> bool:
        return delete_article(item_id, connection_provider=self._connection_provider)
