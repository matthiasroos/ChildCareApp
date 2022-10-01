import base64
import threading
import typing

import fastapi
import requests
import starlette.authentication
import starlette.types

import backend.database.queries_v2


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
