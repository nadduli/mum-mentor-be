"""merge staging branch heads

Revision ID: 855c207c427a
Revises: 2fbb63c4da8f, e2068d715173
Create Date: 2025-11-19 20:51:16.350599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '855c207c427a'
down_revision: Union[str, Sequence[str], None] = ('2fbb63c4da8f', 'e2068d715173')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
