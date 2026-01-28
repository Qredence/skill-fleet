"""
Skills-Fleet Database Repositories.

Repository layer for common CRUD operations on skills fleet entities.
"""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from .models import (
    Capability,
    ConversationSession,
    ConversationStateEnum,
    HITLInteraction,
    Job,
    Skill,
    SkillAllowedTool,
    SkillCategory,
    SkillDependency,
    SkillKeyword,
    SkillStatusEnum,
    SkillTag,
    TaxonomyCategory,
    TaxonomyClosure,
    UsageEvent,
    ValidationReport,
)

ModelType = TypeVar("ModelType", bound=Any)


class BaseRepository(Generic[ModelType]):  # noqa: UP046
    """Base repository with common CRUD operations."""

    def __init__(self, model: type[ModelType], db: Session):
        """Initialize the base repository.

        Args:
            model: The model class for this repository.
            db: The database session.
        """
        self.model = model
        self.db = db

    def get(self, id: int) -> ModelType | None:
        """Get a single entity by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        order_desc: bool = False,
        **filters: Any,
    ) -> list[ModelType]:
        """
        Get multiple entities with optional filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by
            order_desc: Whether to order in descending order
            **filters: Filter parameters (field=value)

        """
        query = self.db.query(self.model)

        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            query = query.order_by(desc(order_column) if order_desc else asc(order_column))

        # Apply pagination
        return query.offset(skip).limit(limit).all()

    def create(self, *, obj_in: dict) -> ModelType:
        """Create a new entity."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, *, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Update an existing entity."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, *, id: int) -> ModelType | None:
        """Delete an entity by ID."""
        obj = self.db.get(self.model, id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj

    def count(self, **filters: Any) -> int:
        """Count entities matching filters."""
        query = self.db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)
        return query.count()


class SkillRepository(BaseRepository[Skill]):
    """Repository for Skill entity."""

    def __init__(self, db: Session):
        """Initialize the skill repository.

        Args:
            db: The database session.
        """
        super().__init__(Skill, db)

    def get_by_path(self, skill_path: str) -> Skill | None:
        """Get a skill by its path."""
        return self.db.query(Skill).filter(Skill.skill_path == skill_path).first()

    def get_by_path_with_relations(
        self,
        skill_path: str,
        load_capabilities: bool = True,
        load_dependencies: bool = True,
        load_keywords: bool = True,
        load_tags: bool = True,
    ) -> Skill | None:
        """Get a skill by path with specified relations loaded."""
        query = self.db.query(Skill).filter(Skill.skill_path == skill_path)

        if load_capabilities:
            query = query.options(joinedload(Skill.capabilities))
        if load_dependencies:
            query = query.options(
                joinedload(Skill.dependencies_as_dependent).joinedload(
                    SkillDependency.dependency_skill
                )
            )
        if load_keywords:
            query = query.options(joinedload(Skill.keywords))
        if load_tags:
            query = query.options(joinedload(Skill.tags))

        return query.first()

    def search(
        self,
        *,
        query: str,
        status: str | None = SkillStatusEnum.ACTIVE,
        skill_type: str | None = None,
        weight: str | None = None,
        limit: int = 20,
    ) -> list[Skill]:
        """
        Full-text search for skills.

        Uses PostgreSQL full-text search on the search_vector column.
        """
        from sqlalchemy import func

        # Build search query
        search_query = self.db.query(Skill)

        # Apply status filter
        if status:
            search_query = search_query.filter(Skill.status == status)

        # Apply type filter
        if skill_type:
            search_query = search_query.filter(Skill.type == skill_type)

        # Apply weight filter
        if weight:
            search_query = search_query.filter(Skill.weight == weight)

        # Apply full-text search
        if query:
            # Use PostgreSQL's tsvector for full-text search
            search_query = search_query.filter(
                Skill.search_vector.op("@@")(func.plainto_tsquery("english", query))
            )

        # Order by relevance and limit
        return (
            search_query.order_by(
                func.ts_rank(Skill.search_vector, func.plainto_tsquery("english", query)).desc()
            )
            .limit(limit)
            .all()
        )

    def get_active_skills(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        type: str | None = None,
    ) -> list[Skill]:
        """Get all active (published) skills."""
        query = self.db.query(Skill).filter(Skill.status == SkillStatusEnum.ACTIVE)

        if type:
            query = query.filter(Skill.type == type)

        return query.order_by(Skill.name).offset(skip).limit(limit).all()

    def get_dependent_skills(self, skill_id: int) -> list[Skill]:
        """Get all skills that depend on this skill."""
        return (
            self.db.query(Skill)
            .join(SkillDependency, Skill.skill_id == SkillDependency.dependent_id)
            .filter(SkillDependency.dependency_skill_id == skill_id)
            .all()
        )

    def get_dependency_tree(self, skill_id: int) -> dict:
        """
        Get the full dependency tree for a skill.

        Returns a dict with 'dependencies' (what this skill needs)
        and 'dependents' (what needs this skill).
        """
        # First get the skill to find its path
        skill = self.get(skill_id)
        if not skill:
            return {"dependencies": [], "dependents": []}

        # Now get with relations using the path
        skill = self.get_by_path_with_relations(skill.skill_path, load_dependencies=True)
        if not skill:
            return {"dependencies": [], "dependents": []}

        dependencies = []
        for dep in skill.dependencies_as_dependent:
            dependencies.append(
                {
                    "skill_path": dep.dependency_skill.skill_path,
                    "name": dep.dependency_skill.name,
                    "type": dep.dependency_type,
                    "justification": dep.justification,
                }
            )

        dependents = []
        for dep in self.get_dependent_skills(skill_id):
            dependents.append(
                {
                    "skill_path": dep.skill_path,
                    "name": dep.name,
                }
            )

        return {"dependencies": dependencies, "dependents": dependents}

    def create_with_relations(
        self,
        *,
        skill_data: dict,
        capabilities: list[dict] | None = None,
        dependencies: list[dict] | None = None,
        keywords: list[str] | None = None,
        tags: list[str] | None = None,
        allowed_tools: list[str] | None = None,
    ) -> Skill:
        """Create a skill with its relations in a single transaction."""
        # Create skill
        skill = self.create(obj_in=skill_data)

        # Add capabilities
        if capabilities:
            for cap_data in capabilities:
                cap_data["skill_id"] = skill.skill_id
                self.db.add(Capability(**cap_data))

        # Add dependencies
        if dependencies:
            for dep_data in dependencies:
                dep_data["dependent_id"] = skill.skill_id
                self.db.add(SkillDependency(**dep_data))

        # Add keywords
        if keywords:
            for keyword in keywords:
                self.db.add(SkillKeyword(skill_id=skill.skill_id, keyword=keyword))

        # Add tags
        if tags:
            for tag in tags:
                self.db.add(SkillTag(skill_id=skill.skill_id, tag=tag))

        # Add allowed tools
        if allowed_tools:
            for tool in allowed_tools:
                self.db.add(SkillAllowedTool(skill_id=skill.skill_id, tool_name=tool))

        self.db.commit()
        self.db.refresh(skill)
        return skill

    def publish(self, skill_id: int) -> Skill | None:
        """Publish a skill (change status to active)."""
        skill = self.get(skill_id)
        if skill:
            skill.status = SkillStatusEnum.ACTIVE
            skill.published_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(skill)
        return skill

    def deprecate(self, skill_id: int) -> Skill | None:
        """Deprecate a skill."""
        skill = self.get(skill_id)
        if skill:
            skill.status = SkillStatusEnum.DEPRECATED
            self.db.commit()
            self.db.refresh(skill)
        return skill


class JobRepository(BaseRepository[Job]):
    """Repository for Job entity."""

    def __init__(self, db: Session):
        """Initialize the job repository.

        Args:
            db: The database session.
        """
        super().__init__(Job, db)

    def get_by_id(self, job_id: Any) -> Job | None:
        """
        Get a job by its ID (UUID).

        Args:
            job_id: UUID of the job

        Returns:
            Job instance or None if not found

        """
        from uuid import UUID

        if isinstance(job_id, str):
            job_id = UUID(job_id)
        return self.db.query(Job).filter(Job.job_id == job_id).first()

    def get_by_status(self, status: str, *, limit: int = 100) -> list[Job]:
        """
        Get all jobs with a specific status.

        Args:
            status: Job status (pending, running, pending_hitl, completed, failed, cancelled)
            limit: Maximum number of jobs to return

        Returns:
            List of Job instances

        """
        return (
            self.db.query(Job)
            .filter(Job.status == status)
            .order_by(Job.created_at.asc())
            .limit(limit)
            .all()
        )

    def get_by_user(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
    ) -> list[Job]:
        """Get jobs for a specific user."""
        query = self.db.query(Job).filter(Job.user_id == user_id)

        if status:
            query = query.filter(Job.status == status)

        return query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    def get_pending_hitl(self, *, limit: int = 10) -> list[Job]:
        """Get jobs that are waiting for human input."""
        return (
            self.db.query(Job)
            .filter(Job.status == "pending_hitl")
            .order_by(Job.created_at.asc())
            .limit(limit)
            .all()
        )

    def update_status(self, job_id: str, status: str, **updates: Any) -> Job | None:
        """Update job status and optionally other fields."""
        job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = status
            for key, value in updates.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            self.db.commit()
            self.db.refresh(job)
        return job

    def add_hitl_interaction(
        self,
        job_id: str,
        interaction_type: str,
        prompt_data: dict,
    ) -> HITLInteraction:
        """Add a HITL interaction to a job."""
        interaction = HITLInteraction(
            job_id=job_id,
            interaction_type=interaction_type,
            prompt_data=prompt_data,
        )
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def complete_job(self, job_id: str, result: dict) -> Job | None:
        """Mark a job as completed with result."""
        job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = "completed"
            job.result = result
            job.completed_at = datetime.now(UTC)
            job.progress_percent = 100
            self.db.commit()
            self.db.refresh(job)
        return job


class TaxonomyRepository(BaseRepository[TaxonomyCategory]):
    """Repository for TaxonomyCategory entity."""

    def __init__(self, db: Session):
        """Initialize the taxonomy repository.

        Args:
            db: The database session.
        """
        super().__init__(TaxonomyCategory, db)

    def get_by_path(self, path: str) -> TaxonomyCategory | None:
        """Get a category by its path."""
        return self.db.query(TaxonomyCategory).filter(TaxonomyCategory.path == path).first()

    def get_tree(self, root_path: str | None = None) -> list[dict]:
        """
        Get the taxonomy tree structure.

        Args:
            root_path: Optional path to start from (defaults to root level)

        """
        if root_path:
            root = self.get_by_path(root_path)
            if not root:
                return []
            query = self.db.query(TaxonomyCategory).filter(
                TaxonomyCategory.parent_id == root.category_id
            )
        else:
            query = self.db.query(TaxonomyCategory).filter(TaxonomyCategory.parent_id.is_(None))

        categories = query.order_by(TaxonomyCategory.sort_order).all()

        result = []
        for cat in categories:
            result.append(
                {
                    "category_id": cat.category_id,
                    "path": cat.path,
                    "name": cat.name,
                    "description": cat.description,
                    "level": cat.level,
                    "children": self._get_children(cat.category_id),
                }
            )

        return result

    def _get_children(self, parent_id: int) -> list[dict]:
        """Recursively get child categories."""
        children = (
            self.db.query(TaxonomyCategory)
            .filter(TaxonomyCategory.parent_id == parent_id)
            .order_by(TaxonomyCategory.sort_order)
            .all()
        )

        result = []
        for cat in children:
            result.append(
                {
                    "category_id": cat.category_id,
                    "path": cat.path,
                    "name": cat.name,
                    "description": cat.description,
                    "level": cat.level,
                    "children": self._get_children(cat.category_id),
                }
            )

        return result

    def get_skills_in_category(self, category_id: int) -> list[Skill]:
        """Get all skills in a category (including subcategories)."""
        # Get all descendant category IDs using closure table

        descendant_ids = (
            self.db.query(TaxonomyClosure.descendant_id)
            .filter(TaxonomyClosure.ancestor_id == category_id)
            .all()
        )
        category_ids = [cat_id for (cat_id,) in descendant_ids]

        # Get skills in these categories
        skills = (
            self.db.query(Skill)
            .join(SkillCategory)
            .filter(SkillCategory.category_id.in_(category_ids))
            .all()
        )

        return skills


class ValidationRepository(BaseRepository[ValidationReport]):
    """Repository for ValidationReport entity."""

    def __init__(self, db: Session):
        """Initialize the validation repository.

        Args:
            db: The database session.
        """
        super().__init__(ValidationReport, db)

    def get_latest_for_skill(self, skill_id: int) -> ValidationReport | None:
        """Get the latest validation report for a skill."""
        return (
            self.db.query(ValidationReport)
            .filter(ValidationReport.skill_id == skill_id)
            .order_by(ValidationReport.created_at.desc())
            .first()
        )

    def get_failed_validations(self, *, limit: int = 50) -> list[ValidationReport]:
        """Get all failed validation reports."""
        return (
            self.db.query(ValidationReport)
            .filter(ValidationReport.status == "failed")
            .order_by(ValidationReport.created_at.desc())
            .limit(limit)
            .all()
        )


class UsageRepository:
    """Repository for usage analytics."""

    def __init__(self, db: Session):
        """Initialize the usage repository.

        Args:
            db: The database session.
        """
        self.db = db

    def record_usage(
        self,
        skill_id: int,
        user_id: str,
        *,
        success: bool = True,
        duration_ms: int | None = None,
        error_type: str | None = None,
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> UsageEvent:
        """Record a skill usage event."""
        event = UsageEvent(
            skill_id=skill_id,
            user_id=user_id,
            success=success,
            duration_ms=duration_ms,
            error_type=error_type,
            session_id=session_id,
            metadata=metadata or {},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_skill_stats(
        self,
        skill_id: int,
        *,
        days: int = 30,
    ) -> dict:
        """Get usage statistics for a skill."""
        from datetime import timedelta

        from sqlalchemy import func

        since = datetime.now(UTC) - timedelta(days=days)

        stats = (
            self.db.query(
                func.count(UsageEvent.event_id).label("total_uses"),
                func.count(func.distinct(UsageEvent.user_id)).label("unique_users"),
                func.avg(UsageEvent.success.cast("integer")).label("success_rate"),
                func.avg(UsageEvent.duration_ms).label("avg_duration_ms"),
            )
            .filter(
                UsageEvent.skill_id == skill_id,
                UsageEvent.occurred_at >= since,
            )
            .first()
        )

        return {
            "total_uses": stats.total_uses or 0,
            "unique_users": stats.unique_users or 0,
            "success_rate": float(stats.success_rate or 0),
            "avg_duration_ms": float(stats.avg_duration_ms or 0),
        }

    def get_popular_skills(self, *, days: int = 30, limit: int = 20) -> list[dict]:
        """Get the most popular skills by usage."""
        from datetime import timedelta

        from sqlalchemy import desc, func

        since = datetime.now(UTC) - timedelta(days=days)

        results = (
            self.db.query(
                Skill.skill_id,
                Skill.skill_path,
                Skill.name,
                func.count(UsageEvent.event_id).label("usage_count"),
                func.count(func.distinct(UsageEvent.user_id)).label("unique_users"),
            )
            .join(UsageEvent, Skill.skill_id == UsageEvent.skill_id)
            .filter(UsageEvent.occurred_at >= since)
            .group_by(Skill.skill_id, Skill.skill_path, Skill.name)
            .order_by(desc("usage_count"))
            .limit(limit)
            .all()
        )

        return [
            {
                "skill_id": r.skill_id,
                "skill_path": r.skill_path,
                "name": r.name,
                "usage_count": r.usage_count,
                "unique_users": r.unique_users,
            }
            for r in results
        ]


def get_skill_repository(db: Session) -> SkillRepository:
    """Get a SkillRepository instance."""
    return SkillRepository(db)


def get_job_repository(db: Session) -> JobRepository:
    """Get a JobRepository instance."""
    return JobRepository(db)


def get_taxonomy_repository(db: Session) -> TaxonomyRepository:
    """Get a TaxonomyRepository instance."""
    return TaxonomyRepository(db)


def get_validation_repository(db: Session) -> ValidationRepository:
    """Get a ValidationRepository instance."""
    return ValidationRepository(db)


def get_usage_repository(db: Session) -> UsageRepository:
    """Get a UsageRepository instance."""
    return UsageRepository(db)


class ConversationSessionRepository:
    """
    Repository for conversation session persistence.

    Replaces in-memory session dict with database-backed storage.
    """

    def __init__(self, db: Session):
        """Initialize the conversation session repository.

        Args:
            db: Database session for persistence operations
        """
        self.db = db

    def get_by_id(self, session_id: str | Any) -> ConversationSession | None:
        """
        Get a session by its ID.

        Args:
            session_id: UUID of the session (string or UUID)

        Returns:
            ConversationSession or None if not found

        """
        from uuid import UUID

        if isinstance(session_id, str):
            try:
                session_id = UUID(session_id)
            except ValueError:
                return None
        return (
            self.db.query(ConversationSession)
            .filter(ConversationSession.session_id == session_id)
            .first()
        )

    def get_by_user(
        self,
        user_id: str,
        *,
        active_only: bool = True,
        limit: int = 50,
    ) -> list[ConversationSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier
            active_only: Filter to non-complete sessions
            limit: Maximum sessions to return

        Returns:
            List of ConversationSession instances

        """
        query = self.db.query(ConversationSession).filter(ConversationSession.user_id == user_id)

        if active_only:
            query = query.filter(ConversationSession.state != ConversationStateEnum.COMPLETE)

        return query.order_by(ConversationSession.last_activity_at.desc()).limit(limit).all()

    def create(
        self,
        *,
        session_id: str | None = None,
        user_id: str = "default",
        state: str = ConversationStateEnum.EXPLORING,
        metadata: dict | None = None,
    ) -> ConversationSession:
        """
        Create a new conversation session.

        Args:
            session_id: Optional pre-defined session ID (must be valid UUID if provided)
            user_id: User identifier
            state: Initial conversation state
            metadata: Optional session metadata

        Returns:
            Created ConversationSession

        Raises:
            ValueError: If session_id is provided but not a valid UUID

        """
        from datetime import timedelta
        from uuid import UUID, uuid4

        # Parse or generate session ID
        if session_id:
            if isinstance(session_id, str):
                try:
                    parsed_id = UUID(session_id)
                except ValueError as e:
                    raise ValueError(f"Invalid session_id: {session_id}") from e
            else:
                parsed_id = session_id
        else:
            parsed_id = uuid4()

        session = ConversationSession(
            session_id=parsed_id,
            user_id=user_id,
            state=state,
            session_metadata=metadata or {},
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    # Allowed fields for update - prevents mutation of protected fields
    _ALLOWED_UPDATE_FIELDS = frozenset(
        {
            "state",
            "session_metadata",
            "messages",
            "expires_at",
            "current_skill_request",
            "pending_skills",
        }
    )

    def update(
        self,
        session: ConversationSession,
        **updates: Any,
    ) -> ConversationSession:
        """
        Update a session with new values.

        Only allows updates to whitelisted fields: state, session_metadata,
        messages, expires_at, current_skill_request, pending_skills.

        Args:
            session: Session to update
            **updates: Fields to update (only allowed fields are applied)

        Returns:
            Updated ConversationSession

        """
        for key, value in updates.items():
            if key in self._ALLOWED_UPDATE_FIELDS:
                setattr(session, key, value)

        # Always update activity timestamp
        session.last_activity_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(session)
        return session

    def add_message(
        self,
        session: ConversationSession,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> ConversationSession:
        """
        Add a message to the session.

        Args:
            session: Session to add message to
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata

        Returns:
            Updated ConversationSession

        """
        messages = list(session.messages) if session.messages else []
        messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            }
        )
        return self.update(session, messages=messages)

    def delete(self, session_id: str | Any) -> bool:
        """
        Delete a session.

        Args:
            session_id: UUID of the session

        Returns:
            True if deleted, False if not found

        """
        session = self.get_by_id(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False

    def cleanup_expired(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of sessions deleted

        """
        result = (
            self.db.query(ConversationSession)
            .filter(
                ConversationSession.expires_at.isnot(None),
                ConversationSession.expires_at < datetime.now(UTC),
            )
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return result

    def list_active_summaries(
        self,
        *,
        limit: int = 100,
    ) -> list[dict]:
        """
        List all active (non-expired, non-complete) sessions as summary dicts.

        Returns:
            List of session summary dicts (not ORM models)

        """
        sessions = (
            self.db.query(ConversationSession)
            .filter(
                ConversationSession.state != ConversationStateEnum.COMPLETE,
            )
            .filter(
                (ConversationSession.expires_at.is_(None))
                | (ConversationSession.expires_at > datetime.now(UTC))
            )
            .order_by(ConversationSession.last_activity_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "session_id": str(s.session_id),
                "user_id": s.user_id,
                "state": s.state,
                "message_count": len(s.messages) if s.messages else 0,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "last_activity_at": (
                    s.last_activity_at.isoformat() if s.last_activity_at else None
                ),
            }
            for s in sessions
        ]


def get_conversation_session_repository(db: Session) -> ConversationSessionRepository:
    """Get a ConversationSessionRepository instance."""
    return ConversationSessionRepository(db)
