import typing
import uuid

import sqlalchemy.orm
import starlette.status
import starlite
import uvicorn

import backend.app.REST.starlite.middleware
import backend.app.REST.utils
import backend.database.queries_v2
import backend.database.schemas


def get_db() -> sqlalchemy.orm.Session:
    """

    :return:
    """
    db_config = backend.database.queries_v2.get_database_config()
    db = backend.database.queries_v2.create_session(db_config=db_config)
    return db


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
        return backend.app.REST.utils.serialize_result(result=result)

    @starlite.get('/{child_id: uuid}')
    async def fetch_child(self, db: sqlalchemy.orm.Session, child_id: uuid.UUID) \
            -> backend.database.schemas.Child:
        """

        :return:
        """
        result = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
        if result:
            return backend.app.REST.utils.serialize_result(result=result)
        return None
        # TODO: error handling

    @starlite.post(status_code=starlette.status.HTTP_200_OK)
    async def fetch_one_child(self, db: sqlalchemy.orm.Session, data: dict) \
            -> backend.database.schemas.Child:
        """

        :return:
        """
        result = backend.database.queries_v2.fetch_child(db=db, child_id=data['child_id'])
        if result:
            return backend.app.REST.utils.serialize_result(result=result)
        return None
        # TODO: error handling


app = starlite.Starlite(route_handlers=[ChildrenController],
                        dependencies={'db': starlite.Provide(get_db)},
                        middleware=[backend.app.REST.starlite.middleware.BasicAuthMiddleware])


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8085)