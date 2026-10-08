from __future__ import annotations

import os
import sqlite3
import sys
import urllib.parse
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Iterator

from sqlalchemy import Column, DateTime, Integer, String, create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[2]


def _is_test_mode() -> bool:
    if os.getenv("USE_IN_MEMORY_DB", "").lower() in {"1", "true", "yes"}:
        return True
    return any(
        segment in Path(sys.argv[0]).name.lower()
        for segment in ("pytest", "_pytest", "test")
    ) or any("pytest" in arg.lower() for arg in sys.argv)


def _load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        env_example = ROOT / ".env.example"
        if env_example.exists():
            env_path.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_env()


def build_mysql_url(include_database: bool = True) -> str:
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    name = os.getenv("DB_NAME", "ecommerce_intelligence")
    charset = os.getenv("DB_CHARSET", "utf8mb4")
    safe_user = urllib.parse.quote_plus(user)
    safe_password = urllib.parse.quote_plus(password, safe="")
    db_segment = f"/{urllib.parse.quote_plus(name)}" if include_database else "/"
    return f"mysql+pymysql://{safe_user}:{safe_password}@{host}:{port}{db_segment}?charset={charset}"


SQLITE_FALLBACK_PATH = ROOT / "data" / "users.db"
SQLITE_FALLBACK_URL = f"sqlite:///{SQLITE_FALLBACK_PATH.as_posix()}"
SQLITE_IN_MEMORY_URL = "sqlite:///:memory:"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(32), nullable=True, index=True)
    password = Column(String(512), nullable=False)
    role = Column(String(64), nullable=False, default="Viewer")
    otp_code = Column(String(16), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict[str, str]:
        return {
            "email": self.email,
            "phone": self.phone or "",
            "role": self.role or "Viewer",
        }


_SHARED_INMEMORY_CONN: sqlite3.Connection | None = None


def _get_shared_memory_conn() -> sqlite3.Connection:
    global _SHARED_INMEMORY_CONN
    if _SHARED_INMEMORY_CONN is None:
        _SHARED_INMEMORY_CONN = sqlite3.connect(":memory:", check_same_thread=False)
        _SHARED_INMEMORY_CONN.isolation_level = None
    return _SHARED_INMEMORY_CONN


_ENGINE_STATE: dict[str, object] = {}


def _build_engine_and_backend() -> tuple[Engine, str]:
    test_mode = _is_test_mode()
    if not test_mode:
        try:
            root_engine = create_engine(
                build_mysql_url(include_database=False),
                pool_pre_ping=True,
                pool_recycle=1800,
                future=True,
                connect_args={"connect_timeout": 5},
            )
            with root_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_name = os.getenv("DB_NAME", "ecommerce_intelligence")
            with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            mysql_engine = create_engine(
                build_mysql_url(include_database=True),
                pool_pre_ping=True,
                pool_recycle=1800,
                future=True,
                connect_args={"connect_timeout": 5},
            )
            with mysql_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return mysql_engine, "mysql"
        except (SQLAlchemyError, ModuleNotFoundError, Exception):
            pass

    if test_mode:
        sqlite_engine = create_engine(
            SQLITE_IN_MEMORY_URL,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            creator=_get_shared_memory_conn,
        )
        return sqlite_engine, "sqlite-memory"

    SQLITE_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    sqlite_engine = create_engine(
        SQLITE_FALLBACK_URL,
        future=True,
        connect_args={"check_same_thread": False},
    )
    return sqlite_engine, "sqlite"


def _ensure_engine_ready() -> None:
    if "engine" in _ENGINE_STATE and "backend" in _ENGINE_STATE:
        return
    engine, backend = _build_engine_and_backend()
    _ENGINE_STATE["engine"] = engine
    _ENGINE_STATE["backend"] = backend
    if backend == "sqlite-memory":
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()


def force_rebuild_engine() -> None:
    _ENGINE_STATE.clear()
    _ensure_engine_ready()


def get_db_engine() -> Engine:
    _ensure_engine_ready()
    return _ENGINE_STATE["engine"]  # type: ignore[return-value]


def get_db_backend() -> str:
    _ensure_engine_ready()
    return _ENGINE_STATE["backend"]  # type: ignore[return-value]


DB_BACKEND: str = get_db_backend()
db_engine: Engine = get_db_engine()


def _session_factory() -> sessionmaker[Session]:
    _ensure_engine_ready()
    if "session_factory" not in _ENGINE_STATE:
        _ENGINE_STATE["session_factory"] = sessionmaker(
            bind=_ENGINE_STATE["engine"],
            autoflush=False,
            autocommit=False,
            future=True,
            expire_on_commit=False,
        )
    return _ENGINE_STATE["session_factory"]  # type: ignore[return-value]


def init_db() -> None:
    _ensure_engine_ready()
    engine = _ENGINE_STATE["engine"]
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            for col, col_type in [("phone", "VARCHAR(32)"), ("otp_code", "VARCHAR(16)"), ("otp_expires_at", "DATETIME")]:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                except Exception:
                    pass
    except Exception:
        pass


@contextmanager
def get_session() -> Iterator[Session]:
    factory = _session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Iterator[Session]:
    factory = _session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_user(
    session: Session,
    email: str,
    hashed_password: str,
    role: str = "Viewer",
    phone: str | None = None,
) -> User:
    user = User(
        email=email.strip().lower(),
        phone=phone.strip() if phone else None,
        password=hashed_password,
        role=role,
    )
    session.add(user)
    session.flush()
    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.query(User).filter(User.email == email.strip().lower()).first()


def get_user_by_phone_or_email(session: Session, identifier: str) -> User | None:
    clean = identifier.strip().lower()
    user = session.query(User).filter(User.email == clean).first()
    if user:
        return user
    # Try by phone number
    digits = "".join(ch for ch in clean if ch.isdigit())
    if digits:
        for u in session.query(User).all():
            if u.phone and "".join(ch for ch in u.phone if ch.isdigit()) == digits:
                return u
    return None


@asynccontextmanager
async def app_lifespan(_app) -> AsyncIterator[None]:
    force_rebuild_engine()
    init_db()
    yield
