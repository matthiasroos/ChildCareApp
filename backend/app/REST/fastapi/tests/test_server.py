import asyncio

import fastapi.requests
import fastapi.testclient
import pydantic_factories
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.pool

import backend.app.REST.fastapi.server
import backend.app.REST.utils.testing
import backend.database.models
import backend.database.queries_v2
import backend.database.usermanagement


class ChildBaseFactory(pydantic_factories.ModelFactory):
    __model__ = backend.database.schemas.ChildBase


def override_get_db(test_db_name: str):
    def wrapper():
        engine = backend.app.REST.utils.testing.create_local_engine(test_db_name=test_db_name)
        session = sqlalchemy.orm.Session(autocommit=False, autoflush=False, bind=engine)
        try:
            yield session
        finally:
            session.close()
            engine.dispose()
    return wrapper


class TestingServer(backend.app.REST.utils.testing.TestingServer):

    def setUp(self):
        super().setUp()

        app = backend.app.REST.fastapi.server.app
        app.dependency_overrides[backend.app.REST.fastapi.server.get_db] = override_get_db(
            test_db_name=self.test_db_name)

        self.client = fastapi.testclient.TestClient(app)

    def tearDown(self) -> None:
        self.client = None

    def test_fetch_children(self):
        db_config = backend.database.queries_v2.get_database_config()
        db_config['database'] = self.test_db_name
        self.monkeypatch.setattr('backend.database.queries_v2.get_database_config',
                                 lambda **kwargs: db_config
                                 )
        response = self.client.get('/children',
                                   auth=(self.user, self.password))
        self.monkeypatch.undo()
        assert response.status_code == 200
