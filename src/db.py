from typing import Dict, List
import pandas as pd
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.dialects.sqlite import (
    BLOB,
    BOOLEAN,
    CHAR,
    DATE,
    DATETIME,
    DECIMAL,
    FLOAT,
    INTEGER,
    NUMERIC,
    JSON,
    SMALLINT,
    TEXT,
    TIME,
    TIMESTAMP,
    VARCHAR,
)

class Base(DeclarativeBase):
    pass

class Models(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    size: Mapped[str] = mapped_column(TEXT, nullable=False)
    options: Mapped[Dict] = mapped_column(JSON)

    def __repr__(self) -> str:
        if self.options:
            return f"{self.name}:{self.size}_o:{self.options}"
        else:
            return f"{self.name}:{self.size}_Default"
    
    @classmethod
    def get_by_id(cls, session: Session, model_id: int):
        return session.query(cls).filter_by(id=model_id).first()
    

class Prompts(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, nullable=False)
    
    prompt: Mapped[str] = mapped_column(TEXT, nullable=False)

    tags: Mapped[List[str]] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"prompt {self.id}: {self.prompt}"
    
    @classmethod
    def get_by_id(cls, session: Session, prompt_id: int):
        return session.query(cls).filter_by(id=prompt_id).first()

class Ris(Base):
    __tablename__ = "ris"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, nullable=False)
    
    revision_1: Mapped[str] = mapped_column(TEXT)
    revision_2: Mapped[str] = mapped_column(TEXT)
    final: Mapped[str] = mapped_column(TEXT)
    examination: Mapped[str] = mapped_column(TEXT)


    def __repr__(self) -> str:
        return f"prompt {self.id}: {self.prompt}"
    
    @classmethod
    def get_by_id(cls, session: Session, ris_id: int):
        return session.query(cls).filter_by(id=ris_id).first()
    
    @classmethod
    def get_rev_reports(cls, session: Session):
        # Step 1: Query the database to get the columns id, revision_1, and revision_2
        results = session.query(cls.id, cls.revision_1, cls.revision_2).all()

        # Step 2: Prepare data for the DataFrame
        data = []
        for result in results:
            id = result.id
            if result.revision_1 is not None:
             rev = result.revision_1
            elif result.revision_2 is not None:
                rev = result.revision_2
            else:
                rev = None
            data.append({'id': id, 'report': rev})

        # Step 3: Create a pandas DataFrame
        df = pd.DataFrame(data)
        
        # Step 4: Drop rows where the 'report' column is null
        df.dropna(subset=['report'], inplace=True)
        
        return df

    @classmethod
    def get_final_reports(cls, session: Session, df: pd.DataFrame):
        # Step 1: Query the database to get the columns id, revision_1, and revision_2
        results = session.query(cls.id, cls.final).all()
    
        # Step 2: Prepare data for the DataFrame
        data = []
        for result in results:
            id = result.id
            final = result.final
            data.append({'id': id, 'report': final})
    
        # Step 3: Create a pandas DataFrame
        df = pd.DataFrame(data)
        return df
