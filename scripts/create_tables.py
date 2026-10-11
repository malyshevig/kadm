#!/usr/bin/env python3
"""Create PostgreSQL tables: dialog, file, isbn."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from books_utill.models import Base, Dialog, File, Isbn  # noqa: E402
from books_utill.postgres_db import (  # noqa: E402
    DEFAULT_HOST,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_USER,
    PostgresDb,
)

logger = logging.getLogger(__name__)

# file before isbn (FK file.uuid)
TABLES = (
    Dialog.__table__,
    File.__table__,
    Isbn.__table__,
)


def create_tables(
    dbname: str = "books",
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    user: str = DEFAULT_USER,
    password: str = DEFAULT_PASSWORD,
) -> list[str]:
    db = PostgresDb(
        dbname,
        host=host,
        port=port,
        user=user,
        password=password,
    )
    try:
        Base.metadata.create_all(db.engine, tables=list(TABLES))
        return [table.name for table in TABLES]
    finally:
        db.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Create PostgreSQL tables dialog, file, isbn"
    )
    parser.add_argument("--dbname", default="books")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    args = parser.parse_args()

    tables = create_tables(
        args.dbname,
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
    )
    logger.info("Tables ready: %s", ", ".join(tables))


if __name__ == "__main__":
    main()
