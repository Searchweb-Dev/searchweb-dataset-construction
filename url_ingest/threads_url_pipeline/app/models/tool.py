from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class ExtractedTool(Base, TimestampMixin):
    """게시글에서 보조적으로 추출한 툴/서비스명 후보를 저장하는 모델."""
    __tablename__ = "extracted_tools"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    post = relationship("Post", back_populates="tools")

    __table_args__ = (
        UniqueConstraint("post_id", "normalized_tool_name", name="uq_extracted_tools_post_normalized_name"),
        Index("ix_extracted_tools_name", "normalized_tool_name"),
    )
