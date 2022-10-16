
import functools
import typing
import unittest.mock


import psycopg2
import psycopg2.sql
import pytest
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.pool

import backend.database.models
import backend.database.queries_v2
import backend.database.usermanagement


SQL_COMMANDS = {'db_exits': psycopg2.sql.SQL("""SELECT datname from pg_database WHERE datname = (%s);"""),
                'create_db': psycopg2.sql.SQL("""CREATE DATABASE {};"""),
                'drop_db': psycopg2.sql.SQL("""DROP DATABASE {};""")}


def provide_cursor(func: typing.Callable) -> typing.Callable:
    """decorator to provide a cursor"""
    @functools.wraps(func)
    def wrapper(**kwargs):
        db_user, db_password, db_host, db_schema = backend.database.queries_v2.get_database_config()
        conn = psycopg2.connect(database=db_schema,
                                user=db_user,
                                password=db_password,
                                host=db_host)
        conn.autocommit = True
        cursor = conn.cursor()
        func(cursor=cursor, **kwargs)
        cursor.close()
        conn.close()
    return wrapper


@provide_cursor
def create_testing_db_schema(test_db_name: str, cursor):
    cursor.execute(SQL_COMMANDS['db_exits'], (test_db_name, ))
    result = cursor.fetchone()
    if result:
        cursor.execute(SQL_COMMANDS['drop_db'].format(psycopg2.sql.Identifier(test_db_name)))
    cursor.execute(SQL_COMMANDS['create_db'].format(psycopg2.sql.Identifier(test_db_name)))


@provide_cursor
def destroy_testing_db_schema(test_db_name: str, cursor):
    cursor.execute(SQL_COMMANDS['drop_db'].format(psycopg2.sql.Identifier(test_db_name)))


def create_local_engine(test_db_name: str):
    db_user, db_password, db_host, _ = backend.database.queries_v2.get_database_config()
    engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{test_db_name}',
                                      poolclass=sqlalchemy.pool.NullPool)
    return engine


class TestingServer(unittest.TestCase):

    test_db_name = 'jqngxgdxla'
    user = 'test_user'
    password = 'foqAZ5Fi3zHyJaBICV6h'
    client = None

    @classmethod
    def setUpClass(cls) -> None:
        create_testing_db_schema(test_db_name=cls.test_db_name)

        # create engine and session
        engine = create_local_engine(test_db_name=cls.test_db_name)
        session = sqlalchemy.orm.Session(autocommit=False, autoflush=False, bind=engine, future=True)

        # create tables
        backend.database.models.Base.metadata.create_all(bind=engine)

        # add user
        backend.database.usermanagement.create_new_user(db=session,
                                                        user_name=cls.user,
                                                        password=cls.password,
                                                        role='admin')
        session.close()
        engine.dispose()

    @classmethod
    def tearDownClass(cls) -> None:
        destroy_testing_db_schema(test_db_name=cls.test_db_name)

    def setUp(self):
        self.monkeypatch = pytest.MonkeyPatch()
