"""add role column to user table

Revision ID: 8d0826b83426
Revises: f589d458cf2b
Create Date: 2022-09-09 18:49:15.746027

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d0826b83426'
down_revision = 'f589d458cf2b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users',
                  sa.Column('role', sa.String(15)))


def downgrade():
    op.drop_column('users', 'role')
