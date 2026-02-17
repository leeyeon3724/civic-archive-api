from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

engine: Engine = None  # type: ignore[assignment]


def init_db(database_url):
    global engine
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True,
    )
    return engine

