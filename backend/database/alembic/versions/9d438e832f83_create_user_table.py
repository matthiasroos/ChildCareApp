"""create user table

Revision ID: 9d438e832f83
Revises: 295eec3a4826
Create Date: 2022-09-03 15:10:04.544022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d438e832f83'
down_revision = '295eec3a4826'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
                    sa.Column('user_name', sa.String(15), primary_key=True, index=True, unique=True),
                    sa.Column('salt', sa.String(16)),
                    sa.Column('hashed_password', sa.String(128)))


def downgrade():
    op.drop_table('users')
