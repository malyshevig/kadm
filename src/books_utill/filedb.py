import logging
from typing import Optional

from books_utill.models import File
from books_utill.postgres_db import PostgresDb

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
)


class FileDb(PostgresDb):
    def __init__(self):
        super().__init__("books")

    def create_file(
        self,
        file_id: int,
        name: str,
        file_path: Optional[str],
        file_desc: Optional[str] = None,
        src: str = "tg",
    ) -> File:
        with self.session() as session:
            existing = session.get(File, file_id)
            if existing is not None:
                session.expunge(existing)
                return existing

            file_row = File(
                id=file_id,
                name=name,
                file_path=file_path,
                description=file_desc,
                src=src,
            )
            session.add(file_row)
            session.flush()
            session.expunge(file_row)
            return file_row

    def check_if_exists(self, file_id: int) -> bool:
        with self.session() as session:
            return session.get(File, file_id) is not None

    def get_file_by_id(self, file_id: int) -> Optional[File]:
        with self.session() as session:
            file_row = session.get(File, file_id)
            if file_row is None:
                return None
            session.expunge(file_row)
            return file_row

    def update_isbn_processed(self, file_id: int, isbn_status: str) -> int:
        with self.session() as session:
            file_row = session.get(File, file_id)
            if file_row is None:
                return 0
            file_row.process_isbn = isbn_status
            return 1
