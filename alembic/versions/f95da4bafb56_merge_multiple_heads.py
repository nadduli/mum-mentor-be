"""merge multiple heads

Revision ID: f95da4bafb56
Revises: 2fbb63c4da8f, e2068d715173
Create Date: 2025-11-19 20:33:56.569941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f95da4bafb56'
down_revision: Union[str, Sequence[str], None] = ('2fbb63c4da8f', 'e2068d715173')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
