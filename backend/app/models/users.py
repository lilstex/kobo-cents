import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import metadata

# Sub-phase 1.1: identity and account tables, per
# docs/backend-architecture/03-phases.md. Session handling is
# Redis-only per 01.md, deliberately no session table here.

users = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("email", String, nullable=False, unique=True),
    Column("password_hash", String, nullable=False),
    Column("email_verified", Boolean, nullable=False, default=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    # Which version of the legal terms this user accepted, and when,
    # per frontend-architecture/04-landing-page-indepth.md. Stamped at
    # signup (Phase 2), nullable here since the column exists before
    # the endpoint that fills it does.
    Column("terms_accepted_version", String, nullable=True),
    Column("terms_accepted_at", DateTime(timezone=True), nullable=True),
)


def _single_use_token_columns() -> list[Column]:
    """Shared shape for verification_tokens and password_reset_tokens,
    per 00.md's security section: single-use, hashed, never the raw
    token stored, expiry timestamp."""
    return [
        Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
        Column("token_hash", String, nullable=False),
        Column("expires_at", DateTime(timezone=True), nullable=False),
        Column("used_at", DateTime(timezone=True), nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    ]


verification_tokens = Table("verification_tokens", metadata, *_single_use_token_columns())
password_reset_tokens = Table("password_reset_tokens", metadata, *_single_use_token_columns())
