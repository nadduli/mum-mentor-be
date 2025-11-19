"""Add download_events table

Revision ID: add_download_events_table
Revises: dee5c4df7914
Create Date: 2025-11-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_download_events_table'
down_revision: Union[str, Sequence[str], None] = 'c3698ef51d6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'download_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('download_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_url', sa.Text(), nullable=True),
        sa.Column('referrer', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_download_events_user_id', 'download_events', ['user_id'])
    op.create_index('idx_download_events_download_type', 'download_events', ['download_type'])
    op.create_index('idx_download_events_occurred_at', 'download_events', ['occurred_at'])


def downgrade() -> None:
    op.drop_index('idx_download_events_occurred_at', table_name='download_events')
    op.drop_index('idx_download_events_download_type', table_name='download_events')
    op.drop_index('idx_download_events_user_id', table_name='download_events')
    op.drop_table('download_events')
