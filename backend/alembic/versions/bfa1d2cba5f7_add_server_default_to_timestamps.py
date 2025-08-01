"""add_server_default_to_timestamps

Revision ID: bfa1d2cba5f7
Revises: 352d6933526e
Create Date: 2025-07-07 17:52:09.287065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfa1d2cba5f7'
down_revision: Union[str, Sequence[str], None] = '352d6933526e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('data_sources',
                    'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text('now()'))
    op.alter_column('data_sources',
                    'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text('now()'))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('data_sources',
                    'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True,
                    server_default=None)
    op.alter_column('data_sources',
                    'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True,
                    server_default=None)
    # ### end Alembic commands ###
