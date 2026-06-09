import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from src.extensions.database import db


def _now():
    return datetime.now(timezone.utc)


class RoleEnum(PyEnum):
    usuario = "usuario"
    admin = "admin"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.usuario)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    interests = db.relationship("UserTagInterest", back_populates="user", cascade="all, delete-orphan")
    ratings = db.relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    reports = db.relationship("Report", back_populates="user", cascade="all, delete-orphan")
    collections = db.relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    submitted_reas = db.relationship("REA", back_populates="submitter")


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)

    rea_associations = db.relationship("REATag", back_populates="tag", cascade="all, delete-orphan")
    user_interests = db.relationship("UserTagInterest", back_populates="tag", cascade="all, delete-orphan")


class UserTagInterest(db.Model):
    __tablename__ = "user_tag_interests"

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    weight = db.Column(db.Float, nullable=False, default=1.0)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = db.relationship("User", back_populates="interests")
    tag = db.relationship("Tag", back_populates="user_interests")


class REA(db.Model):
    __tablename__ = "reas"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=False, unique=True)
    author = db.Column(db.String(200))
    license = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(10), nullable=False, default="pt-BR")
    thumbnail_url = db.Column(db.String(500))
    avg_rating = db.Column(db.Float, nullable=False, default=0.0)
    rating_count = db.Column(db.Integer, nullable=False, default=0)
    report_count = db.Column(db.Integer, nullable=False, default=0)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    is_blocked = db.Column(db.Boolean, nullable=False, default=False)
    submitted_by = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    submitter = db.relationship("User", back_populates="submitted_reas")
    tags = db.relationship("REATag", back_populates="rea", cascade="all, delete-orphan")
    ratings = db.relationship("Rating", back_populates="rea", cascade="all, delete-orphan")
    reports = db.relationship("Report", back_populates="rea", cascade="all, delete-orphan")
    collection_items = db.relationship("CollectionItem", back_populates="rea", cascade="all, delete-orphan")


class REATag(db.Model):
    __tablename__ = "rea_tags"

    rea_id = db.Column(UUID(as_uuid=True), db.ForeignKey("reas.id", ondelete="CASCADE"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    rea = db.relationship("REA", back_populates="tags")
    tag = db.relationship("Tag", back_populates="rea_associations")


class Rating(db.Model):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "rea_id", name="uq_rating_user_rea"),
        CheckConstraint("score >= 1 AND score <= 5", name="ck_rating_score_range"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rea_id = db.Column(UUID(as_uuid=True), db.ForeignKey("reas.id", ondelete="CASCADE"), nullable=False)
    score = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    user = db.relationship("User", back_populates="ratings")
    rea = db.relationship("REA", back_populates="ratings")


class Report(db.Model):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("user_id", "rea_id", name="uq_report_user_rea"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rea_id = db.Column(UUID(as_uuid=True), db.ForeignKey("reas.id", ondelete="CASCADE"), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    user = db.relationship("User", back_populates="reports")
    rea = db.relationship("REA", back_populates="reports")


class Collection(db.Model):
    __tablename__ = "collections"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    user = db.relationship("User", back_populates="collections")
    items = db.relationship("CollectionItem", back_populates="collection", cascade="all, delete-orphan")


class CollectionItem(db.Model):
    __tablename__ = "collection_items"

    collection_id = db.Column(UUID(as_uuid=True), db.ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    rea_id = db.Column(UUID(as_uuid=True), db.ForeignKey("reas.id", ondelete="CASCADE"), primary_key=True)
    added_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    collection = db.relationship("Collection", back_populates="items")
    rea = db.relationship("REA", back_populates="collection_items")
