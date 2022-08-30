import os
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


def get_children(recent: bool, limit: int):
    """
    Fetch all children.

    :param recent:
    :param limit:
    :return:
    """
    connection = create_connection()
    model = database.models.Child
    with sqlalchemy.orm.Session(connection) as session:
        children = session.execute(
            sqlalchemy.sql.select(
                from_obj=model,
                columns=model.__table__.columns,
            ),
        ).all()
    return [child for child in children][:limit]


def post_children(child: dict):
    """


    :param child:
    :return:
    """
    connection = create_connection()
    with sqlalchemy.orm.Session(connection) as session:
        session.execute(sqlalchemy.insert(database.models.Child).values(child_id=child['child_id'],
                                                                        name=child['name'],
                                                                        sur_name=child['sur_name'],
                                                                        birth_day=child['birth_day']))
        session.commit()
    return


def get_child(child_id: uuid.UUID):
    """


    :param child_id:
    :return:
    """
    connection = create_connection()
    model = database.models.Child
    with sqlalchemy.orm.Session(connection) as session:
        child = session.execute(
            sqlalchemy.sql.select(
                from_obj=model,
                columns=model.__table__.columns,
            ).where(model.child_id == child_id)
        ).first()
    return child


def put_child(child_id: int, changed_attributes: dict):
    """


    :param child_id:
    :return:
    """
    # child_dict = CHILDREN[child_id]
    # child_dict.update({key: value for key, value in changed_attributes.items()})
    # CHILDREN.update(child_dict)
    return 'OK', 200
