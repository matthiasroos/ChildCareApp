import base64
import datetime
import uuid

import starlite.middleware.base
import starlite.types
import starlite

import backend.database.queries_v2
import backend.database.usermanagement


class BasicAuthMiddleware(starlite.AbstractAuthenticationMiddleware):
    """

    """
    async def authenticate_request(self, connection: starlite.ASGIConnection) -> starlite.AuthenticationResult:
        """

        :param connection:
        :return:
        """
        if 'Authorization' not in connection.headers:
            raise starlite.NotAuthorizedException()
        db_config = backend.database.queries_v2.get_database_config()
        db = backend.database.queries_v2.create_session(db_config=db_config)
        username, password = base64.b64decode(connection.headers.get('authorization').split()[1]).split(b':')
        authenticated, role = backend.database.usermanagement.authenticate_user(db=db,
                                                                                user_name=username.decode('utf-8'),
                                                                                password=password.decode('utf-8'))

        db.close()

        if not authenticated:
            raise starlite.NotAuthorizedException()
        return starlite.AuthenticationResult(user=username, auth=role)


class DBLoggingMiddleware(starlite.middleware.base.MiddlewareProtocol):
    """

    """
    def __init__(self, app: starlite.types.ASGIApp) -> None:
        super().__init__(app=app)
        self.app = app

    async def __call__(self, scope: starlite.types.Scope, receive: starlite.types.Receive, send: starlite.types.Send) \
         -> None:
        if scope['type'] == 'http':
            db_config = backend.database.queries_v2.get_database_config()
            db = backend.database.queries_v2.create_session(db_config=db_config)
            body = None
            if scope['method'] in ('POST', 'PUT',):
                messages = []
                more_body = True
                while more_body:
                    message_ = await receive()
                    messages.append(message_)
                    more_body = message_.get('more_body', False)

                body = b''.join([message.get('body', b'') for message in messages])
            request_id = uuid.uuid4()
            log_entry = {
                'request_id': request_id,
                'user_name': scope['user'].decode('utf-8'),
                'endpoint': scope['path'],
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

            async def send_wrapper(message: starlite.types.Message) -> None:
                if message['type'] == 'http.response.start':
                    scope['state']['http.response.start'] = message
                elif message['type'] == 'http.response.body':
                    if scope['state'].get('http.response.body'):
                        scope['state']['http.response.body'].append(message)
                    else:
                        scope['state']['http.response.body'] = [message]
                    if not message['more_body']:
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
