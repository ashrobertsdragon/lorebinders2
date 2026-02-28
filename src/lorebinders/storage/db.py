"""SQLAlchemy storage backend for LoreBinders."""

from collections.abc import Generator
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, String, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

from lorebinders import models


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class ExtractionModel(Base):
    """SQLAlchemy model for extractions."""

    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    directory_path: Mapped[str] = mapped_column(String(1024), index=True)
    chapter_num: Mapped[int] = mapped_column(index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class ProfileModel(Base):
    """SQLAlchemy model for EntityProfiles."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    directory_path: Mapped[str] = mapped_column(String(1024), index=True)
    chapter_num: Mapped[int] = mapped_column(index=True)
    category: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class SummaryModel(Base):
    """SQLAlchemy model for summaries."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    directory_path: Mapped[str] = mapped_column(String(1024), index=True)
    category: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str] = mapped_column(String)


class DBStorage:
    """SQLAlchemy-backed storage provider."""

    def __init__(self, db_url: str = "sqlite:///:memory:") -> None:
        """Initialize the database storage.

        Args:
            db_url: The SQLAlchemy database URL. Defaults to in-memory SQLite.
        """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def _get_session(self) -> Generator[Session, None, None]:
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def ensure_workspace(self, author: str, title: str) -> Path:
        """Ensure the workspace directory exists.

        For DBStorage, we still return a Path (acting as a workspace key/ID)
        and ensure the folder exists, just like FilesystemStorage,
        because other components might still write separate artifacts.

        Returns:
            The path to the workspace.
        """
        from lorebinders.storage.workspace import (
            ensure_workspace as base_ensure,
        )

        return base_ensure(author, title)

    def extraction_exists(
        self, extractions_dir: Path, chapter_num: int
    ) -> bool:
        """Check if extraction exists.

        Returns:
            True if it exists.
        """
        dir_str = str(extractions_dir)
        with self.SessionLocal() as session:
            stmt = select(ExtractionModel).where(
                ExtractionModel.directory_path == dir_str,
                ExtractionModel.chapter_num == chapter_num,
            )
            return session.scalars(stmt).first() is not None

    def save_extraction(
        self,
        extractions_dir: Path,
        chapter_num: int,
        data: dict[str, list[str]],
    ) -> None:
        """Save extraction data."""
        dir_str = str(extractions_dir)
        with self.SessionLocal() as session:
            stmt = select(ExtractionModel).where(
                ExtractionModel.directory_path == dir_str,
                ExtractionModel.chapter_num == chapter_num,
            )
            model = session.scalars(stmt).first()
            if model:
                model.data = data
            else:
                model = ExtractionModel(
                    directory_path=dir_str,
                    chapter_num=chapter_num,
                    data=data,
                )
                session.add(model)
            session.commit()

    def load_extraction(
        self, extractions_dir: Path, chapter_num: int
    ) -> dict[str, list[str]]:
        """Load extraction data.

        Returns:
            The extraction data.

        Raises:
            FileNotFoundError: If the extraction does not exist.
        """
        dir_str = str(extractions_dir)
        with self.SessionLocal() as session:
            stmt = select(ExtractionModel).where(
                ExtractionModel.directory_path == dir_str,
                ExtractionModel.chapter_num == chapter_num,
            )
            model = session.scalars(stmt).first()
            if not model:
                raise FileNotFoundError(
                    f"Extraction for chapter {chapter_num} not found "
                    f"in {dir_str}"
                )

            return {
                str(k): [str(v) for v in val] for k, val in model.data.items()
            }

    def profile_exists(
        self, profiles_dir: Path, chapter_num: int, category: str, name: str
    ) -> bool:
        """Check if profile exists.

        Returns:
            True if it exists.
        """
        dir_str = str(profiles_dir)
        with self.SessionLocal() as session:
            stmt = select(ProfileModel).where(
                ProfileModel.directory_path == dir_str,
                ProfileModel.chapter_num == chapter_num,
                ProfileModel.category == category,
                ProfileModel.name == name,
            )
            return session.scalars(stmt).first() is not None

    def save_profile(
        self,
        profiles_dir: Path,
        chapter_num: int,
        profile: models.EntityProfile,
    ) -> None:
        """Save profile data."""
        dir_str = str(profiles_dir)
        with self.SessionLocal() as session:
            stmt = select(ProfileModel).where(
                ProfileModel.directory_path == dir_str,
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
                    directory_path=dir_str,
                    chapter_num=chapter_num,
                    category=profile.category,
                    name=profile.name,
                    data=data,
                )
                session.add(model)
            session.commit()

    def load_profile(
        self, profiles_dir: Path, chapter_num: int, category: str, name: str
    ) -> models.EntityProfile:
        """Load profile data.

        Returns:
            The entity profile.

        Raises:
            FileNotFoundError: If the profile does not exist.
        """
        dir_str = str(profiles_dir)
        with self.SessionLocal() as session:
            stmt = select(ProfileModel).where(
                ProfileModel.directory_path == dir_str,
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

    def summary_exists(
        self, summaries_dir: Path, category: str, name: str
    ) -> bool:
        """Check if summary exists.

        Returns:
            True if it exists.
        """
        dir_str = str(summaries_dir)
        with self.SessionLocal() as session:
            stmt = select(SummaryModel).where(
                SummaryModel.directory_path == dir_str,
                SummaryModel.category == category,
                SummaryModel.name == name,
            )
            return session.scalars(stmt).first() is not None

    def save_summary(
        self, summaries_dir: Path, category: str, name: str, summary: str
    ) -> None:
        """Save summary data."""
        dir_str = str(summaries_dir)
        with self.SessionLocal() as session:
            stmt = select(SummaryModel).where(
                SummaryModel.directory_path == dir_str,
                SummaryModel.category == category,
                SummaryModel.name == name,
            )
            model = session.scalars(stmt).first()
            if model:
                model.summary = summary
            else:
                model = SummaryModel(
                    directory_path=dir_str,
                    category=category,
                    name=name,
                    summary=summary,
                )
                session.add(model)
            session.commit()

    def load_summary(
        self, summaries_dir: Path, category: str, name: str
    ) -> str:
        """Load summary data.

        Returns:
            The summary text.

        Raises:
            FileNotFoundError: If the summary does not exist.
        """
        dir_str = str(summaries_dir)
        with self.SessionLocal() as session:
            stmt = select(SummaryModel).where(
                SummaryModel.directory_path == dir_str,
                SummaryModel.category == category,
                SummaryModel.name == name,
            )
            model = session.scalars(stmt).first()
            if not model:
                raise FileNotFoundError(
                    f"Summary for '{name}' ({category}) not found"
                )
            return model.summary
