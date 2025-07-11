"""add_user_id_to_data_sources_table

Revision ID: 55140254014a
Revises: 866c454824bf
Create Date: 2025-07-08 08:06:29.794888

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55140254014a'
down_revision: Union[str, Sequence[str], None] = '866c454824bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Safely adds a nullable user_id column to the data_sources table and creates the foreign key.
    Making the column non-nullable will be handled in a subsequent migration
    after data has been backfilled.
    """
    op.add_column('data_sources', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_data_sources_user_id', 
        'data_sources', 
        'users', 
        ['user_id'], 
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_data_sources_user_id', 'data_sources', type_='foreignkey')
    op.drop_column('data_sources', 'user_id')
