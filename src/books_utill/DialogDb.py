import logging
from typing import Any, Optional

from sqlalchemy import select

from books_utill.models import Dialog
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
        with self.session() as session:
            dialog = session.get(Dialog, channel_id)
            if dialog is None:
                dialog = Dialog(
                    channel_id=channel_id,
                    name=name,
                    msg_offset=offset,
                )
                session.add(dialog)
                session.flush()
            return dialog.to_dict()

    def update_dialog_offset(self, channel_id: int, offset: int) -> int:
        with self.session() as session:
            dialog = session.get(Dialog, channel_id)
            if dialog is None:
                return 0
            dialog.msg_offset = offset
            return 1

    def get_dialog(self, channel_id: int) -> Optional[dict[str, Any]]:
        with self.session() as session:
            dialog = session.get(Dialog, channel_id)
            return dialog.to_dict() if dialog else None

    def find_by_name(self, name: str) -> Optional[dict[str, Any]]:
        with self.session() as session:
            dialog = session.scalars(
                select(Dialog).where(Dialog.name == name).limit(1)
            ).first()
            return dialog.to_dict() if dialog else None
