"""SQLite database models using SQLAlchemy 2.0.

Engine is lazily initialised so that importing this module never touches
the filesystem (important for unit-tests, linting, etc.).
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Index,
    create_engine,
    Engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

JST = timezone(timedelta(hours=9))

from config_paths import DB_PATH as _DB_PATH_OBJ
DB_PATH = str(_DB_PATH_OBJ)

# ── Thread-safe lazy init ──

_init_lock = threading.RLock()  # reentrant: get_session() → get_engine() calls within same lock
_engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker[Session]] = None


def _create_engine() -> Engine:
    """Create (or return cached) SQLAlchemy Engine with WAL + busy timeout."""
    global _engine
    if _engine is not None:
        return _engine
    with _init_lock:
        if _engine is not None:
            return _engine
        eng = create_engine(
            f"sqlite:///{DB_PATH}",
            echo=False,
            connect_args={
                "check_same_thread": False,
            },
        )

        @event.listens_for(eng, "connect")
        def _on_connect(dbapi_connection, _connection_record):
            dbapi_connection.execute("PRAGMA journal_mode=WAL")
            dbapi_connection.execute("PRAGMA busy_timeout=5000")
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        _engine = eng
        return eng


def get_engine() -> Engine:
    """Return the module-level SQLAlchemy Engine (lazy init)."""
    return _create_engine()


def get_session() -> sessionmaker[Session]:
    """Return the module-level session factory (lazy init)."""
    global SessionLocal
    if SessionLocal is None:
        with _init_lock:
            if SessionLocal is None:
                SessionLocal = sessionmaker(bind=get_engine())
    return SessionLocal


# ── Delete the legacy __getattr__ (SessionLocal is now a module-level var) ──


# ── ORM base ──


class Base(DeclarativeBase):
    pass


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String, nullable=False)
    platform = Column(String, nullable=False, index=True)  # youtube / niconico
    title = Column(String)
    url = Column(String)
    channel = Column(String)
    channel_id = Column(String)
    channel_url = Column(String)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    thumbnail_url = Column(String)
    description_snippet = Column(String)
    published_at = Column(DateTime(timezone=True), nullable=True)
    published_text = Column(String)
    score = Column(Float, default=0.0)
    time_window = Column(String, index=True)  # 24h / 3d / 7d
    scraped_date = Column(String, index=True)  # YYYY-MM-DD
    is_short = Column(Integer, default=0)
    is_live = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_platform_window_date", "platform", "time_window", "scraped_date"),
    )


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(get_engine())
