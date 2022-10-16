import typing
import uuid

import sqlalchemy.orm
import starlette.status
import starlite
import starlite.enums
import starlite.plugins.sql_alchemy
import uvicorn

import backend.app.REST.starlite.guards
import backend.app.REST.starlite.middleware
import backend.app.REST.utils.json_handling
import backend.database.queries_v2
import backend.database.schemas


def not_authorized(request: starlite.Request, exc: Exception) -> starlite.Response:
    return starlite.Response(status_code=401,
                             content={'error': 'Not authorized'},
                             media_type=starlite.enums.MediaType.JSON,
                             headers={"WWW-Authenticate": "Basic"})


def forbidden(request: starlite.Request, exc: Exception) -> starlite.Response:
    return starlite.Response(status_code=403,
                             content={'error': 'Permission denied'},
                             media_type=starlite.enums.MediaType.JSON)


def not_found(request: starlite.Request, exc: Exception) -> starlite.Response:
    return starlite.Response(status_code=404,
                             content={'error': 'Item not found'},
                             media_type=starlite.enums.MediaType.JSON)


def server_error(request: starlite.Request, exc: Exception) -> starlite.Response:
    return starlite.Response(status_code=500,
                             content={'error': 'Server error'},
                             media_type=starlite.enums.MediaType.JSON)


class ChildrenController(starlite.Controller):
    """

    """
    path = '/rest/starlite/v1/children'

    @starlite.get()
    async def fetch_children(self, db: sqlalchemy.orm.Session, recent: bool = False, skip: int = 0, limit: int = 10)\
            -> typing.List[backend.database.schemas.Child]:
        """

        :return:
        """
        result = backend.database.queries_v2.fetch_children(db=db, recent=recent, skip=skip, limit=limit)
        return backend.app.REST.utils.json_handling.serialize_result(result=result)

    @starlite.get('/{child_id: uuid}')
    async def fetch_child(self, db: sqlalchemy.orm.Session, child_id: uuid.UUID) \
            -> backend.database.schemas.Child:
        """

        :return:
        """
        result = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
        if result:
            return backend.app.REST.utils.json_handling.serialize_result(result=result)
        raise starlite.NotFoundException()

    @starlite.post(status_code=starlette.status.HTTP_200_OK)
    async def fetch_one_child(self, db: sqlalchemy.orm.Session, data: dict) \
            -> backend.database.schemas.Child:
        """

        :return:
        """
        result = backend.database.queries_v2.fetch_child(db=db, child_id=data['child_id'])
        if result:
            return backend.app.REST.utils.json_handling.serialize_result(result=result)
        raise starlite.NotFoundException()


app = starlite.Starlite(route_handlers=[ChildrenController],
                        plugins=[starlite.plugins.sql_alchemy.SQLAlchemyPlugin(
                            config=starlite.plugins.sql_alchemy.SQLAlchemyConfig(
                                connection_string=backend.database.queries_v2.create_connection_string(
                                    db_config=backend.database.queries_v2.get_database_config()),
                                use_async_engine=False,
                                dependency_key='db')
                        )],
                        middleware=[backend.app.REST.starlite.middleware.BasicAuthMiddleware],
                        guards=[backend.app.REST.starlite.guards.admin_user_guard('admin')],
                        exception_handlers={starlette.status.HTTP_401_UNAUTHORIZED: not_authorized,
                                            starlette.status.HTTP_403_FORBIDDEN: forbidden,
                                            starlette.status.HTTP_404_NOT_FOUND: not_found,
                                            starlette.status.HTTP_500_INTERNAL_SERVER_ERROR: server_error})


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8085)
