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
import starlette.authentication
import starlette.middleware.authentication
import starlette.requests
import starlette.types
import uvicorn

import backend.database.queries
import backend.database.queries_v2
import backend.database.schemas
import backend.database.usermanagement


def get_db(request: fastapi.Request):
    """

    :return:
    """
    db_config = backend.database.queries_v2.get_database_config()
    db = backend.database.queries_v2.create_session(db_config=db_config)
    try:
        request.state.db = db
        yield db
    finally:
        db.close()


app = fastapi.FastAPI(root_path='/rest/fastapi/v1', dependencies=[fastapi.Depends(get_db)])


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

        messages = []
        more_body = True
        while more_body:
            message = await receive()
            messages.append(message)
            more_body = message.get('more_body', False)

        body = b''.join([message.get('body', b'') for message in messages])

        request = fastapi.requests.Request(scope)
        for server in self.servers:
            if request.method == 'GET':
                thread = threading.Thread(target=getattr(requests, request.method.lower()),
                                          kwargs={'url': f'{server}{scope["path"]}',
                                                  'headers': dict(scope['headers'])})
                thread.start()
            elif request.method == 'POST':
                thread = threading.Thread(target=getattr(requests, request.method.lower()),
                                          kwargs={'url': f'{server}{scope["path"]}',
                                                  'headers': dict(scope['headers']),
                                                  'data': body})
                thread.start()

        # Dispatch to the ASGI callable
        async def wrapped_receive():
            # First up we want to return any messages we've stashed.
            if messages:
                return messages.pop(0)

            # Once that's done we can just await any other messages.
            return await receive()

        await self.app(scope, wrapped_receive, send)


app.add_middleware(CloneRequestMiddleware, servers=['http://localhost:8000/rest/flask/v2', ])


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

        auth_header = conn.headers['Authorization']
        username, password = base64.b64decode(auth_header.split()[1]).split(b':')
        authenticated, role = backend.database.usermanagement.authenticate_user(user_name=username.decode('utf-8'),
                                                                                password=password.decode('utf-8'))
        if not authenticated:
            raise starlette.authentication.AuthenticationError('Invalid credentials')
        return starlette.authentication.AuthCredentials([role]), \
            starlette.authentication.SimpleUser(username)


def on_auth_error(conn: fastapi.requests.HTTPConnection, exc: Exception) -> fastapi.Response:
    """function executed on error"""
    return fastapi.responses.JSONResponse(status_code=401,
                                          content={'error': str(exc)},
                                          headers={"WWW-Authenticate": "Basic"})


app.add_middleware(starlette.middleware.authentication.AuthenticationMiddleware,
                   backend=BasicAuthBackend(),
                   on_error=on_auth_error)


#@app.middleware('http')
async def authenticate_user(request: fastapi.Request, call_next: typing.Callable):
    """

    :return:
    """
    username, password = base64.b64decode(request.headers.get('authorization').split()[1]).split(b':')
    authenticated, role = backend.database.usermanagement.authenticate_user(user_name=username.decode('utf-8'),
                                                                            password=password.decode('utf-8'))
    if not authenticated or role != 'admin':
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    response = await call_next(request)
    return response


error_404_response = fastapi.responses.JSONResponse(status_code=404, content={'error': 'Item not found'})


@app.get('/children', response_model=typing.List[backend.database.schemas.Child])
@starlette.authentication.requires(['admin'])
async def fetch_children(request: fastapi.Request, recent: bool = False, limit: int = 10):
    """

    :return:
    """
    result = backend.database.queries_v2.fetch_children(db=request.state.db, recent=recent, limit=limit)
    return result


@app.get('/children/{child_id}', response_model=backend.database.schemas.Child)
@starlette.authentication.requires(['admin'])
async def fetch_child(request: fastapi.Request, child_id: uuid.UUID = fastapi.Path(..., title='ID of the child to get')):
    """

    :return:
    """
    result = backend.database.queries_v2.fetch_child(db=request.state.db, child_id=child_id)
    if result:
        return result
    return error_404_response


@app.post('/children', response_model=backend.database.schemas.Child)
@starlette.authentication.requires(['admin'])
async def fetch_one_child(request: fastapi.Request, body: dict):
    """

    :return:
    """
    result = backend.database.queries_v2.fetch_child(db=request.state.db, child_id=body['child_id'])
    if result:
        return result
    return error_404_response


@app.post('/children/create', status_code=fastapi.status.HTTP_201_CREATED)
@starlette.authentication.requires(['admin'])
async def create_child(request: fastapi.Request, child: backend.database.schemas.ChildBase):
    """

    :return:
    """
    child_id = uuid.uuid4()
    child_dict = child.dict()
    child_dict['child_id'] = child_id
    _ = backend.database.queries_v2.create_child(db=request.state.db, child=child_dict)
    return child_id


@app.put('/children/{child_id}/update')
@starlette.authentication.requires(['admin'])
async def update_child(request: fastapi.Request, child_id: uuid.UUID, updates_for_child: backend.database.schemas.ChildUpdate):
    """

    :return:
    """
    updates_dict = {key: values for key, values in updates_for_child.dict().items() if values is not None}
    _ = backend.database.queries_v2.update_child(db=request.state.db, child_id=child_id, updates_for_child=updates_dict)
    return


@app.delete('/children/{child_id}/delete')
@starlette.authentication.requires(['admin'])
async def delete_child(request: fastapi.Request, child_id: uuid.UUID):
    """

    :return:
    """
    backend.database.queries_v2.delete_child(db=request.state.db, child_id=child_id)
    return


@app.post('/children/{child_id}/caretimes')
@starlette.authentication.requires(['admin'])
async def add_caretime(request: fastapi.Request,
                       child_id: uuid.UUID,
                       ):
    """

    :return:
    """
    return None


@app.get('/parents')
@starlette.authentication.requires(['admin'])
async def fetch_parents(request: fastapi.Request, limit: int = 10):
    """

    :return:
    """
    return []


@app.get('/is_alive')
def is_alive():
    return {'message': 'Server is alive'}


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8083)
