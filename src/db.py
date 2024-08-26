"""Database models for the application."""

from typing import Dict, List
import pandas as pd
from sqlalchemy.orm import DeclarativeBase as Base
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.dialects.sqlite import INTEGER, JSON, TEXT

# from sqlalchemy import ForeignKey


class Models(Base):
    """Model class for the models table."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    size: Mapped[str] = mapped_column(TEXT, nullable=False)
    options: Mapped[Dict] = mapped_column(JSON)

    def __repr__(self) -> str:
        if self.options:
            return f"{self.name}:{self.size}_o:{self.options}"
        return f"{self.name}:{self.size}_Default"

    @classmethod
    def get_by_id(cls, session: Session, model_id: int):
        """Function to get a model by its id."""
        return session.query(cls).filter_by(id=model_id).first()


class Prompts(Base):
    """Model class for the prompts table."""

    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, nullable=False)

    prompt: Mapped[str] = mapped_column(TEXT, nullable=False)

    tags: Mapped[List[str]] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"prompt {self.id}: {self.prompt}"

    @classmethod
    def get_by_id(cls, session: Session, prompt_id: int):
        """Function to get a prompt by its id."""
        return session.query(cls).filter_by(id=prompt_id).first()


class Ris(Base):
    """Model class for the ris table."""

    __tablename__ = "ris"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, nullable=False)

    revision_1: Mapped[str] = mapped_column(TEXT)
    revision_2: Mapped[str] = mapped_column(TEXT)
    final: Mapped[str] = mapped_column(TEXT)
    examination: Mapped[str] = mapped_column(TEXT)

    def __repr__(self) -> str:
        return f"Ris Report: {self.id}"

    @classmethod
    def get_by_id(cls, session: Session, ris_id: int):
        """Function to get a ris report by its id."""
        return session.query(cls).filter_by(id=ris_id).first()

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
