import logging
import uuid
from typing import Any, Optional, Sequence, Union

from sqlalchemy import select, update

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
    ) -> Isbn:
        if file_uuid is None:
            raise ValueError("file_uuid is required")

        file_uuid = uuid.UUID(str(file_uuid))
        with self.session() as session:
            existing = session.get(Isbn, isbn)
            if existing is not None:
                session.expunge(existing)
                return existing

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
            session.expunge(row)
            return row

    def save_isbns(self, file_uuid:str, items: Sequence[Isbn]) -> list[Isbn]:
        """Save a list of Isbn rows; existing ISBN keys are left unchanged."""
        if not items:
            return []

        result: list[Isbn] = []
        with self.session() as session:
            for item in items:

                row = Isbn(
                    isbn=item,
                    title=None,
                    authors=None,
                    year=None,
                    publisher=None,
                    file_uuid=uuid.UUID(str(item.file_uuid)),
                )
                session.add(row)
                session.flush()
                session.expunge(row)
                result.append(row)

        return result

    def get_by_isbn(self, isbn: str) -> Optional[Isbn]:
        with self.session() as session:
            row = session.get(Isbn, isbn)
            if row is None:
                return None
            session.expunge(row)
            return row

    def get_by_file_uuid(self, file_uuid: UuidLike) -> list[Isbn]:
        file_uuid = uuid.UUID(str(file_uuid))
        with self.session() as session:
            rows = session.scalars(
                select(Isbn).where(Isbn.file_uuid == file_uuid)
            ).all()
            result = list(rows)
            for row in result:
                session.expunge(row)
            return result

    def check_if_exists(self, isbn: str) -> bool:
        with self.session() as session:
            return session.get(Isbn, isbn) is not None

    def save_isbn_info(self,  isbn_info):
        with self.session() as session:
            stmt = (
                update("isbn").
                where("isbn.isbn" == isbn_info["isbn"]).
                values(fullname="Patrick the Star")
            )
            return row
        pass


