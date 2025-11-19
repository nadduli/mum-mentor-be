"""make download_events.occurred_at timezone-aware

Revision ID: df5f0b5d9145
Revises: e3c1d12eae82
Create Date: 2025-11-19 14:19:06.654379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df5f0b5d9145'
down_revision: Union[str, Sequence[str], None] = 'e3c1d12eae82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: make occurred_at timezone-aware (TIMESTAMP WITH TIME ZONE)."""
    from alembic import op
    import sqlalchemy as sa
    # For Postgres, alter type with USING clause; for others (e.g., SQLite), skip if not supported
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.alter_column(
            "download_events",
            "occurred_at",
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
    else:
        # SQLite stores naive datetimes; keep schema compatible
        try:
            op.alter_column(
                "download_events",
                "occurred_at",
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
            )
        except Exception:
            pass


def downgrade() -> None:
    """Downgrade schema: revert to naive TIMESTAMP."""
    from alembic import op
    import sqlalchemy as sa
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.alter_column(
            "download_events",
            "occurred_at",
            type_=sa.DateTime(timezone=False),
            existing_nullable=False,
        )
    else:
        try:
            op.alter_column(
                "download_events",
                "occurred_at",
                type_=sa.DateTime(timezone=False),
                existing_nullable=False,
            )
        except Exception:
            pass
