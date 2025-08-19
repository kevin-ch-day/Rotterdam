"""Repository layer for CRUD operations on stored analysis results."""

from __future__ import annotations

import os
from typing import Iterable, List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, RiskReport


def init_db(url: str | None = None) -> sessionmaker:
    """Initialise a database and return a ``sessionmaker`` factory.

    The URL can point to any SQLAlchemy-supported backend, e.g. SQLite or
    MySQL.  If omitted, the ``DATABASE_URL`` environment variable is inspected
    and finally an in-memory SQLite database is used as a fallback.
    """

    db_url = url or os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


class RiskReportRepository:
    """Simple repository for :class:`RiskReport` records."""

    def __init__(
        self, session_factory: sessionmaker | None = None, *, db_url: str | None = None
    ):
        self._session_factory = session_factory or init_db(db_url)

    def _session(self) -> Session:
        return self._session_factory()

    # CRUD operations
    def add_report(
        self,
        package_name: str,
        score: float,
        rationale: str,
        breakdown: dict,
    ) -> RiskReport:
        with self._session() as session:
            report = RiskReport(
                package_name=package_name,
                score=score,
                rationale=rationale,
                breakdown=breakdown,
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            return report

    def get_report(self, report_id: int) -> Optional[RiskReport]:
        with self._session() as session:
            return session.get(RiskReport, report_id)

    def list_reports(self, package_name: str | None = None) -> List[RiskReport]:
        with self._session() as session:
            stmt = select(RiskReport)
            if package_name:
                stmt = stmt.where(RiskReport.package_name == package_name)
            stmt = stmt.order_by(RiskReport.created_at.desc())
            return list(session.scalars(stmt))

    def get_latest(self, package_name: str) -> Optional[RiskReport]:
        reports = self.list_reports(package_name)
        return reports[0] if reports else None

    def delete(self, report_id: int) -> None:
        with self._session() as session:
            report = session.get(RiskReport, report_id)
            if report is not None:
                session.delete(report)
                session.commit()
