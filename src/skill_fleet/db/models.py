"""
Skills-Fleet Database Models.

SQLAlchemy models for the skills fleet database schema.
These models map to the PostgreSQL tables defined in migrations/001_init_skills_schema.sql
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# =============================================================================
# ENUM TYPES (as Python enums)
# =============================================================================


class SkillStatusEnum:
    """Skill lifecycle status values."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class SkillTypeEnum:
    """Skill category/type classification."""

    COGNITIVE = "cognitive"
    TECHNICAL = "technical"
    DOMAIN = "domain"
    TOOL = "tool"
    MCP = "mcp"
    SPECIALIZATION = "specialization"
    TASK_FOCUS = "task_focus"
    MEMORY = "memory"


class SkillWeightEnum:
    """Skill resource weight/complexity level."""

    LIGHTWEIGHT = "lightweight"
    MEDIUM = "medium"
    HEAVYWEIGHT = "heavyweight"


class LoadPriorityEnum:
    """Skill loading priority strategy."""

    ALWAYS = "always"
    TASK_SPECIFIC = "task_specific"
    ON_DEMAND = "on_demand"
    DORMANT = "dormant"


class SkillStyleEnum:
    """Skill structural style pattern."""

    NAVIGATION_HUB = "navigation_hub"
    COMPREHENSIVE = "comprehensive"
    MINIMAL = "minimal"


class DependencyTypeEnum:
    """Dependency relationship type."""

    REQUIRED = "required"
    RECOMMENDED = "recommended"
    CONFLICT = "conflict"


class JobStatusEnum:
    """Background job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PENDING_HITL = "pending_hitl"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HITLTypeEnum:
    """Human-in-the-loop interaction type."""

    CLARIFY = "clarify"
    CONFIRM = "confirm"
    PREVIEW = "preview"
    VALIDATE = "validate"
    DEEP_UNDERSTANDING = "deep_understanding"
    TDD_RED = "tdd_red"
    TDD_GREEN = "tdd_green"
    TDD_REFACTOR = "tdd_refactor"


class ChecklistPhaseEnum:
    """TDD checklist phase."""

    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"


class ConversationStateEnum:
    """Conversation workflow states for session persistence."""

    EXPLORING = "EXPLORING"
    DEEP_UNDERSTANDING = "DEEP_UNDERSTANDING"
    MULTI_SKILL_DETECTED = "MULTI_SKILL_DETECTED"
    CONFIRMING = "CONFIRMING"
    READY = "READY"
    CREATING = "CREATING"
    TDD_RED_PHASE = "TDD_RED_PHASE"
    TDD_GREEN_PHASE = "TDD_GREEN_PHASE"
    TDD_REFACTOR_PHASE = "TDD_REFACTOR_PHASE"
    REVIEWING = "REVIEWING"
    REVISING = "REVISING"
    CHECKLIST_COMPLETE = "CHECKLIST_COMPLETE"
    COMPLETE = "COMPLETE"


class ValidationStatusEnum:
    """Skill validation result status."""

    PASSED = "passed"
    FAILED = "failed"
    WARNINGS = "warnings"


class SeverityEnum:
    """Issue or diagnostic severity level."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class FileTypeEnum:
    """Attached file classification type."""

    REFERENCE = "reference"
    GUIDE = "guide"
    TEMPLATE = "template"
    SCRIPT = "script"
    EXAMPLE = "example"
    ASSET = "asset"
    TEST = "test"


# =============================================================================
# CORE TABLES
# =============================================================================


class Skill(Base):
    """
    Primary skills table.
    Represents a single skill with its metadata, content, and classification.
    """

    __tablename__ = "skills"

    # Primary key
    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identity
    skill_path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Versioning
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    parent_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("skills.skill_id"), nullable=True
    )

    # Classification
    type: Mapped[str] = mapped_column(
        Enum(
            SkillTypeEnum.COGNITIVE,
            SkillTypeEnum.TECHNICAL,
            SkillTypeEnum.DOMAIN,
            SkillTypeEnum.TOOL,
            SkillTypeEnum.MCP,
            SkillTypeEnum.SPECIALIZATION,
            SkillTypeEnum.TASK_FOCUS,
            SkillTypeEnum.MEMORY,
            name="skill_type_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    weight: Mapped[str] = mapped_column(
        Enum(
            SkillWeightEnum.LIGHTWEIGHT,
            SkillWeightEnum.MEDIUM,
            SkillWeightEnum.HEAVYWEIGHT,
            name="skill_weight_enum",
            create_constraint=True,
        ),
        nullable=False,
        default=SkillWeightEnum.MEDIUM,
    )
    load_priority: Mapped[str] = mapped_column(
        Enum(
            LoadPriorityEnum.ALWAYS,
            LoadPriorityEnum.TASK_SPECIFIC,
            LoadPriorityEnum.ON_DEMAND,
            LoadPriorityEnum.DORMANT,
            name="load_priority_enum",
            create_constraint=True,
        ),
        nullable=False,
        default=LoadPriorityEnum.TASK_SPECIFIC,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            SkillStatusEnum.DRAFT,
            SkillStatusEnum.ACTIVE,
            SkillStatusEnum.DEPRECATED,
            SkillStatusEnum.ARCHIVED,
            name="skill_status_enum",
            create_constraint=True,
        ),
        nullable=False,
        default=SkillStatusEnum.DRAFT,
    )
    skill_style: Mapped[str | None] = mapped_column(
        Enum(
            SkillStyleEnum.NAVIGATION_HUB,
            SkillStyleEnum.COMPREHENSIVE,
            SkillStyleEnum.MINIMAL,
            name="skill_style_enum",
            create_constraint=True,
        ),
        nullable=True,
    )

    # Content
    skill_content: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Evolution tracking
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    integrity_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Performance metadata
    performance_stats: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # Relationships
    capabilities: Mapped[list["Capability"]] = relationship(
        "Capability", back_populates="skill", cascade="all, delete-orphan"
    )
    dependencies_as_dependent: Mapped[list["SkillDependency"]] = relationship(
        "SkillDependency",
        foreign_keys="SkillDependency.dependent_id",
        back_populates="dependent",
        cascade="all, delete-orphan",
    )
    dependencies_as_dependency: Mapped[list["SkillDependency"]] = relationship(
        "SkillDependency",
        foreign_keys="SkillDependency.dependency_skill_id",
        back_populates="dependency_skill",
        cascade="all, delete-orphan",
    )
    files: Mapped[list["SkillFile"]] = relationship(
        "SkillFile", back_populates="skill", cascade="all, delete-orphan"
    )
    keywords: Mapped[list["SkillKeyword"]] = relationship(
        "SkillKeyword", back_populates="skill", cascade="all, delete-orphan"
    )
    tags: Mapped[list["SkillTag"]] = relationship(
        "SkillTag", back_populates="skill", cascade="all, delete-orphan"
    )
    categories: Mapped[list["SkillCategory"]] = relationship(
        "SkillCategory", back_populates="skill", cascade="all, delete-orphan"
    )
    aliases: Mapped[list["SkillAlias"]] = relationship(
        "SkillAlias", back_populates="skill", cascade="all, delete-orphan"
    )
    facets: Mapped[list["SkillFacet"]] = relationship(
        "SkillFacet", back_populates="skill", cascade="all, delete-orphan"
    )
    allowed_tools: Mapped[list["SkillAllowedTool"]] = relationship(
        "SkillAllowedTool", back_populates="skill", cascade="all, delete-orphan"
    )
    validation_reports: Mapped[list["ValidationReport"]] = relationship(
        "ValidationReport", back_populates="skill", cascade="all, delete-orphan"
    )
    test_coverage: Mapped[list["SkillTestCoverage"]] = relationship(
        "SkillTestCoverage", back_populates="skill", cascade="all, delete-orphan"
    )
    usage_events: Mapped[list["UsageEvent"]] = relationship("UsageEvent", back_populates="skill")

    # Parent version relationship
    parent_version: Mapped[Optional["Skill"]] = relationship(
        "Skill", remote_side=[skill_id], backref="child_versions"
    )

    # Indexes
    __table_args__ = (
        Index("idx_skills_path", "skill_path"),
        Index("idx_skills_status", "status"),
        Index("idx_skills_type", "type"),
        Index("idx_skills_version_lookup", "skill_path", "version"),
        Index("idx_skills_parent_version", "parent_version_id"),
        Index("idx_skills_created_at", "created_at"),
        Index("idx_skills_published_at", "published_at"),
        Index("idx_skills_status_type", "status", "type"),
        Index("idx_skills_status_priority", "status", "load_priority"),
        CheckConstraint("skill_path ~ '^[a-z0-9_-]+(?:/[a-z0-9_-]+)*$'", name="skill_path_format"),
        CheckConstraint("name ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="name_kebab_case"),
        CheckConstraint("version ~ '^\\d+\\.\\d+\\.\\d+$'", name="version_format"),
    )

    def __repr__(self) -> str:
        return (
            f"<Skill(skill_id={self.skill_id}, skill_path='{self.skill_path}', name='{self.name}')>"
        )


# =============================================================================
# TAXONOMY & ORGANIZATION
# =============================================================================


class TaxonomyCategory(Base):
    """Hierarchical category organization for skills."""

    __tablename__ = "taxonomy_categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("taxonomy_categories.category_id"), nullable=True
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    parent: Mapped[Optional["TaxonomyCategory"]] = relationship(
        "TaxonomyCategory", remote_side=[category_id], backref="children"
    )
    skills: Mapped[list["SkillCategory"]] = relationship(
        "SkillCategory", back_populates="category", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_taxonomy_path", "path"),
        Index("idx_taxonomy_parent", "parent_id"),
        Index("idx_taxonomy_level", "level"),
        CheckConstraint("parent_id IS NULL OR parent_id != category_id", name="category_no_loop"),
    )

    def __repr__(self) -> str:
        return f"<TaxonomyCategory(category_id={self.category_id}, path='{self.path}')>"


class TaxonomyClosure(Base):
    """Closure table for efficient tree queries on taxonomy."""

    __tablename__ = "taxonomy_closure"

    ancestor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxonomy_categories.category_id", ondelete="CASCADE"), primary_key=True
    )
    descendant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxonomy_categories.category_id", ondelete="CASCADE"), primary_key=True
    )
    depth: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)

    __table_args__ = (
        Index("idx_taxonomy_closure_ancestor", "ancestor_id"),
        Index("idx_taxonomy_closure_descendant", "descendant_id"),
        Index("idx_taxonomy_closure_depth", "depth"),
    )


class SkillCategory(Base):
    """Many-to-many relationship between skills and categories."""

    __tablename__ = "skill_categories"

    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxonomy_categories.category_id", ondelete="CASCADE"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="categories")
    category: Mapped["TaxonomyCategory"] = relationship("TaxonomyCategory", back_populates="skills")

    __table_args__ = (
        Index("idx_skill_categories_skill", "skill_id"),
        Index("idx_skill_categories_category", "category_id"),
        Index("idx_skill_categories_primary", "is_primary"),
    )


class SkillAlias(Base):
    """Legacy path support for skills."""

    __tablename__ = "skill_aliases"

    alias_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False
    )
    alias_path: Mapped[str] = mapped_column(String(512), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="aliases")

    __table_args__ = (
        Index("idx_skill_aliases_path", "alias_path"),
        Index("idx_skill_aliases_skill", "skill_id"),
        CheckConstraint(
            "alias_path ~ '^[a-z0-9_.-]+(?:/[a-z0-9_.-]+)*$'", name="alias_path_format"
        ),
    )


class SkillFacet(Base):
    """Multi-dimensional filtering for skills."""

    __tablename__ = "skill_facets"

    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    facet_key: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    facet_value: Mapped[str] = mapped_column(String(256), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="facets")

    __table_args__ = (
        Index("idx_skill_facets_key_value", "facet_key", "facet_value"),
        Index("idx_skill_facets_skill", "skill_id"),
    )


class FacetDefinition(Base):
    """Facet lookup table for validation."""

    __tablename__ = "facet_definitions"

    facet_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    allowed_values: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# =============================================================================
# CAPABILITIES & DEPENDENCIES
# =============================================================================


class Capability(Base):
    """What skills can do - discrete capabilities."""

    __tablename__ = "capabilities"

    capability_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    test_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="capabilities")

    __table_args__ = (
        Index("idx_capabilities_skill", "skill_id"),
        Index("idx_capabilities_name", "name"),
    )


class SkillDependency(Base):
    """Skill dependency graph."""

    __tablename__ = "skill_dependencies"

    dependency_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dependent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False
    )
    dependency_skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False
    )
    dependency_type: Mapped[str] = mapped_column(
        Enum(
            DependencyTypeEnum.REQUIRED,
            DependencyTypeEnum.RECOMMENDED,
            DependencyTypeEnum.CONFLICT,
            name="dependency_type_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    dependent: Mapped["Skill"] = relationship(
        "Skill", foreign_keys=[dependent_id], back_populates="dependencies_as_dependent"
    )
    dependency_skill: Mapped["Skill"] = relationship(
        "Skill", foreign_keys=[dependency_skill_id], back_populates="dependencies_as_dependency"
    )

    __table_args__ = (
        Index("idx_dependencies_dependent", "dependent_id"),
        Index("idx_dependencies_dependency", "dependency_skill_id"),
        Index("idx_dependencies_type", "dependency_type"),
        CheckConstraint("dependent_id != dependency_skill_id", name="no_self_dependency"),
    )


class DependencyClosure(Base):
    """Closure table for dependency graph traversal."""

    __tablename__ = "dependency_closure"

    ancestor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id"), primary_key=True
    )
    descendant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id"), primary_key=True
    )
    min_depth: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    dependency_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    __table_args__ = (
        Index("idx_dependency_closure_ancestor", "ancestor_id"),
        Index("idx_dependency_closure_descendant", "descendant_id"),
    )


class SkillReference(Base):
    """Cross-references between skills (see also)."""

    __tablename__ = "skill_references"

    source_skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    target_skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    reference_type: Mapped[str] = mapped_column(String(32), nullable=False, default="see_also")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_skill_references_source", "source_skill_id"),
        Index("idx_skill_references_target", "target_skill_id"),
        CheckConstraint("source_skill_id != target_skill_id", name="no_self_reference"),
    )


# =============================================================================
# DISCOVERY & SEARCH
# =============================================================================


class SkillKeyword(Base):
    """Search terms for skills."""

    __tablename__ = "skill_keywords"

    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    keyword: Mapped[str] = mapped_column(String(128), primary_key=True, nullable=False)
    weight: Mapped[float] = mapped_column(default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="keywords")

    __table_args__ = (
        Index("idx_skill_keywords_keyword", "keyword"),
        Index("idx_skill_keywords_skill", "skill_id"),
    )


class SkillTag(Base):
    """User-defined tags for skills."""

    __tablename__ = "skill_tags"

    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="tags")

    __table_args__ = (
        Index("idx_skill_tags_tag", "tag"),
        Index("idx_skill_tags_skill", "skill_id"),
    )


class TagStats(Base):
    """Tag popularity tracking."""

    __tablename__ = "tag_stats"

    tag: Mapped[str] = mapped_column(String(64), primary_key=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# =============================================================================
# SKILL FILES & ASSETS
# =============================================================================


class SkillFile(Base):
    """Associated files and resources for skills."""

    __tablename__ = "skill_files"

    file_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        Enum(
            FileTypeEnum.REFERENCE,
            FileTypeEnum.GUIDE,
            FileTypeEnum.TEMPLATE,
            FileTypeEnum.SCRIPT,
            FileTypeEnum.EXAMPLE,
            FileTypeEnum.ASSET,
            FileTypeEnum.TEST,
            name="file_type_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    binary_data: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="files")

    __table_args__ = (
        Index("idx_skill_files_skill", "skill_id"),
        Index("idx_skill_files_type", "file_type"),
        Index("idx_skill_files_path", "relative_path"),
    )


class SkillAllowedTool(Base):
    """Tools a skill is allowed to use."""

    __tablename__ = "skill_allowed_tools"

    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    tool_name: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="allowed_tools")

    __table_args__ = (
        Index("idx_skill_allowed_tools_tool", "tool_name"),
        Index("idx_skill_allowed_tools_skill", "skill_id"),
    )


# =============================================================================
# JOBS & WORKFLOW
# =============================================================================


class Job(Base):
    """Background job tracking."""

    __tablename__ = "jobs"

    job_id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.uuid_generate_v4())
    status: Mapped[str] = mapped_column(
        Enum(
            JobStatusEnum.PENDING,
            JobStatusEnum.RUNNING,
            JobStatusEnum.PENDING_HITL,
            JobStatusEnum.COMPLETED,
            JobStatusEnum.FAILED,
            JobStatusEnum.CANCELLED,
            name="job_status_enum",
            create_constraint=True,
        ),
        nullable=False,
        default=JobStatusEnum.PENDING,
    )
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, default="skill_creation")
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    user_context: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    task_description_refined: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_phase: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_stack: Mapped[str | None] = mapped_column(Text, nullable=True)
    intended_taxonomy_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    draft_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    promoted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validation_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(
        Enum(
            ValidationStatusEnum.PASSED,
            ValidationStatusEnum.FAILED,
            ValidationStatusEnum.WARNINGS,
            name="validation_status_enum",
            create_constraint=True,
        ),
        nullable=True,
    )
    validation_score: Mapped[float | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    job_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Relationships
    hitl_interactions: Mapped[list["HITLInteraction"]] = relationship(
        "HITLInteraction", back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_user", "user_id"),
        Index("idx_jobs_created_at", "created_at"),
        Index("idx_jobs_type", "job_type"),
        Index("idx_jobs_promoted", "promoted"),
        Index("idx_jobs_polling", "user_id", "created_at"),
    )


class HITLInteraction(Base):
    """Human-in-the-Loop interaction tracking."""

    __tablename__ = "hitl_interactions"

    interaction_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False
    )
    interaction_type: Mapped[str] = mapped_column(
        Enum(
            HITLTypeEnum.CLARIFY,
            HITLTypeEnum.CONFIRM,
            HITLTypeEnum.PREVIEW,
            HITLTypeEnum.VALIDATE,
            HITLTypeEnum.DEEP_UNDERSTANDING,
            HITLTypeEnum.TDD_RED,
            HITLTypeEnum.TDD_GREEN,
            HITLTypeEnum.TDD_REFACTOR,
            name="hitl_type_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    prompt_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    response_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    timeout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hitl_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="hitl_interactions")

    __table_args__ = (
        Index("idx_hitl_job", "job_id"),
        Index("idx_hitl_type", "interaction_type"),
        Index("idx_hitl_status", "status"),
        Index("idx_hitl_created_at", "created_at"),
    )


class DeepUnderstandingState(Base):
    """Extended HITL tracking for deep understanding phase."""

    __tablename__ = "deep_understanding_state"

    state_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    questions_asked: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    answers: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    research_performed: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    understanding_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_goals: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    readiness_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class TDDWorkflowState(Base):
    """Test-driven development workflow tracking."""

    __tablename__ = "tdd_workflow_state"

    state_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    phase: Mapped[str | None] = mapped_column(String(32), nullable=True)
    baseline_tests_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    compliance_tests_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rationalizations_identified: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    checklist_state: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# =============================================================================
# VALIDATION & QUALITY
# =============================================================================


class ValidationReport(Base):
    """Skill validation results."""

    __tablename__ = "validation_reports"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="SET NULL"), nullable=True
    )
    job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum(
            ValidationStatusEnum.PASSED,
            ValidationStatusEnum.FAILED,
            ValidationStatusEnum.WARNINGS,
            name="validation_status_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[float] = mapped_column(Integer, nullable=False)
    errors: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    warnings: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    checks_performed: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Integer, nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(Integer, nullable=True)
    compliance_score: Mapped[float | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped[Optional["Skill"]] = relationship("Skill", back_populates="validation_reports")
    checks: Mapped[list["ValidationCheck"]] = relationship(
        "ValidationCheck", back_populates="report", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_validation_reports_skill", "skill_id"),
        Index("idx_validation_reports_job", "job_id"),
        Index("idx_validation_reports_status", "status"),
        Index("idx_validation_reports_created_at", "created_at"),
    )


class ValidationCheck(Base):
    """Individual validation check items."""

    __tablename__ = "validation_checks"

    check_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("validation_reports.report_id", ondelete="CASCADE"), nullable=False
    )
    check_name: Mapped[str] = mapped_column(String(128), nullable=False)
    check_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        Enum(
            SeverityEnum.CRITICAL,
            SeverityEnum.WARNING,
            SeverityEnum.INFO,
            name="severity_enum",
            create_constraint=True,
        ),
        nullable=False,
        default=SeverityEnum.INFO,
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    report: Mapped["ValidationReport"] = relationship("ValidationReport", back_populates="checks")

    __table_args__ = (
        Index("idx_validation_checks_report", "report_id"),
        Index("idx_validation_checks_severity", "severity"),
        Index("idx_validation_checks_category", "category"),
    )


class SkillTestCoverage(Base):
    """Test coverage tracking for skills."""

    __tablename__ = "skill_test_coverage"

    coverage_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False
    )
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passing_tests: Mapped[int] = mapped_column(Integer, default=0)
    failing_tests: Mapped[int] = mapped_column(Integer, default=0)
    skipped_tests: Mapped[int] = mapped_column(Integer, default=0)
    coverage_percent: Mapped[float | None] = mapped_column(Integer, nullable=True)
    unit_tests: Mapped[int] = mapped_column(Integer, default=0)
    integration_tests: Mapped[int] = mapped_column(Integer, default=0)
    e2e_tests: Mapped[int] = mapped_column(Integer, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="test_coverage")

    __table_args__ = (
        Index("idx_test_coverage_skill", "skill_id"),
        Index("idx_test_coverage_created_at", "created_at"),
    )


# =============================================================================
# ANALYTICS & USAGE TRACKING
# =============================================================================


class UsageEvent(Base):
    """Skill usage tracking events."""

    __tablename__ = "usage_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.skill_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    task_id: Mapped[UUID | None] = mapped_column(nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_id: Mapped[UUID | None] = mapped_column(nullable=True)
    event_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="usage_events")

    __table_args__ = (
        Index("idx_usage_events_skill", "skill_id"),
        Index("idx_usage_events_user", "user_id"),
        Index("idx_usage_events_occurred_at", "occurred_at"),
        Index("idx_usage_events_task", "task_id"),
        Index("idx_usage_events_skill_time", "skill_id", "occurred_at"),
    )


class OptimizationJob(Base):
    """DSPy optimization job tracking."""

    __tablename__ = "optimization_jobs"

    job_id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.uuid_generate_v4())
    optimizer: Mapped[str] = mapped_column(String(64), nullable=False)
    auto_config: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    max_bootstrapped_demos: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    max_labeled_demos: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    trainset_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    training_skills: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    result_score: Mapped[float | None] = mapped_column(Integer, nullable=True)
    optimized_program_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    training_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validation_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_stack: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_optimization_jobs_status", "status"),
        Index("idx_optimization_jobs_created_at", "created_at"),
        Index("idx_optimization_jobs_optimizer", "optimizer"),
    )


# =============================================================================
# CONVERSATION SESSIONS
# =============================================================================


class ConversationSession(Base):
    """
    Database-backed conversation session storage.

    Replaces the in-memory _sessions dict in conversational router.
    Persists conversation state across server restarts.
    """

    __tablename__ = "conversation_sessions"

    # Primary key
    session_id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid()
    )

    # User context
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")

    # Workflow state
    state: Mapped[str] = mapped_column(
        Enum(
            ConversationStateEnum.EXPLORING,
            ConversationStateEnum.DEEP_UNDERSTANDING,
            ConversationStateEnum.MULTI_SKILL_DETECTED,
            ConversationStateEnum.CONFIRMING,
            ConversationStateEnum.READY,
            ConversationStateEnum.CREATING,
            ConversationStateEnum.TDD_RED_PHASE,
            ConversationStateEnum.TDD_GREEN_PHASE,
            ConversationStateEnum.TDD_REFACTOR_PHASE,
            ConversationStateEnum.REVIEWING,
            ConversationStateEnum.REVISING,
            ConversationStateEnum.CHECKLIST_COMPLETE,
            ConversationStateEnum.COMPLETE,
            name="conversation_state_enum",
            create_constraint=True,
        ),
        nullable=False,
        default=ConversationStateEnum.EXPLORING,
    )
    task_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    taxonomy_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Multi-skill support
    multi_skill_queue: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), server_default=text("'{}'"), nullable=True
    )
    current_skill_index: Mapped[int] = mapped_column(Integer, default=0)

    # Conversation data (JSONB for flexibility)
    messages: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    collected_examples: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))

    # Draft data
    skill_draft: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    skill_metadata_draft: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # TDD workflow
    checklist_state: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Pending confirmations
    pending_confirmation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Deep understanding phase
    deep_understanding: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    current_understanding: Mapped[str | None] = mapped_column(Text, nullable=True)

    # User problem/goals
    user_problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_goals: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Research context
    research_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Session metadata
    session_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Optional job association
    job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_state", "state"),
        Index("idx_sessions_created_at", "created_at"),
        Index("idx_sessions_last_activity", "last_activity_at"),
        Index("idx_sessions_expires_at", "expires_at"),
        Index("idx_sessions_job", "job_id"),
    )

    def __repr__(self) -> str:
        return f"<ConversationSession(session_id={self.session_id}, state='{self.state}')>"
