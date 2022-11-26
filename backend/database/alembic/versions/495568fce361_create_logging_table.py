"""create logging table

Revision ID: 495568fce361
Revises: a8f74425bc3b
Create Date: 2022-11-24 17:41:14.612723

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '495568fce361'
down_revision = 'a8f74425bc3b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('children_api_logging',
                    sa.Column('request_id', UUID(as_uuid=True), primary_key=True, index=True, unique=True),
                    sa.Column('user_name', sa.String(15)),
                    sa.Column('endpoint', sa.String(120)),
                    sa.Column('method', sa.String(6)),
                    sa.Column('body', sa.String(1000)),
                    sa.Column('query', sa.String(200)),
                    sa.Column('request_timestamp', sa.DateTime()),
                    sa.Column('status_code', sa.Integer()),
                    sa.Column('response_timestamp', sa.DateTime()))


def downgrade():
    op.drop_table('children_api_logging')
