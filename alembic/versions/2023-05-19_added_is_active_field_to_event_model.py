"""added is_active field to event model

Revision ID: aad4257946b3
Revises: 3b34b34425da
Create Date: 2023-05-19 20:40:09.212151

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'aad4257946b3'
down_revision = '3b34b34425da'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event', sa.Column('is_active', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('event', 'is_active')
    # ### end Alembic commands ###
