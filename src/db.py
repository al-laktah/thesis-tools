"""Database models for the application."""

from typing import Dict, List
import pandas as pd
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.dialects.sqlite import INTEGER, JSON, TEXT

# from sqlalchemy import ForeignKey


class Base(DeclarativeBase):
    """Base class for all database models."""

    __abstract__ = True
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, nullable=False)

    def to_dict(self):
        """Convert an instance to a dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    @classmethod
    def get_by_id(cls, session: Session, x_id: int):
        """Function to get a row by its id."""
        return session.query(cls).filter_by(id=x_id).first()

    @classmethod
    def to_dataframe(cls, session: Session) -> pd.DataFrame:
        """Convert the entire table to a pandas DataFrame."""
        instances = session.query(cls).all()
        if not instances:
            return pd.DataFrame()

        # Convert each instance to a dictionary
        data = [instance.to_dict() for instance in instances]
        return pd.DataFrame(data)


class Models(Base):
    """Model class for the models table."""

    __tablename__ = "models"

    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    size: Mapped[str] = mapped_column(TEXT, nullable=False)
    options: Mapped[Dict] = mapped_column(JSON)

    def __repr__(self) -> str:
        if self.options:
            return f"{self.name}:{self.size}_o:{self.options}"
        return f"{self.name}:{self.size}_Default"


class Prompts(Base):
    """Model class for the prompts table."""

    __tablename__ = "prompts"

    prompt: Mapped[str] = mapped_column(TEXT, nullable=False)
    tags: Mapped[List[str]] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"prompt {self.id}: {self.prompt}"


class Ris(Base):
    """Model class for the ris table."""

    __tablename__ = "ris"

    revision_1: Mapped[str] = mapped_column(TEXT)
    revision_2: Mapped[str] = mapped_column(TEXT)
    final: Mapped[str] = mapped_column(TEXT)
    examination: Mapped[str] = mapped_column(TEXT)

    def __repr__(self) -> str:
        return f"Ris Report: {self.id}"

    @classmethod
    def get_rev_reports(cls, session: Session):
        """Function to get the revision reports as a DataFrame."""

        results = session.query(cls.id, cls.revision_1, cls.revision_2).all()

        data = []
        for result in results:
            if result.revision_1 is not None:
                rev = result.revision_1
            elif result.revision_2 is not None:
                rev = result.revision_2
            else:
                rev = None
            data.append({"id": result.id, "report": rev})

        df = pd.DataFrame(data)
        df.dropna(subset=["report"], inplace=True)

        return df

    @classmethod
    def get_final_reports(cls, session: Session, df: pd.DataFrame):
        """Function to get the final reports as a DataFrame."""

        results = session.query(cls.id, cls.final).all()

        data = []
        for result in results:
            data.append({"id": result.id, "report": result.final})

        df = pd.DataFrame(data)

        return df
