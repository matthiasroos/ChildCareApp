import datetime

import pydantic_factories
import starlite.plugins.sql_alchemy
import starlite.testing

import backend.app.REST.starlite.server
import backend.app.REST.utils.testing
import backend.database.schemas
import backend.database.queries_v2


class ChildBaseFactory(pydantic_factories.ModelFactory):
    __model__ = backend.database.schemas.ChildBase


class TestingStarliteServer(backend.app.REST.utils.testing.TestingServer):

    def setUp(self):
        super().setUp()

        self.app = backend.app.REST.starlite.server.app

        db_config = backend.database.queries_v2.get_database_config()
        db_config['database'] = self.test_db_name
        self.app.plugins = [starlite.plugins.sql_alchemy.SQLAlchemyPlugin(
            config=starlite.plugins.sql_alchemy.SQLAlchemyConfig(
                engine_instance=backend.database.queries_v2.create_engine(
                    url=backend.database.queries_v2.create_url(
                        db_config=db_config)),
                use_async_engine=False,
                dependency_key='db')
        )]
        self.app.plugins[0].on_app_init(app=self.app)
        self.client = starlite.testing.TestClient(app=self.app)

    def tearDown(self) -> None:
        self.client = None

    def test_create_child(self):
        db_config = backend.database.queries_v2.get_database_config()
        db_config['database'] = self.test_db_name
        self.monkeypatch.setattr('backend.database.queries_v2.get_database_config',
                                 lambda **kwargs: db_config
                                 )
        child = ChildBaseFactory.build().json()
        response = self.client.post('/rest/starlite/v1/children/create',
                                    content=child,
                                    auth=(self.user, self.password))
        self.monkeypatch.undo()
        assert response.status_code == 201

    def test_fetch_children(self):
        db_config = backend.database.queries_v2.get_database_config()
        db_config['database'] = self.test_db_name
        self.monkeypatch.setattr('backend.database.queries_v2.get_database_config',
                                 lambda **kwargs: db_config
                                 )
        response = self.client.get('/rest/starlite/v1/children',
                                   auth=(self.user, self.password))
        self.monkeypatch.undo()
        assert response.status_code == 200
        assert len(response.json()) == 1
