import asyncio
import base64
import datetime
import typing
import uuid

import fastapi
import httpx
import starlette.authentication
import starlette.types

import backend.database.queries_v2


async def snatch_body(receive: starlette.types.Receive):
    """
    Snatch the body of the request.

    :param receive:
    :return:
    """
    messages = []
    more_body = True
    while more_body:
        message = await receive()
        messages.append(message)
        more_body = message.get('more_body', False)

    body = b''.join([message.get('body', b'') for message in messages])

    return body, messages


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
            body, messages = await snatch_body(receive=receive)
            kw_args.update({'data': body})

        for server in self.servers:
            kw_args.update({'url': f'{server}{scope["path"]}'})
            client = httpx.AsyncClient()
            asyncio.ensure_future(client.request(**kw_args))

        # Dispatch to the ASGI callable
        async def wrapped_receive():
            # First up we want to return any messages we've stashed.
            if messages:
                return messages.pop(0)

            # Once that's done we can just await any other messages.
            return await receive()

        await self.app(scope, wrapped_receive, send)


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

        db.close()

        if not authenticated:
            raise starlette.authentication.AuthenticationError('Invalid credentials')
        return starlette.authentication.AuthCredentials([role]), \
            starlette.authentication.SimpleUser(username)


def on_auth_error(conn: fastapi.requests.HTTPConnection, exc: Exception) -> fastapi.Response:
    """function executed on error"""
    return fastapi.responses.JSONResponse(status_code=401, content={'error': 'Not authorized'},
                                          headers={"WWW-Authenticate": "Basic"})


# This alternative authentication middleware is not in use
#  It can be used via:
# @app.middleware('http')(authenticate_user)
#
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

    db.close()

    if not authenticated:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    request.scope['auth'] = starlette.authentication.AuthCredentials([role])
    response = await call_next(request)
    return response


class DBLoggingMiddleware:
    """

    """
    def __init__(self, app: starlette.types.ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: starlette.types.Scope,
                       receive: starlette.types.Receive,
                       send: starlette.types.Send) -> None:
        if scope['type'] == 'http':
            db_config = backend.database.queries_v2.get_database_config()
            db = backend.database.queries_v2.create_session(db_config=db_config)
            body = None
            if scope['method'] in ('POST', 'PUT',):
                body, messages = await snatch_body(receive=receive)
            request_id = uuid.uuid4()
            log_entry = {
                'request_id': request_id,
                'user_name': scope['user'].display_name.decode('utf-8'),
                'endpoint': f'{scope["root_path"]}{scope["path"]}',
                'method': scope['method'],
                'request_timestamp': datetime.datetime.now(),
                'body': body.decode('utf-8') if body else None,
                'query': scope['query_string'].decode('utf-8')
            }
            backend.database.queries_v2.write_logging(db=db,
                                                      log_entry=log_entry,
                                                      insert=True)

            async def wrapped_receive():
                if messages:
                    return messages.pop(0)
                return await receive()

            async def send_wrapper(message: starlette.types.Message) -> None:
                if not scope.get('state', None):
                    scope['state'] = {}
                if message['type'] == 'http.response.start':
                    scope['state']['http.response.start'] = message
                elif message['type'] == 'http.response.body':
                    if scope['state'].get('http.response.body'):
                        scope['state']['http.response.body'].append(message)
                    else:
                        scope['state']['http.response.body'] = [message]
                    if not message.get('more_body', None):
                        log_entry = {
                            'request_id': request_id,
                            'status_code': scope['state']['http.response.start']['status'],
                            'response_timestamp': datetime.datetime.now()}
                        backend.database.queries_v2.write_logging(db=db,
                                                                  log_entry=log_entry,
                                                                  insert=False)
                        db.close()
                await send(message)

            await self.app(scope, wrapped_receive, send_wrapper)
        else:
            await self.app(scope, receive, send)