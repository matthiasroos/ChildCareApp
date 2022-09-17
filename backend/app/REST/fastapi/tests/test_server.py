import asyncio

import fastapi.requests
import starlette.datastructures

import backend.app.REST.fastapi.server


def test_authenticate_all_is_working():
    headers = starlette.datastructures.Headers(
        {'Authorization': 'Basic dGVzdF91c2VyOkRnaWRYcXB0OVJJNGM3WDN0MkYz'})
    scope = {
        'method': 'GET',
        'type': 'http',
        'headers': None}
    conn = fastapi.requests.HTTPConnection(scope=scope)
    conn._headers = headers

    basicauthbackend = backend.app.REST.fastapi.server.BasicAuthBackend()

    credentials, user = asyncio.run(basicauthbackend.authenticate(conn=conn))

    assert credentials
    assert user
