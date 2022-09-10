"""create children table

Revision ID: 295eec3a4826
Revises:
Create Date: 2022-08-18 19:45:43.994198

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '295eec3a4826'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('children',
                    sa.Column('child_id', UUID(as_uuid=True), primary_key=True, index=True, unique=True),
                    sa.Column('name', sa.String(20)),
                    sa.Column('sur_name', sa.String(20)),
                    sa.Column('birth_day', sa.Date),
                    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()))


def downgrade():
    op.drop_table('children')
