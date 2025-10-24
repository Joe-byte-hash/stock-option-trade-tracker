"""add_strategy_column_to_trades

Revision ID: 3f1aabbd2713
Revises: 
Create Date: 2025-10-24 02:24:45.192428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f1aabbd2713'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add strategy column to trades table."""
    # Add strategy column with default value 'untagged'
    op.add_column(
        'trades',
        sa.Column('strategy', sa.String(50), nullable=True, server_default='untagged')
    )


def downgrade() -> None:
    """Remove strategy column from trades table."""
    # Drop strategy column
    op.drop_column('trades', 'strategy')
