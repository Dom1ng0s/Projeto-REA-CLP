import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from src.extensions.database import db


def _pg_enum(name: str, *values: str) -> sa.Enum:
    """Mapeia um enum PostgreSQL existente — create_type=False não tenta criá-lo."""
    return sa.Enum(*values, name=name, create_type=False)


def _now():
    return datetime.now(timezone.utc)


# ── Status constants (mirrors public.rea_status enum in Supabase) ──────────────
REA_STATUS_ACTIVE  = "active"
REA_STATUS_HIDDEN  = "hidden_low_rating"
REA_STATUS_REVIEW  = "blocked_review"
REA_STATUS_REMOVED = "removed"


# ── Profile (mirrors public.profiles — linked to auth.users) ──────────────────
class Profile(db.Model):
    __tablename__ = "profiles"

    id              = db.Column(UUID(as_uuid=True), primary_key=True)
    display_name    = db.Column(db.Text)
    bio             = db.Column(db.Text)
    avatar_url      = db.Column(db.Text)
    skip_external_warning = db.Column(db.Boolean, nullable=False, default=False)
    created_at      = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at      = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)


# ── UserRole (mirrors public.user_roles) ──────────────────────────────────────
class UserRole(db.Model):
    __tablename__ = "user_roles"

    id         = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    role       = db.Column(db.String(20), nullable=False)   # 'admin' | 'user'
    granted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)


# ── REA (mirrors public.reas) ──────────────────────────────────────────────────
class REA(db.Model):
    __tablename__ = "reas"

    id            = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title         = db.Column(db.Text, nullable=False)
    description   = db.Column(db.Text)
    resource_url  = db.Column(db.Text, nullable=False)
    thumbnail_url = db.Column(db.Text)
    source_url    = db.Column(db.Text)
    author        = db.Column(db.Text)
    format          = db.Column(_pg_enum("rea_format",
                        "video", "audio", "text", "image", "interactive", "slides", "other"),
                        nullable=False)
    license         = db.Column(_pg_enum("rea_license",
                        "cc_by", "cc_by_sa", "cc_by_nc", "cc_by_nc_sa",
                        "cc_by_nd", "cc0", "public_domain", "other"),
                        nullable=False)
    language        = db.Column(_pg_enum("rea_language", "pt_br", "en", "es", "other"),
                        nullable=False, default="pt_br")
    subject_area    = db.Column(db.Text, nullable=False)
    education_level = db.Column(_pg_enum("education_level",
                        "infantil", "fundamental", "medio", "tecnico",
                        "graduacao", "pos_graduacao", "extensao", "livre"),
                        nullable=False)
    tags            = db.Column(ARRAY(db.Text), nullable=False, default=list)
    status          = db.Column(_pg_enum("rea_status",
                        "active", "hidden_low_rating", "blocked_review", "removed"),
                        nullable=False, default=REA_STATUS_ACTIVE, index=True)
    rating_avg    = db.Column(db.Numeric(3, 2), nullable=False, default=0)
    rating_count  = db.Column(db.Integer, nullable=False, default=0)
    report_count  = db.Column(db.Integer, nullable=False, default=0)
    submitted_by  = db.Column(UUID(as_uuid=True), nullable=True)
    created_at    = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at    = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    ratings  = db.relationship("REARating",  back_populates="rea", cascade="all, delete-orphan")
    reports  = db.relationship("REAReport",  back_populates="rea", cascade="all, delete-orphan")
    collection_items = db.relationship("CollectionItem", back_populates="rea", cascade="all, delete-orphan")
    interactions = db.relationship("REAInteraction", back_populates="rea", cascade="all, delete-orphan")


# ── Tag (mirrors public.tags) ──────────────────────────────────────────────────
class Tag(db.Model):
    __tablename__ = "tags"

    id         = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug       = db.Column(db.Text, unique=True, nullable=False, index=True)
    label      = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    user_interests = db.relationship("UserInterest", back_populates="tag", cascade="all, delete-orphan")


# ── UserInterest (mirrors public.user_interests) ───────────────────────────────
class UserInterest(db.Model):
    __tablename__ = "user_interests"

    user_id    = db.Column(UUID(as_uuid=True), primary_key=True)
    tag_id     = db.Column(UUID(as_uuid=True), db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    weight     = db.Column(db.Numeric(5, 3), nullable=False, default=1.0)
    source     = db.Column(db.String(10), nullable=False, default="manual")  # 'manual' | 'inferred'
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    tag = db.relationship("Tag", back_populates="user_interests")


# ── SubjectArea (mirrors public.subject_areas) ────────────────────────────────
class SubjectArea(db.Model):
    __tablename__ = "subject_areas"

    id         = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug       = db.Column(db.Text, unique=True, nullable=False)
    label      = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)


# ── REAInteraction (mirrors public.rea_interactions) ──────────────────────────
class REAInteraction(db.Model):
    __tablename__ = "rea_interactions"

    id         = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = db.Column(UUID(as_uuid=True), nullable=False)
    rea_id     = db.Column(UUID(as_uuid=True), db.ForeignKey("reas.id", ondelete="CASCADE"), nullable=False)
    event_type = db.Column(db.String(30), nullable=False)
    value      = db.Column(db.Numeric(6, 3), nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    rea = db.relationship("REA", back_populates="interactions")


# ── REARating (mirrors public.rea_ratings) ────────────────────────────────────
class REARating(db.Model):
    __tablename__ = "rea_ratings"
    __table_args__ = (db.UniqueConstraint("rea_id", "user_id", name="uq_rea_rating_user"),)

    id         = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rea_id     = db.Column(UUID(as_uuid=True), db.ForeignKey("reas.id", ondelete="CASCADE"), nullable=False)
    user_id    = db.Column(UUID(as_uuid=True), nullable=False)
    rating     = db.Column(db.SmallInteger, nullable=False)
    comment    = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    rea = db.relationship("REA", back_populates="ratings")


# ── REAReport (mirrors public.rea_reports) ────────────────────────────────────
class REAReport(db.Model):
    __tablename__ = "rea_reports"
    __table_args__ = (db.UniqueConstraint("rea_id", "user_id", name="uq_rea_report_user"),)

    id          = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rea_id      = db.Column(UUID(as_uuid=True), db.ForeignKey("reas.id", ondelete="CASCADE"), nullable=False)
    user_id     = db.Column(UUID(as_uuid=True), nullable=False)
    reason      = db.Column(_pg_enum("report_reason",
                    "inappropriate", "broken_link", "copyright",
                    "misinformation", "spam", "other"),
                    nullable=False)
    details     = db.Column(db.Text)
    state       = db.Column(_pg_enum("report_state", "pending", "dismissed", "accepted"),
                    nullable=False, default="pending")
    resolved_by = db.Column(UUID(as_uuid=True), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at  = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    rea = db.relationship("REA", back_populates="reports")


# ── Collection (mirrors public.collections) ───────────────────────────────────
class Collection(db.Model):
    __tablename__ = "collections"

    id          = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = db.Column(UUID(as_uuid=True), nullable=False)
    title       = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    visibility  = db.Column(db.String(10), nullable=False, default="private")  # 'private' | 'public'
    cover_url   = db.Column(db.Text)
    is_system   = db.Column(db.Boolean, nullable=False, default=False)
    created_at  = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at  = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    items = db.relationship("CollectionItem", back_populates="collection", cascade="all, delete-orphan")


# ── CollectionItem (mirrors public.collection_items) ──────────────────────────
class CollectionItem(db.Model):
    __tablename__ = "collection_items"

    collection_id = db.Column(UUID(as_uuid=True), db.ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    rea_id        = db.Column(UUID(as_uuid=True), db.ForeignKey("reas.id", ondelete="CASCADE"), primary_key=True)
    position      = db.Column(db.Integer, nullable=False, default=0)
    note          = db.Column(db.Text)
    added_at      = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    collection = db.relationship("Collection", back_populates="items")
    rea        = db.relationship("REA", back_populates="collection_items")
