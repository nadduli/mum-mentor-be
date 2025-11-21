"""merge heads (download-tracking + dev)

Revision ID: e3c1d12eae82
Revises: 2fbb63c4da8f, add_download_events_table
Create Date: 2025-11-19 14:07:04.413785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3c1d12eae82'
down_revision: Union[str, Sequence[str], None] = ('2fbb63c4da8f', 'add_download_events_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
