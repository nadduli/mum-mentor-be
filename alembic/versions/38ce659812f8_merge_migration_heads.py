"""merge migration heads

Revision ID: 38ce659812f8
Revises: 21c4c314e650, 5dff51f31b56, 855c207c427a, df5f0b5d9145, f95da4bafb56
Create Date: 2025-11-20 13:07:31.488464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38ce659812f8'
down_revision: Union[str, Sequence[str], None] = ('5dff51f31b56', '855c207c427a', 'df5f0b5d9145', 'f95da4bafb56')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
