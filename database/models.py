import uuid

import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlalchemy.orm


Base = sqlalchemy.orm.declarative_base()


class Child(Base):
    """
    Table Children
    """
    __tablename__ = 'children'

    child_id = sqlalchemy.Column(
        sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name = sqlalchemy.Column(sqlalchemy.String)
    sur_name = sqlalchemy.Column(sqlalchemy.String)
    birth_day = sqlalchemy.Column(sqlalchemy.Date)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime)
