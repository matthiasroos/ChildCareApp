import uuid

import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlalchemy.orm


Base = sqlalchemy.orm.declarative_base()


class User(Base):
    """
    Table Users
    """
    __tablename__ = 'users'

    user_name = sqlalchemy.Column(sqlalchemy.String, primary_key=True, unique=True, index=True)
    salt = sqlalchemy.Column(sqlalchemy.String)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)


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


class Caretime(Base):
    """
    Table Caretimes
    """
    __tablename__ = 'caretimes'

    caretime_id = sqlalchemy.Column(
        sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id = sqlalchemy.Column(sqlalchemy.dialects.postgresql.UUID(as_uuid=True))
    start_time = sqlalchemy.Column(sqlalchemy.DateTime)
    stop_time = sqlalchemy.Column(sqlalchemy.DateTime)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime)
    modified_at = sqlalchemy.Column(sqlalchemy.DateTime)
