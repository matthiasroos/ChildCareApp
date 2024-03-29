import os
import typing
import uuid

import dotenv
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.pool

import backend.database.models


def get_database_config() -> dict[str, str]:
    """

    :return:
    """
    dotenv.load_dotenv()
    db_config = dict()

    db_config['username'] = os.environ.get('DB_USER')
    db_config['password'] = os.environ.get('DB_PASSWORD')
    db_config['host'] = os.environ.get('DB_HOST')
    db_config['port'] = os.environ.get('DB_PORT')
    db_config['database'] = os.environ.get('DB_SCHEMA')
    return db_config


def create_url(db_config: dict[str, str]) -> sqlalchemy.engine.url.URL:
    """

    :return:
    """
    db_config['drivername'] = 'postgresql+psycopg2'
    url = sqlalchemy.engine.url.URL.create(**db_config)
    return url


def create_engine(url: sqlalchemy.engine.url.URL) -> sqlalchemy.engine.Engine:
    """

    :return:
    """
    engine = sqlalchemy.create_engine(url, poolclass=sqlalchemy.pool.NullPool)
    return engine


def create_session(db_config: dict[str, str]) -> sqlalchemy.orm.Session:
    """

    :return:
    """
    engine = create_engine(create_url(db_config=db_config))
    session = sqlalchemy.orm.Session(autocommit=False, autoflush=False, bind=engine)

    return session


def fetch_user(db: sqlalchemy.orm.Session, user_name: str):
    """
    Fetch user.

    :param db:
    :param user_name:
    :return:
    """
    user_model = backend.database.models.User
    return db.execute(
            sqlalchemy.sql.select(
                from_obj=user_model,
                columns=user_model.__table__.columns).
            where(user_model.user_name == user_name)).\
        first()


def create_user(db: sqlalchemy.orm.Session, user: dict):
    """

    :param db:
    :param user:
    :return:
    """
    db.execute(sqlalchemy.insert(backend.database.models.User).values(**user))
    db.commit()
    return


def edit_user(db: sqlalchemy.orm.Session, user_name: str, new_values: typing.Dict[str, typing.Any]):
    """

    :param db:
    :param user_name:
    :param new_values:
    :return:
    """
    db.execute(sqlalchemy.update(backend.database.models.User).
               where(backend.database.models.User.user_name == user_name).
               values(**new_values))
    db.commit()
    return


def write_logging(db: sqlalchemy.orm.Session, log_entry: dict, insert: bool):
    """

    :param db:
    :param log_entry:
    :param insert:
    :return:
    """
    if insert:
        db.execute(sqlalchemy.insert(backend.database.models.Log).values(**log_entry))
    else:
        db.execute(sqlalchemy.update(backend.database.models.Log).
                   where(backend.database.models.Log.request_id == log_entry['request_id']).
                   values(**log_entry))
    db.commit()
    return


def fetch_children(db: sqlalchemy.orm.Session, recent: bool = False, skip: int = 0, limit: int = 10):
    """
    Fetch all children.

    :param db:
    :param recent: boolean flag for fetching only recent children, default: False; currently unused
    :param skip:
    :param limit:
    :return:
    """
    child_model = backend.database.models.Child
    return db.execute(
        sqlalchemy.sql.select(
            from_obj=child_model,
            columns=child_model.__table__.columns).
        where(1 == 1).offset(skip).limit(limit)).all()


def create_child(db: sqlalchemy.orm.Session, child: dict):
    """

    :param db:
    :param child:
    :return:
    """
    db.execute(sqlalchemy.insert(backend.database.models.Child).values(**child))
    db.commit()
    return


def fetch_child(db: sqlalchemy.orm.Session, child_id: uuid.UUID):
    """

    :param db:
    :param child_id:
    :return:
    """
    child_model = backend.database.models.Child
    return db.execute(
        sqlalchemy.sql.select(
            from_obj=child_model,
            columns=child_model.__table__.columns).
        where(child_model.child_id == child_id)).first()


def update_child(db: sqlalchemy.orm.Session, child_id: uuid.UUID, updates_for_child: typing.Dict):
    """

    :param db:
    :param child_id:
    :param updates_for_child:
    :return:
    """
    child_model = backend.database.models.Child
    db.execute(sqlalchemy.update(child_model).
               where(child_model.child_id == child_id).
               values(**updates_for_child))
    db.commit()
    return


def delete_child(db: sqlalchemy.orm.Session, child_id: uuid.UUID):
    """

    :param db:
    :param child_id:
    :return:
    """
    child_model = backend.database.models.Child
    db.execute(sqlalchemy.delete(child_model).where(child_model.child_id == child_id))
    db.commit()
    return


def fetch_caretimes(db: sqlalchemy.orm.Session, child_id: uuid.UUID, skip: int = 0, limit: int = 10):
    """

    :param db:
    :param child_id:
    :param skip:
    :param limit:
    :return:
    """
    caretime_model = backend.database.models.Caretime
    return db.execute(
        sqlalchemy.sql.select(
            from_obj=caretime_model,
            columns=caretime_model.__table__.columns).
        where(caretime_model.child_id == child_id).offset(skip).limit(limit)).all()


def fetch_single_caretime(db: sqlalchemy.orm.Session, caretime_id: uuid.UUID, child_id: uuid.UUID):
    """

    :param db:
    :param caretime_id:
    :param child_id:
    :return:
    """
    caretime_model = backend.database.models.Caretime
    return db.execute(
        sqlalchemy.sql.select(
            from_obj=caretime_model,
            columns=caretime_model.__table__.columns).
        where(caretime_model.child_id == child_id, caretime_model.caretime_id == caretime_id)).first()


def create_caretime(db: sqlalchemy.orm.Session, caretime_entry: dict):
    """

    :param db:
    :param caretime_entry:
    :return:
    """
    db.execute(sqlalchemy.insert(backend.database.models.Caretime).values(**caretime_entry))
    db.commit()
    return


def edit_caretime(db: sqlalchemy.orm.Session, caretime_entry: dict):
    """

    :param db:
    :param caretime_entry:
    :return:
    """
    caretime_model = backend.database.models.Caretime
    db.execute(
        sqlalchemy.update(caretime_model).
        where(caretime_model.child_id == caretime_entry['child_id'],
              caretime_model.caretime_id == caretime_entry['caretime_id'],
              ).
        values(**caretime_entry))
    db.commit()
    return


def delete_caretime(db: sqlalchemy.orm.Session, caretime_id: uuid.UUID, child_id: uuid.UUID):
    """

    :param db:
    :param caretime_id:
    :param child_id:
    :return:
    """
    caretime_model = backend.database.models.Caretime
    db.execute(sqlalchemy.delete(
        caretime_model).
               where(
        caretime_model.caretime_id == caretime_id,
        caretime_model.child_id == child_id,
    ))
    db.commit()
    return
