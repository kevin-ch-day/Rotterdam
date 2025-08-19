from __future__ import annotations

"""SQLAlchemy ORM models for analysis metadata."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TimestampMixin:
    """Server-side UTC timestamp mixin."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    serial = Column(String(191), unique=True, index=True, nullable=False)
    model = Column(String(191))
    manufacturer = Column(String(191))
    android_version = Column(String(32))
    sdk = Column(String(16))
    connection = Column(String(32))
    is_emulator = Column(Boolean, default=False)
    packages = relationship(
        "DevicePackage", back_populates="device", cascade="all, delete-orphan"
    )
    analyses = relationship("Analysis", back_populates="device")


class Package(Base, TimestampMixin):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True)
    package_name = Column(String(191), unique=True, index=True, nullable=False)
    version = Column(String(191))
    installer = Column(String(191))
    uid = Column(String(32))
    system = Column(Boolean, default=False)
    priv_app = Column(Boolean, default=False)
    devices = relationship(
        "DevicePackage", back_populates="package", cascade="all, delete-orphan"
    )


class DevicePackage(Base, TimestampMixin):
    __tablename__ = "device_packages"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    package_id = Column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("device_id", "package_id", name="uq_device_pkg"),)
    device = relationship("Device", back_populates="packages")
    package = relationship("Package", back_populates="devices")


class Analysis(Base, TimestampMixin):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    kind = Column(String(64), nullable=False)
    package_name = Column(String(191), index=True)
    apk_sha256 = Column(String(64), index=True)
    score = Column(Float)
    status = Column(String(32), default="queued")
    report_path = Column(Text)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    device = relationship("Device", back_populates="analyses")
    findings = relationship(
        "AnalysisFinding", back_populates="analysis", cascade="all, delete-orphan"
    )


class AnalysisFinding(Base, TimestampMixin):
    __tablename__ = "analysis_findings"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(64))
    key = Column(String(191))
    value = Column(Text)
    severity = Column(String(16))
    analysis = relationship("Analysis", back_populates="findings")


class PermissionsSnapshot(Base, TimestampMixin):
    __tablename__ = "permissions_snapshots"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)


class PermissionItem(Base, TimestampMixin):
    __tablename__ = "permission_items"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(
        Integer, ForeignKey("permissions_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    package_name = Column(String(191))
    permission = Column(String(191))
    granted = Column(Boolean, default=False)
    source = Column(String(64))


# Helpful indices
Index("ix_analyses_created_at", Analysis.created_at)
Index("ix_perm_items_pkg_perm", PermissionItem.package_name, PermissionItem.permission)
