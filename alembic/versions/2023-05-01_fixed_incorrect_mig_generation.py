"""fixed incorrect mig generation

Revision ID: 88b145ec7d0b
Revises: 03dcb6b1f51c
Create Date: 2023-05-01 13:19:26.978630

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = '88b145ec7d0b'
down_revision = '03dcb6b1f51c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # ### end Alembic commands ###
    op.create_primary_key('refreshtoken_pkey', 'refreshtoken', ['user_id', 'value'])


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # ### end Alembic commands ###
    op.drop_constraint('refreshtoken_pkey', 'refreshtoken')