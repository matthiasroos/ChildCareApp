import starlite.plugins.sql_alchemy
import starlite.testing

import backend.app.REST.starlite.server
import backend.app.REST.utils.testing
import backend.database.queries_v2


class TestingStarliteServer(backend.app.REST.utils.testing.TestingServer):

    def setUp(self):
        super().setUp()

        app = backend.app.REST.starlite.server.app

        db_user, db_password, db_host, _ = backend.database.queries_v2.get_database_config()
        app.plugins = [starlite.plugins.sql_alchemy.SQLAlchemyPlugin(
            config=starlite.plugins.sql_alchemy.SQLAlchemyConfig(
                connection_string=backend.database.queries_v2.create_connection_string(
                    db_config=(db_user, db_password, db_host, self.test_db_name)),
                use_async_engine=False,
                dependency_key='db')
        )]

        self.client = starlite.testing.TestClient(app=app)

    def tearDown(self) -> None:
        self.client = None

    def test_fetch_children(self):
        db_user, db_password, db_host, _ = backend.database.queries_v2.get_database_config()
        self.monkeypatch.setattr('backend.database.queries_v2.get_database_config',
                                 lambda **kwargs: (db_user, db_password, db_host, self.test_db_name)
                                 )
        response = self.client.get('/rest/starlite/v1/children',
                                   auth=(self.user, self.password))
        self.monkeypatch.undo()
        assert response.status_code == 200
