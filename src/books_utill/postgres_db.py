import logging
from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional, Sequence

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result, Row
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

DEFAULT_HOST = "gek"
DEFAULT_PORT = 5432
DEFAULT_USER = "ilia"
DEFAULT_PASSWORD = "begemot"


class PostgresDb:
    """PostgreSQL access layer built on SQLAlchemy."""

    def __init__(
        self,
        dbname: str,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        user: str = DEFAULT_USER,
        password: str = DEFAULT_PASSWORD,
        pool_size: int = 5,
        max_overflow: int = 0,
        echo: bool = False,
    ):
        self.dbname = dbname
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        self.engine: Engine = create_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            echo=echo,
        )
        self._session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def close(self) -> None:
        self.engine.dispose()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Session rolled back")
            raise
        finally:
            session.close()

    def execute(self, query: str, params: Optional[Mapping[str, Any]] = None) -> int:
        """Execute DML/DDL and return affected rowcount."""
        with self.session() as session:
            result = session.execute(text(query), params or {})
            return result.rowcount or 0

    def execute_returning(
        self,
        query: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        limit: Optional[int] = 1,
    ) -> list[dict[str, Any]]:
        """Execute a statement that returns rows (INSERT/UPDATE ... RETURNING)."""
        with self.session() as session:
            result = session.execute(text(query), params or {})
            return self._rows_to_dicts(result, limit=limit)

    def select(
        self,
        query: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        limit: Optional[int] = 1,
    ) -> list[dict[str, Any]]:
        with self.session() as session:
            result = session.execute(text(query), params or {})
            return self._rows_to_dicts(result, limit=limit)

    def select_one(
        self,
        query: str,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        rows = self.select(query, params, limit=1)
        return rows[0] if rows else None

    def select_all(
        self,
        query: str,
        params: Optional[Mapping[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        return self.select(query, params, limit=None)

    @staticmethod
    def _rows_to_dicts(
        result: Result[Any],
        *,
        limit: Optional[int],
    ) -> list[dict[str, Any]]:
        rows: Sequence[Row[Any]] = result.fetchall()
        if limit is not None:
            rows = rows[:limit]
        return [dict(row._mapping) for row in rows]
