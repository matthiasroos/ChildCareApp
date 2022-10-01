import base64
import typing
import uuid

import fastapi
import fastapi.requests
import fastapi.responses
import fastapi.security
import sqlalchemy.orm
import starlette.authentication
import starlette.middleware.authentication
import starlette.types
import uvicorn

import backend.app.REST.fastapi.middleware
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


app.add_middleware(backend.app.REST.fastapi.middleware.CloneRequestMiddleware,
                   servers=['http://localhost:8000/rest/flask/v2', ])

app.add_middleware(starlette.middleware.authentication.AuthenticationMiddleware,
                   backend=backend.app.REST.fastapi.middleware.BasicAuthBackend(),
                   on_error=backend.app.REST.fastapi.middleware.on_auth_error)


# This alternative authentication middleware is not in use
# @app.middleware('http')
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
    child = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
    if not child:
        raise fastapi.HTTPException(status_code=404)
    updates_dict = {key: values for key, values in updates_for_child.dict().items() if values is not None}
    _ = backend.database.queries_v2.update_child(db=db, child_id=child_id, updates_for_child=updates_dict)
    return


@app.delete('/children/{child_id}/delete')
@starlette.authentication.requires(['admin'])
async def delete_child(request: fastapi.Request,
                       child_id: uuid.UUID,
                       db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    :return:
    """
    child = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
    if not child:
        raise fastapi.HTTPException(status_code=404)
    backend.database.queries_v2.delete_child(db=db, child_id=child_id)
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
    child = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
    caretime = backend.database.queries_v2.fetch_single_caretime(db=db, child_id=child_id, caretime_id=caretime_id)
    if not child or not caretime:
        raise fastapi.HTTPException(status_code=404)
    backend.database.queries_v2.delete_caretime(db=db, child_id=child_id, caretime_id=caretime_id)
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
