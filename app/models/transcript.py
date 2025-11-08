from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from .base import Base


class Transcript(Base):
    """
    A transcript created by a user from audio/video file.
    """

    __tablename__ = "transcripts"
    __table_args__ = (Index("ix_transcripts_user_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    storage_filename = Column(String(500), nullable=False)
    content = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True)
    status = Column(String(50), default="completed", nullable=False)
    
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Transcript id={self.id!r} user_id={self.user_id!r} "
            f"title={self.title!r} status={self.status!r}>"
        )
