import logging
import uuid
from typing import Any, Optional, Sequence, Union

from sqlalchemy import select

from books_utill.models import Base, Isbn
from books_utill.postgres_db import PostgresDb

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
)

UuidLike = Union[uuid.UUID, str]


class IsbnDb(PostgresDb):
    def __init__(self):
        super().__init__("books")

    def create_table(self) -> None:
        Base.metadata.create_all(self.engine, tables=[Isbn.__table__])

    def create_isbn(
        self,
        isbn: str,
        title: str,
        authors: Optional[Sequence[Any]] = None,
        year: Optional[int] = None,
        publisher: Optional[str] = None,
        file_uuid: Optional[UuidLike] = None,
    ) -> dict[str, Any]:
        if file_uuid is None:
            raise ValueError("file_uuid is required")

        file_uuid = uuid.UUID(str(file_uuid))
        with self.session() as session:
            existing = session.get(Isbn, isbn)
            if existing is not None:
                return existing.to_dict()

            row = Isbn(
                isbn=isbn,
                title=title,
                authors=list(authors or []),
                year=year,
                publisher=publisher,
                file_uuid=file_uuid,
            )
            session.add(row)
            session.flush()
            return row.to_dict()

    def get_by_isbn(self, isbn: str) -> Optional[dict[str, Any]]:
        with self.session() as session:
            row = session.get(Isbn, isbn)
            return row.to_dict() if row else None

    def get_by_file_uuid(self, file_uuid: UuidLike) -> list[dict[str, Any]]:
        file_uuid = uuid.UUID(str(file_uuid))
        with self.session() as session:
            rows = session.scalars(
                select(Isbn).where(Isbn.file_uuid == file_uuid)
            ).all()
            return [row.to_dict() for row in rows]

    def check_if_exists(self, isbn: str) -> bool:
        with self.session() as session:
            return session.get(Isbn, isbn) is not None
