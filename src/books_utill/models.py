from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Dialog(Base):
    __tablename__ = "dialog"

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    msg_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "msg_offset": self.msg_offset,
        }


class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    uuid: Mapped[UUID] = mapped_column(
        Uuid,
        nullable=False,
        unique=True,
        default=uuid4,
    )
    tg_file_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    src: Mapped[str] = mapped_column(String, nullable=False, default="tg")
    process_isbn: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "uuid": str(self.uuid),
            "tg_file_id": self.tg_file_id,
            "name": self.name,
            "file_path": self.file_path,
            "description": self.description,
            "src": self.src,
            "process_isbn": self.process_isbn,
            "created_at": self.created_at,
            "updated_at": self.updated_at,

        }


class Isbn(Base):
    __tablename__ = "isbn"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    isbn: Mapped[str] = mapped_column(String, primary_key=False)
    title: Mapped[str] = mapped_column(String, nullable=True)
    authors: Mapped[Any] = mapped_column(JSONB, nullable=True, default=list)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_uuid: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("file.uuid"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "isbn": self.isbn,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "publisher": self.publisher,
            "file_uuid": str(self.file_uuid),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
