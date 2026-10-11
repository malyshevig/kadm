import logging
from typing import Any, Optional

from books_utill.postgres_db import PostgresDb

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
)


class DialogDb(PostgresDb):
    def __init__(self):
        super().__init__("books")

    def create_dialog_if_not_exists(
        self,
        channel_id: int,
        name: str,
        offset: int = 0,
    ) -> dict[str, Any]:
        existing = self.select_one(
            "SELECT channel_id, name, msg_offset FROM dialog "
            "WHERE channel_id = :channel_id",
            {"channel_id": channel_id},
        )
        if existing is not None:
            return existing

        rows = self.execute_returning(
            "INSERT INTO dialog (channel_id, name, msg_offset) "
            "VALUES (:channel_id, :name, :msg_offset) "
            "RETURNING channel_id, name, msg_offset",
            {
                "channel_id": channel_id,
                "name": name,
                "msg_offset": offset,
            },
        )
        return rows[0]

    def update_dialog_offset(self, channel_id: int, offset: int) -> int:
        return self.execute(
            "UPDATE dialog SET msg_offset = :msg_offset "
            "WHERE channel_id = :channel_id",
            {"msg_offset": offset, "channel_id": channel_id},
        )

    def get_dialog(self, channel_id: int) -> Optional[dict[str, Any]]:
        return self.select_one(
            "SELECT channel_id, name, msg_offset FROM dialog "
            "WHERE channel_id = :channel_id",
            {"channel_id": channel_id},
        )

    def find_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return self.select_one(
            "SELECT channel_id, name, msg_offset FROM dialog "
            "WHERE name = :name",
            {"name": name},
        )
