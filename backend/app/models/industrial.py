"""CineForge industrial workflow persistence models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin


class CineForgeWorkflowState(Base, TimestampMixin):
    """Persist the editable CineForge workflow ledger inside Jellyfish."""

    __tablename__ = "cineforge_workflow_states"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="工作流状态 ID")
    project_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Jellyfish 项目 ID",
    )
    chapter_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="可选章节 ID；为空表示项目级工作流",
    )
    workflow_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="cineforge_ai_drama_os",
        index=True,
        comment="工作流类型",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        index=True,
        comment="工作流整体状态",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="每次编辑或重生成都会递增的版本号",
    )
    stage_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="各阶段结构化状态、产物、策略与人工编辑补丁",
    )
    stage_status: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="各阶段状态、证据与版本",
    )
    edit_log: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="人工编辑历史",
    )
    regenerate_log: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="重生成任务历史",
    )
    last_task_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="最近一次编辑或重生成对应的任务 ID",
    )

    __table_args__ = (
        Index("ix_cineforge_workflow_project_chapter", "project_id", "chapter_id"),
        Index("ix_cineforge_workflow_key_updated", "workflow_key", "updated_at"),
    )
