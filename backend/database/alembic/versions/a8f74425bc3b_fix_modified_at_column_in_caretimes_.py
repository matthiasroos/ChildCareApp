"""fix modified_at column in caretimes table

Revision ID: a8f74425bc3b
Revises: 8d0826b83426
Create Date: 2022-10-01 12:34:30.509990

"""
import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8f74425bc3b'
down_revision = '8d0826b83426'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('caretimes', 'modified_at', server_onupdate=None)


def downgrade():
    op.alter_column('caretimes', 'modified_at', server_onupdate=sa.func.now())
