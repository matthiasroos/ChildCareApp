import os
import typing
import uuid

import dotenv
import sqlalchemy
import sqlalchemy.orm

import database.models


def create_connection():
    """

    :return:
    """
    dotenv.load_dotenv()
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_host = os.environ.get('DB_HOST')
    db_schema = os.environ.get('DB_SCHEMA')
    engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_schema}')
    connection = engine.connect()

    return connection


def fetch_user(user_name: str):
    """
    Fetch user.

    :param user_name:
    :return:
    """
    connection = create_connection()
    user_model = database.models.User
    with sqlalchemy.orm.Session(connection) as session:
        user = session.execute(
            sqlalchemy.sql.select(
                from_obj=user_model,
                columns=user_model.__table__.columns,
            ).where(user_model.user_name == user_name)
        ).first()
    return user


def create_user(user: dict):
    """

    :param user:
    :return:
    """
    connection = create_connection()
    with sqlalchemy.orm.Session(connection) as session:
        session.execute(sqlalchemy.insert(database.models.User).values(**user))
        session.commit()
    return


def fetch_children(recent: bool, limit: int):
    """
    Fetch all children.

    :param recent:
    :param limit:
    :return:
    """
    connection = create_connection()
    child_model = database.models.Child
    with sqlalchemy.orm.Session(connection) as session:
        children = session.execute(
            sqlalchemy.sql.select(
                from_obj=child_model,
                columns=child_model.__table__.columns,
            ),
        ).all()
    return [child for child in children][:limit]


def create_child(child: dict):
    """


    :param child:
    :return:
    """
    connection = create_connection()
    with sqlalchemy.orm.Session(connection) as session:
        session.execute(sqlalchemy.insert(database.models.Child).values(**child))
        session.commit()
    return


def fetch_child(child_id: uuid.UUID):
    """


    :param child_id:
    :return:
    """
    connection = create_connection()
    child_model = database.models.Child
    with sqlalchemy.orm.Session(connection) as session:
        child = session.execute(
            sqlalchemy.sql.select(
                from_obj=child_model,
                columns=child_model.__table__.columns,
            ).where(child_model.child_id == child_id)
        ).first()
    return child


def update_child(child_id: uuid.UUID, updates_for_child: typing.Dict):
    """


    :param child_id:
    :param updates_for_child:
    :return:
    """
    connection = create_connection()
    child_model = database.models.Child
    with sqlalchemy.orm.Session(connection) as session:
        session.execute(sqlalchemy.update(child_model).where(child_model.child_id == child_id)
                        .values(**updates_for_child))
        session.commit()
    return


def delete_child(child_id: uuid.UUID):
    """

    :param child_id:
    :return:
    """
    connection = create_connection()
    child_model = database.models.Child
    with sqlalchemy.orm.Session(connection) as session:
        session.execute(sqlalchemy.delete(child_model).where(child_model.child_id == child_id))
        session.commit()
