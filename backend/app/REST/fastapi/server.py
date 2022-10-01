import base64
import datetime
import threading
import typing
import uuid

import fastapi
import fastapi.requests
import fastapi.responses
import fastapi.security
import requests
import sqlalchemy.orm
import starlette.authentication
import starlette.middleware.authentication
import starlette.requests
import starlette.types
import uvicorn

import backend.database.queries
import backend.database.queries_v2
import backend.database.schemas
import backend.database.usermanagement


def get_db():
    """

    :return:
    """
    db_config = backend.database.queries_v2.get_database_config()
    db = backend.database.queries_v2.create_session(db_config=db_config)
    try:
        yield db
    finally:
        db.close()


async def forbidden(request: fastapi.Request, exc: fastapi.HTTPException):
    return fastapi.responses.JSONResponse(status_code=403, content={'error': 'Permission denied'})


async def not_found(request: fastapi.Request, exc: fastapi.HTTPException):
    return fastapi.responses.JSONResponse(status_code=404, content={'error': 'Item not found'})


async def server_error(request: fastapi.Request, exc: fastapi.HTTPException):
    return fastapi.responses.JSONResponse(status_code=500, content={'error': 'Server error'})


exception_handlers = {
    403: forbidden,
    404: not_found,
    500: server_error,
}

app = fastapi.FastAPI(root_path='/rest/fastapi/v1', dependencies=[fastapi.Depends(get_db)],
                      exception_handlers=exception_handlers)


class CloneRequestMiddleware:
    """
    Middleware for cloning the request (sending them to another server)
    Implementation is following:
    https://github.com/encode/starlette/pull/1519#issuecomment-1060633787
    """

    def __init__(self, app: starlette.types.ASGIApp, servers: typing.List[str]) -> None:
        self.app = app
        self.servers = servers

    async def __call__(self, scope: starlette.types.Scope, receive: starlette.types.Receive,
                       send: starlette.types.Send) -> None:
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        kw_args = {'method': scope['method'],
                   'params': scope['query_string'],
                   'headers': dict(scope['headers'])}
        if scope['method'] in ('POST', 'PUT', ):
            messages = []
            more_body = True
            while more_body:
                message = await receive()
                messages.append(message)
                more_body = message.get('more_body', False)

            body = b''.join([message.get('body', b'') for message in messages])
            kw_args.update({'data': body})

        for server in self.servers:
            kw_args.update({'url': f'http://{server}{scope["path"]}'})
            thread = threading.Thread(target=requests.request, kwargs=kw_args)

            thread.start()

        # Dispatch to the ASGI callable
        async def wrapped_receive():
            # First up we want to return any messages we've stashed.
            if messages:
                return messages.pop(0)

            # Once that's done we can just await any other messages.
            return await receive()

        await self.app(scope, wrapped_receive, send)


# app.add_middleware(CloneRequestMiddleware, servers=['http://localhost:8000/rest/flask/v2', ])


class BasicAuthBackend(starlette.authentication.AuthenticationBackend):
    """
    Backend for Basic Authentication
    """

    async def authenticate(self, conn: fastapi.requests.HTTPConnection) \
            -> typing.Optional[typing.Tuple[starlette.authentication.AuthCredentials,
                                            starlette.authentication.BaseUser]]:
        """

        :param conn:
        :return:
        """
        if 'Authorization' not in conn.headers:
            raise starlette.authentication.AuthenticationError('Invalid credentials')

        db_config = backend.database.queries_v2.get_database_config()
        db = backend.database.queries_v2.create_session(db_config=db_config)

        auth_header = conn.headers['Authorization']
        username, password = base64.b64decode(auth_header.split()[1]).split(b':')

        authenticated, role = backend.database.usermanagement.authenticate_user(db=db,
                                                                                user_name=username.decode('utf-8'),
                                                                                password=password.decode('utf-8'))
        if not authenticated:
            raise starlette.authentication.AuthenticationError('Invalid credentials')
        return starlette.authentication.AuthCredentials([role]), \
            starlette.authentication.SimpleUser(username)


def on_auth_error(conn: fastapi.requests.HTTPConnection, exc: Exception) -> fastapi.Response:
    """function executed on error"""
    return fastapi.responses.JSONResponse(status_code=401, content={'error': 'Not authorized'},
                                          headers={"WWW-Authenticate": "Basic"})


app.add_middleware(starlette.middleware.authentication.AuthenticationMiddleware,
                   backend=BasicAuthBackend(),
                   on_error=on_auth_error)


#@app.middleware('http')
async def authenticate_user(request: fastapi.Request, call_next: typing.Callable):
    """

    :return:
    """
    db_config = backend.database.queries_v2.get_database_config()
    db = backend.database.queries_v2.create_session(db_config=db_config)
    username, password = base64.b64decode(request.headers.get('authorization').split()[1]).split(b':')
    authenticated, role = backend.database.usermanagement.authenticate_user(db=db,
                                                                            user_name=username.decode('utf-8'),
                                                                            password=password.decode('utf-8'))
    if not authenticated or role != 'admin':
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    response = await call_next(request)
    return response


@app.get('/children', response_model=typing.List[backend.database.schemas.Child])
@starlette.authentication.requires(['admin'])
async def fetch_children(request: fastapi.Request, recent: bool = False, skip: int = 0, limit: int = 10,
                         db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    result = backend.database.queries_v2.fetch_children(db=db, recent=recent, skip=skip, limit=limit)
    return result


@app.get('/children/{child_id}', response_model=backend.database.schemas.Child)
@starlette.authentication.requires(['admin'])
async def fetch_child(request: fastapi.Request, child_id: uuid.UUID = fastapi.Path(..., title='ID of the child to get'),
                      db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    result = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
    if result:
        return result
    raise fastapi.HTTPException(status_code=404)


@app.post('/children', response_model=backend.database.schemas.Child)
@starlette.authentication.requires(['admin'])
async def fetch_one_child(request: fastapi.Request, body: dict, db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    result = backend.database.queries_v2.fetch_child(db=db, child_id=body['child_id'])
    if result:
        return result
    raise fastapi.HTTPException(status_code=404)


@app.post('/children/create', status_code=fastapi.status.HTTP_201_CREATED)
@starlette.authentication.requires(['admin'])
async def create_child(request: fastapi.Request, child: backend.database.schemas.ChildBase,
                       db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    child_id = uuid.uuid4()
    child_dict = child.dict()
    child_dict['child_id'] = child_id
    _ = backend.database.queries_v2.create_child(db=db, child=child_dict)
    return child_id


@app.put('/children/{child_id}/update')
@starlette.authentication.requires(['admin'])
async def update_child(request: fastapi.Request, child_id: uuid.UUID,
                       updates_for_child: backend.database.schemas.ChildUpdate,
                       db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    updates_dict = {key: values for key, values in updates_for_child.dict().items() if values is not None}
    _ = backend.database.queries_v2.update_child(db=db, child_id=child_id, updates_for_child=updates_dict)
    # TODO: error handling
    return


@app.delete('/children/{child_id}/delete')
@starlette.authentication.requires(['admin'])
async def delete_child(request: fastapi.Request,
                       child_id: uuid.UUID,
                       db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    backend.database.queries_v2.delete_child(db=db, child_id=child_id)
    # TODO: error handling
    return


@app.get('/children/{child_id}/caretimes', response_model=typing.List[backend.database.schemas.Caretime])
@starlette.authentication.requires(['admin'])
async def fetch_caretimes(request: fastapi.Request,
                          child_id: uuid.UUID,
                          skip: int = 0,
                          limit: int = 10,
                          db: sqlalchemy.orm.Session = fastapi.Depends(get_db),
                          ):
    """

    :return:
    """
    result = backend.database.queries_v2.fetch_caretimes(db=db, child_id=child_id, skip=skip, limit=limit)
    return result


@app.get('/children/{child_id}/caretimes/{caretime_id}', response_model=backend.database.schemas.Caretime)
@starlette.authentication.requires(['admin'])
async def fetch_single_caretime(request: fastapi.Request,
                                child_id: uuid.UUID,
                                caretime_id: uuid.UUID,
                                db: sqlalchemy.orm.Session = fastapi.Depends(get_db),
                                ):
    """

    :return:
    """
    result = backend.database.queries_v2.fetch_single_caretime(db=db, child_id=child_id, caretime_id=caretime_id)
    if result:
        return result
    raise fastapi.HTTPException(status_code=404)


@app.post('/children/{child_id}/caretimes', status_code=fastapi.status.HTTP_201_CREATED)
@starlette.authentication.requires(['admin'])
async def add_caretime(request: fastapi.Request,
                       child_id: uuid.UUID,
                       time_interval: backend.database.schemas.CaretimeBase,
                       db: sqlalchemy.orm.Session = fastapi.Depends(get_db),
                       ):
    """

    :return:
    """
    child = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
    if not child:
        raise fastapi.HTTPException(status_code=404)

    caretime_id = uuid.uuid4()
    caretime_entry = dict()
    caretime_entry['caretime_id'] = caretime_id
    caretime_entry['child_id'] = child_id
    caretime_entry['start_time'] = time_interval.start_time
    if time_interval.stop_time:
        caretime_entry['stop_time'] = time_interval.stop_time
    backend.database.queries_v2.create_caretime(db=db, caretime_entry=caretime_entry)

    return caretime_id


@app.post('/children/{child_id}/caretimes/{caretime_id}')
@starlette.authentication.requires(['admin'])
async def edit_caretime(request: fastapi.Request,
                        child_id: uuid.UUID,
                        caretime_id: uuid.UUID,
                        time_interval: backend.database.schemas.CaretimeBase,
                        db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    child = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
    caretime = backend.database.queries_v2.fetch_single_caretime(db=db, child_id=child_id, caretime_id=caretime_id)
    if not child or not caretime:
        raise fastapi.HTTPException(status_code=404)

    caretime_entry = dict()
    caretime_entry['caretime_id'] = caretime_id
    caretime_entry['child_id'] = child_id
    if time_interval.start_time:
        caretime_entry['start_time'] = time_interval.start_time
    if time_interval.stop_time:
        caretime_entry['stop_time'] = time_interval.stop_time

    backend.database.queries_v2.edit_caretime(db=db, caretime_entry=caretime_entry)


@app.delete('/children/{child_id}/caretimes/{caretime_id}')
@starlette.authentication.requires(['admin'])
async def delete_caretime(request: fastapi.Request,
                          child_id: uuid.UUID,
                          caretime_id: uuid.UUID,
                          db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    backend.database.queries_v2.delete_caretime(db=db, child_id=child_id, caretime_id=caretime_id)
    # TODO: error handling
    return


@app.get('/parents')
@starlette.authentication.requires(['admin'])
async def fetch_parents(request: fastapi.Request,
                        limit: int = 10,
                        db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    return []


@app.get('/is_alive')
def is_alive():
    return {'message': 'Server is alive'}


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8083)
