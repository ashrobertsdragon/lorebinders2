"""SQLAlchemy storage backend for LoreBinders."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import JSON, String, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

import lorebinders.storage.workspace as workspace
from lorebinders import models
from lorebinders.settings import get_settings
from lorebinders.types import EntityTraits


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class ExtractionModel(Base):
    """SQLAlchemy model for extractions."""

    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(1024), index=True)
    chapter_num: Mapped[int] = mapped_column(index=True)
    data: Mapped[dict[str, list[str]]] = mapped_column(JSON)


class ProfileModel(Base):
    """SQLAlchemy model for EntityProfiles."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(1024), index=True)
    chapter_num: Mapped[int] = mapped_column(index=True)
    category: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    data: Mapped[EntityTraits] = mapped_column(JSON)


class SummaryModel(Base):
    """SQLAlchemy model for summaries."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(1024), index=True)
    category: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str] = mapped_column(String)


class DBStorage:
    """SQLAlchemy-backed storage provider."""

    def __init__(self, db_url: str | None = None) -> None:
        """Initialize the database storage.

        Args:
            db_url: The SQLAlchemy database URL. Defaults to in-memory SQLite.
                Overrides the DB_URL environment variable.
        """
        if not db_url:
            db_url = get_settings().db_url
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self._path: Path | None = None
        self.workspace_id: str | None = None

    def _get_session(self) -> Generator[Session, None, None]:
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def set_workspace(self, author: str, title: str) -> None:
        """Set the workspace context."""
        path = workspace.ensure_workspace(author, title)
        self._path = path
        self.workspace_id = str(path)

    @property
    def path(self) -> Path:
        """The base path of the workspace."""
        if not self._path:
            raise RuntimeError("Workspace not set")
        return self._path

    def extraction_exists(self, chapter_num: int) -> bool:
        """Check if extraction exists.

        Returns:
            True if it exists.
        """
        with self.SessionLocal() as session:
            stmt = select(ExtractionModel).where(
                ExtractionModel.workspace_id == self.workspace_id,
                ExtractionModel.chapter_num == chapter_num,
            )
            return session.scalars(stmt).first() is not None

    def save_extraction(
        self,
        chapter_num: int,
        data: dict[str, list[str]],
    ) -> None:
        """Save extraction data."""
        with self.SessionLocal() as session:
            stmt = select(ExtractionModel).where(
                ExtractionModel.workspace_id == self.workspace_id,
                ExtractionModel.chapter_num == chapter_num,
            )
            model = session.scalars(stmt).first()
            if model:
                model.data = data
            else:
                model = ExtractionModel(
                    workspace_id=self.workspace_id,
                    chapter_num=chapter_num,
                    data=data,
                )
                session.add(model)
            session.commit()

    def load_extraction(self, chapter_num: int) -> dict[str, list[str]]:
        """Load extraction data.

        Returns:
            The extraction data.

        Raises:
            FileNotFoundError: If the extraction does not exist.
        """
        with self.SessionLocal() as session:
            stmt = select(ExtractionModel).where(
                ExtractionModel.workspace_id == self.workspace_id,
                ExtractionModel.chapter_num == chapter_num,
            )
            model = session.scalars(stmt).first()
            if not model:
                raise FileNotFoundError(
                    f"Extraction for chapter {chapter_num} not found"
                )

            return {
                str(k): [str(v) for v in val] for k, val in model.data.items()
            }

    def profile_exists(
        self, chapter_num: int, category: str, name: str
    ) -> bool:
        """Check if profile exists.

        Returns:
            True if it exists.
        """
        with self.SessionLocal() as session:
            stmt = select(ProfileModel).where(
                ProfileModel.workspace_id == self.workspace_id,
                ProfileModel.chapter_num == chapter_num,
                ProfileModel.category == category,
                ProfileModel.name == name,
            )
            return session.scalars(stmt).first() is not None

    def save_profile(
        self,
        chapter_num: int,
        profile: models.EntityProfile,
    ) -> None:
        """Save profile data."""
        with self.SessionLocal() as session:
            stmt = select(ProfileModel).where(
                ProfileModel.workspace_id == self.workspace_id,
                ProfileModel.chapter_num == chapter_num,
                ProfileModel.category == profile.category,
                ProfileModel.name == profile.name,
            )
            model = session.scalars(stmt).first()
            data = profile.model_dump(mode="json")
            if model:
                model.data = data
            else:
                model = ProfileModel(
                    workspace_id=self.workspace_id,
                    chapter_num=chapter_num,
                    category=profile.category,
                    name=profile.name,
                    data=data,
                )
                session.add(model)
            session.commit()

    def load_profile(
        self, chapter_num: int, category: str, name: str
    ) -> models.EntityProfile:
        """Load profile data.

        Returns:
            The entity profile.

        Raises:
            FileNotFoundError: If the profile does not exist.
        """
        with self.SessionLocal() as session:
            stmt = select(ProfileModel).where(
                ProfileModel.workspace_id == self.workspace_id,
                ProfileModel.chapter_num == chapter_num,
                ProfileModel.category == category,
                ProfileModel.name == name,
            )
            model = session.scalars(stmt).first()
            if not model:
                raise FileNotFoundError(
                    f"Profile '{name}' ({category}) for chapter {chapter_num} "
                    "not found"
                )
            return models.EntityProfile.model_validate(model.data)

    def summary_exists(self, category: str, name: str) -> bool:
        """Check if summary exists.

        Returns:
            True if it exists.
        """
        with self.SessionLocal() as session:
            stmt = select(SummaryModel).where(
                SummaryModel.workspace_id == self.workspace_id,
                SummaryModel.category == category,
                SummaryModel.name == name,
            )
            return session.scalars(stmt).first() is not None

    def save_summary(self, category: str, name: str, summary: str) -> None:
        """Save summary data."""
        with self.SessionLocal() as session:
            stmt = select(SummaryModel).where(
                SummaryModel.workspace_id == self.workspace_id,
                SummaryModel.category == category,
                SummaryModel.name == name,
            )
            model = session.scalars(stmt).first()
            if model:
                model.summary = summary
            else:
                model = SummaryModel(
                    workspace_id=self.workspace_id,
                    category=category,
                    name=name,
                    summary=summary,
                )
                session.add(model)
            session.commit()

    def load_summary(self, category: str, name: str) -> str:
        """Load summary data.

        Returns:
            The summary text.

        Raises:
            FileNotFoundError: If the summary does not exist.
        """
        with self.SessionLocal() as session:
            stmt = select(SummaryModel).where(
                SummaryModel.workspace_id == self.workspace_id,
                SummaryModel.category == category,
                SummaryModel.name == name,
            )
            model = session.scalars(stmt).first()
            if not model:
                raise FileNotFoundError(
                    f"Summary for '{name}' ({category}) not found"
                )
            return model.summary
