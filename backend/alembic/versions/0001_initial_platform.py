"""initial platform schema with tenant RLS

Revision ID: 0001_initial_platform
Revises:
Create Date: 2026-06-19
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_initial_platform"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True, index=True),
        sa.Column("plan", sa.String(length=32), nullable=False, server_default="free", index=True),
        sa.Column("payment_status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True, unique=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
    "processed_webhooks",
    sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    ),
    sa.Column(
        "event_id",
        sa.String(length=255),
        nullable=False,
        unique=True,
    ),
    sa.Column(
        "processed_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    ),
    )
    
    op.create_table(
    "audit_logs",
    sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    ),
    sa.Column(
        "tenant_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "event_type",
        sa.String(length=100),
        nullable=False,
    ),
    sa.Column(
        "event_data",
        sa.Text(),
        nullable=True,
    ),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    ),
    )
    
    op.create_table(
    "subscription_history",
    sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    ),
    sa.Column(
        "tenant_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "previous_plan",
        sa.String(length=32),
        nullable=True,
    ),
    sa.Column(
        "new_plan",
        sa.String(length=32),
        nullable=False,
    ),
    sa.Column(
        "changed_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    ),
)
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("prefix", sa.String(length=32), nullable=False, unique=True, index=True),
        sa.Column("key_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True),
        sa.Column("endpoint", sa.String(length=255), nullable=False, index=True),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False, index=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
    )

    op.create_table(
        "tenant_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.execute("ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE api_keys FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE usage_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE usage_events FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE tenant_documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant_documents FORCE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY tenant_api_keys_isolation ON api_keys
        USING (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.allow_api_key_lookup', true) = 'on'
        )
        WITH CHECK (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.allow_api_key_lookup', true) = 'on'
        )
        """
    )
    op.execute(
        """
        CREATE POLICY tenant_usage_events_isolation ON usage_events
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
        """
    )
    op.execute(
        """
        CREATE POLICY tenant_documents_isolation ON tenant_documents
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
        """
    )


def downgrade() -> None:
    op.drop_table("subscription_history")
    op.drop_table("audit_logs")
    op.drop_table("processed_webhooks")
    op.drop_table("tenant_documents")
    op.drop_table("usage_events")
    op.drop_table("api_keys")
    op.drop_table("tenants")
