"""create caretimes table

Revision ID: f589d458cf2b
Revises: 9d438e832f83
Create Date: 2022-09-04 13:23:46.361432

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'f589d458cf2b'
down_revision = '9d438e832f83'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('caretimes',
                    sa.Column('child_id', UUID(as_uuid=True), primary_key=True, index=True),
                    sa.Column('start_time', sa.DateTime(), primary_key=True),
                    sa.Column('stop_time', sa.DateTime()),
                    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
                    sa.Column('modified_at', sa.DateTime(), server_default=sa.func.now(), server_onupdate=sa.func.now()))


def downgrade():
    op.drop_table('caretimes')
