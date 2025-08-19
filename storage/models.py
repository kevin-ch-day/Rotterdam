"""SQLAlchemy ORM models for persisting analysis results."""

from __future__ import annotations

import datetime as _dt
from typing import Any

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.orm import declarative_base

# Base class for all ORM models
Base = declarative_base()


class RiskReport(Base):
    """Persisted risk score for an analysed package.

    Attributes
    ----------
    id: int
        Primary key for the report entry.
    package_name: str
        Identifier for the analysed application/package.
    score: float
        Calculated risk score.
    rationale: str
        Human readable rationale for the score.
    breakdown: dict
        Mapping of metric name to contribution.  Stored as JSON.
    created_at: datetime
        Timestamp when the report was generated.
    """

    __tablename__ = "risk_reports"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    package_name: str = Column(String, nullable=False, index=True)
    score: float = Column(Float, nullable=False)
    rationale: str = Column(String, nullable=False)
    breakdown: Any = Column(JSON, nullable=False)
    created_at: _dt.datetime = Column(
        DateTime, default=_dt.datetime.utcnow, nullable=False, index=True
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable representation of the report."""

        return {
            "id": self.id,
            "package_name": self.package_name,
            "score": self.score,
            "rationale": self.rationale,
            "breakdown": self.breakdown,
            "created_at": self.created_at,
        }
