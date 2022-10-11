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

    user_name = sqlalchemy.Column(sqlalchemy.String(15), primary_key=True, unique=True, index=True)
    salt = sqlalchemy.Column(sqlalchemy.String(16))
    hashed_password = sqlalchemy.Column(sqlalchemy.String(128))
    role = sqlalchemy.Column(sqlalchemy.String(15))


class Child(Base):
    """
    Table Children
    """
    __tablename__ = 'children'

    child_id = sqlalchemy.Column(
        sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, index=True, unique=True
    )
    name = sqlalchemy.Column(sqlalchemy.String(20))
    sur_name = sqlalchemy.Column(sqlalchemy.String(20))
    birth_day = sqlalchemy.Column(sqlalchemy.Date())
    created_at = sqlalchemy.Column(sqlalchemy.DateTime(), server_default=sqlalchemy.func.now())


class Caretime(Base):
    """
    Table Caretimes
    """
    __tablename__ = 'caretimes'

    caretime_id = sqlalchemy.Column(
        sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, index=True, unique=True
    )
    child_id = sqlalchemy.Column(sqlalchemy.dialects.postgresql.UUID(as_uuid=True))
    start_time = sqlalchemy.Column(sqlalchemy.DateTime())
    stop_time = sqlalchemy.Column(sqlalchemy.DateTime())
    created_at = sqlalchemy.Column(sqlalchemy.DateTime(),
                                   server_default=sqlalchemy.func.now())
    modified_at = sqlalchemy.Column(sqlalchemy.DateTime(),
                                    server_default=sqlalchemy.func.now(),
                                    onupdate=sqlalchemy.func.now())
